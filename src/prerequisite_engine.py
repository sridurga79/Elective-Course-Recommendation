GRADE_SCALE = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0}

def parse_student_completed(student_profile):
    """
    Parses completed courses and grade mappings from student profile.
    """
    completed_courses = set()
    grades_map = {}

    if "completed_courses" in student_profile and isinstance(student_profile["completed_courses"], str):
        courses_str = student_profile["completed_courses"].strip()
        if courses_str:
            completed_courses = {c.strip().upper() for c in courses_str.split(";") if c.strip()}

    if "grades" in student_profile and isinstance(student_profile["grades"], str):
        grades_str = student_profile["grades"].strip()
        if grades_str:
            for item in grades_str.split(";"):
                if ":" in item:
                    cid, gr = item.split(":", 1)
                    grades_map[cid.strip().upper()] = gr.strip().upper()

    return completed_courses, grades_map

def get_prerequisite_chain(course_id, prerequisites_df, visited=None):
    """
    Recursively discovers all ancestor prerequisites for a course.
    """
    if visited is None:
        visited = set()
    
    course_id = course_id.upper()
    chain = []
    direct_reqs = prerequisites_df[prerequisites_df["course_id"] == course_id]
    
    for _, row in direct_reqs.iterrows():
        p_id = row["prerequisite_course_id"]
        min_g = row.get("minimum_grade", "C")
        if p_id not in visited:
            visited.add(p_id)
            sub_chain = get_prerequisite_chain(p_id, prerequisites_df, visited)
            chain.append({
                "prerequisite_course_id": p_id,
                "minimum_grade": min_g,
                "sub_prerequisites": sub_chain
            })
            
    return chain

def check_prerequisite_eligibility(student_profile, course_id, prerequisites_df, courses_df=None):
    """
    Evaluates whether a student is eligible for course_id.
    Returns status, is_eligible boolean, missing prerequisites, grade failures, and explanation.
    """
    course_id = course_id.upper()
    completed_courses, grades_map = parse_student_completed(student_profile)
    
    # Check if course exists in courses_df
    if courses_df is not None and course_id not in courses_df["course_id"].values:
        return {
            "course_id": course_id,
            "is_eligible": False,
            "status": "Invalid Course",
            "missing_prerequisites": [],
            "grade_failures": [],
            "prerequisite_chain": [],
            "explanation": f"Course '{course_id}' does not exist in the university catalog."
        }

    direct_prereqs = prerequisites_df[prerequisites_df["course_id"] == course_id]
    
    if direct_prereqs.empty:
        return {
            "course_id": course_id,
            "is_eligible": True,
            "status": "Eligible",
            "missing_prerequisites": [],
            "grade_failures": [],
            "prerequisite_chain": [],
            "explanation": f"Course {course_id} has no prerequisite requirements."
        }

    missing = []
    grade_failures = []
    chain = get_prerequisite_chain(course_id, prerequisites_df)

    for _, row in direct_prereqs.iterrows():
        p_id = row["prerequisite_course_id"]
        min_grade = row.get("minimum_grade", "C").upper()
        
        if p_id not in completed_courses:
            missing.append(p_id)
        else:
            student_grade = grades_map.get(p_id, "C") # default pass if grade not listed
            student_val = GRADE_SCALE.get(student_grade, 0)
            min_val = GRADE_SCALE.get(min_grade, 2)
            if student_val < min_val:
                grade_failures.append({
                    "course_id": p_id,
                    "student_grade": student_grade,
                    "required_grade": min_grade
                })

    if missing:
        missing_str = ", ".join(missing)
        return {
            "course_id": course_id,
            "is_eligible": False,
            "status": "Missing Prerequisite",
            "missing_prerequisites": missing,
            "grade_failures": grade_failures,
            "prerequisite_chain": chain,
            "explanation": f"NOT ELIGIBLE: Course {course_id} requires {missing_str}, which has not been completed."
        }

    if grade_failures:
        gf = grade_failures[0]
        return {
            "course_id": course_id,
            "is_eligible": False,
            "status": "Prerequisite Grade Not Satisfied",
            "missing_prerequisites": [],
            "grade_failures": grade_failures,
            "prerequisite_chain": chain,
            "explanation": f"NOT ELIGIBLE: {course_id} requires grade '{gf['required_grade']}' in {gf['course_id']}, but student achieved '{gf['student_grade']}'."
        }

    # All direct prerequisites met!
    prereq_list = ", ".join([f"{r['prerequisite_course_id']} (Grade {grades_map.get(r['prerequisite_course_id'], 'Pass')})" for _, r in direct_prereqs.iterrows()])
    return {
        "course_id": course_id,
        "is_eligible": True,
        "status": "Eligible",
        "missing_prerequisites": [],
        "grade_failures": [],
        "prerequisite_chain": chain,
        "explanation": f"ELIGIBLE: All prerequisites satisfied ({prereq_list})."
    }


def get_unlocked_courses(selected_courses, prerequisites_df, courses_df):
    """
    Identifies advanced future courses that will be unlocked by successfully
    completing the given selected courses.
    """
    selected_set = {str(c).strip().upper() for c in selected_courses}
    unlocked = []
    seen = set()
    
    for _, row in prerequisites_df.iterrows():
        p_id = row["prerequisite_course_id"]
        c_id = row["course_id"]
        if p_id in selected_set and c_id not in selected_set and c_id not in seen:
            seen.add(c_id)
            c_info = courses_df[courses_df["course_id"] == c_id]
            if not c_info.empty:
                c_data = c_info.iloc[0]
                unlocked.append({
                    "unlocked_course_id": c_id,
                    "course_name": c_data["course_name"],
                    "prerequisite_satisfied": p_id,
                    "semester": c_data["semester"],
                    "elective_group": c_data["elective_group"]
                })
    return unlocked


def build_prerequisite_dag(target_cid, prerequisites_df, completed_set):
    """
    Constructs a visual directed acyclic graph (DAG) representation for the prerequisite tree of target_cid.
    Returns nodes, edges, and 2D coordinates for Plotly rendering.
    """
    target_cid = str(target_cid).strip().upper()
    nodes = {target_cid: {"level": 0, "status": "Target"}}
    edges = []
    
    def walk(cid, current_level):
        direct = prerequisites_df[prerequisites_df["course_id"] == cid]
        for _, r in direct.iterrows():
            p_id = r["prerequisite_course_id"]
            edges.append((p_id, cid))
            p_status = "Completed" if p_id in completed_set else "Missing"
            p_level = current_level + 1
            if p_id not in nodes or nodes[p_id]["level"] < p_level:
                nodes[p_id] = {"level": p_level, "status": p_status}
            walk(p_id, p_level)
            
    walk(target_cid, 0)
    
    max_lvl = max((n["level"] for n in nodes.values()), default=0)
    level_counts = {}
    for cid, info in nodes.items():
        x = max_lvl - info["level"]
        level_counts[x] = level_counts.get(x, []) + [cid]
        
    coords = {}
    for x, cids in level_counts.items():
        total_in_col = len(cids)
        for idx, cid in enumerate(cids):
            y = idx - (total_in_col - 1) / 2.0
            coords[cid] = (x, y)
            
    return nodes, edges, coords
