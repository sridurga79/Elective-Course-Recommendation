def parse_time_to_minutes(time_str):
    """Converts HH:MM string to integer minutes from midnight."""
    parts = time_str.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])

def check_time_overlap(start1, end1, start2, end2):
    """Returns True if [start1, end1) overlaps with [start2, end2)."""
    m_s1, m_e1 = parse_time_to_minutes(start1), parse_time_to_minutes(end1)
    m_s2, m_e2 = parse_time_to_minutes(start2), parse_time_to_minutes(end2)
    return max(m_s1, m_s2) < min(m_e1, m_e2)

def check_schedule_conflicts(selected_course_ids, schedules_df, student_semester=None, available_credits=None, courses_df=None):
    """
    Analyzes timetable conflicts, semester alignment, and credit limits for a list of course IDs.
    """
    conflicts = []
    semester_mismatches = []
    selected_set = [c.upper() for c in selected_course_ids]
    
    # Filter schedule slots for selected courses
    sched_subset = schedules_df[schedules_df["course_id"].isin(selected_set)].copy()
    
    # Pairwise overlap detection
    slots = sched_subset.to_dict("records")
    for i in range(len(slots)):
        for j in range(i + 1, len(slots)):
            s1 = slots[i]
            s2 = slots[j]
            if s1["course_id"] != s2["course_id"] and s1["day"] == s2["day"]:
                if check_time_overlap(s1["start_time"], s1["end_time"], s2["start_time"], s2["end_time"]):
                    conflicts.append({
                        "course_a": s1["course_id"],
                        "course_b": s2["course_id"],
                        "day": s1["day"],
                        "time_a": f"{s1['start_time']}–{s1['end_time']}",
                        "time_b": f"{s2['start_time']}–{s2['end_time']}",
                        "room_a": s1.get("room", ""),
                        "room_b": s2.get("room", ""),
                        "message": f"Schedule Conflict: {s1['course_id']} ({s1['start_time']}–{s1['end_time']}) overlaps with {s2['course_id']} ({s2['start_time']}–{s2['end_time']}) on {s1['day']}."
                    })

    # Semester alignment check
    if student_semester is not None and courses_df is not None:
        for cid in selected_set:
            c_row = courses_df[courses_df["course_id"] == cid]
            if not c_row.empty:
                c_sem = int(c_row.iloc[0]["semester"])
                if c_sem != student_semester:
                    semester_mismatches.append({
                        "course_id": cid,
                        "course_semester": c_sem,
                        "student_semester": student_semester,
                        "message": f"Semester Mismatch: {cid} is offered in Semester {c_sem}, but current student semester is {student_semester}."
                    })

    # Credit overload check
    credit_info = {"total_credits": 0, "available_credits": available_credits, "is_overload": False, "overload_credits": 0}
    if courses_df is not None and available_credits is not None:
        tot_credits = 0
        for cid in selected_set:
            c_row = courses_df[courses_df["course_id"] == cid]
            if not c_row.empty:
                tot_credits += int(c_row.iloc[0]["credits"])
        credit_info["total_credits"] = tot_credits
        if tot_credits > available_credits:
            credit_info["is_overload"] = True
            credit_info["overload_credits"] = tot_credits - available_credits

    has_conflict = (len(conflicts) > 0) or (len(semester_mismatches) > 0) or credit_info["is_overload"]
    
    return {
        "has_conflict": has_conflict,
        "pairwise_conflicts": conflicts,
        "semester_mismatches": semester_mismatches,
        "credit_info": credit_info,
        "conflict_count": len(conflicts)
    }

def calculate_schedule_compatibility(candidate_course_id, selected_courses, schedules_df, preferred_days=None):
    """
    Computes a schedule compatibility score (0.0 to 1.0) for a candidate course given current selections and day preferences.
    """
    candidate_course_id = candidate_course_id.upper()
    c_sched = schedules_df[schedules_df["course_id"] == candidate_course_id]
    if c_sched.empty:
        return 0.7 # neutral if no schedule record
        
    c_row = c_sched.iloc[0]
    c_day = c_row["day"]
    c_start = c_row["start_time"]
    c_end = c_row["end_time"]
    
    # Check overlap with any selected courses
    for sc in selected_courses:
        sc_sched = schedules_df[schedules_df["course_id"] == sc.upper()]
        if not sc_sched.empty:
            sc_row = sc_sched.iloc[0]
            if sc_row["day"] == c_day:
                if check_time_overlap(c_start, c_end, sc_row["start_time"], sc_row["end_time"]):
                    return 0.0 # hard overlap
                    
    score = 0.8
    if preferred_days:
        pref_list = [d.strip() for d in preferred_days.split(";") if d.strip()]
        if c_day in pref_list:
            score = 1.0
        else:
            score = 0.6
            
    return score
