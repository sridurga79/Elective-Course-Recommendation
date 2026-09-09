from src.prerequisite_engine import check_prerequisite_eligibility, parse_student_completed
from src.schedule_engine import calculate_schedule_compatibility
from src.career_engine import evaluate_career_consequence

def compute_recommendation_score(prereq_score, career_score, outcome_score, schedule_score, pref_score):
    """
    Transparent rule-based scoring formula:
    Recommendation Score = 0.30 * prereq_score + 0.30 * career_score + 0.20 * outcome_score + 0.10 * schedule_score + 0.10 * pref_score
    Scores normalized between 0 and 100.
    """
    final_score = (
        0.30 * prereq_score +
        0.30 * career_score +
        0.20 * outcome_score +
        0.10 * schedule_score +
        0.10 * pref_score
    )
    return round(final_score * 100, 1)

def get_recommended_electives(student_profile, courses_df, prerequisites_df, schedules_df, career_paths_df, mapping_df, top_n=5, filter_semester=True):
    """
    Generates ranked elective recommendations for a student profile.
    Filters out already completed courses, restricts candidates to electives,
    and strictly disqualifies courses with unmet prerequisites.
    """
    completed_courses, _ = parse_student_completed(student_profile)
    student_sem = int(student_profile.get("current_semester", 5)) if student_profile.get("current_semester") else 5
    career_goal = student_profile.get("career_goal", "Software Developer")
    preferred_days = student_profile.get("preferred_days", "")
    
    candidate_courses = []
    
    for _, course in courses_df.iterrows():
        cid = course["course_id"]
        
        # 1. Skip already completed courses
        if cid in completed_courses:
            continue
            
        # 2. Only consider actual Elective courses
        if course["course_type"] not in ["Elective", "Core Elective"]:
            continue
            
        # 3. Semester matching
        c_sem = int(course["semester"])
        if filter_semester and c_sem != student_sem:
            continue

        # 4. Prerequisite Engine evaluation
        prereq_eval = check_prerequisite_eligibility(student_profile, cid, prerequisites_df, courses_df)
        is_eligible = prereq_eval["is_eligible"]
        prereq_score = 1.0 if is_eligible else 0.0
        
        # 5. Career Engine evaluation
        career_eval = evaluate_career_consequence(cid, career_goal, career_paths_df, mapping_df, courses_df)
        career_score = career_eval["career_score"]
        outcome_score = career_eval["outcome_score"]
        
        # 6. Schedule Engine compatibility
        sched_score = calculate_schedule_compatibility(cid, [], schedules_df, preferred_days)
        
        # 7. Student Preference (preferred day matching)
        pref_score = 0.80
        if preferred_days:
            c_sched = schedules_df[schedules_df["course_id"] == cid]
            if not c_sched.empty:
                d = c_sched.iloc[0]["day"]
                if d in preferred_days:
                    pref_score = 1.0
                else:
                    pref_score = 0.60
                    
        # Compute final weighted score
        final_score = compute_recommendation_score(prereq_score, career_score, outcome_score, sched_score, pref_score)
        
        # Strict Rule: If prerequisites not met, mark as not valid choice
        is_recommended = is_eligible and (final_score >= 50.0)
        
        # Explanation generation
        sched_row = schedules_df[schedules_df["course_id"] == cid]
        sched_display = f"{sched_row.iloc[0]['day']} {sched_row.iloc[0]['start_time']}–{sched_row.iloc[0]['end_time']}" if not sched_row.empty else "TBA"

        if is_eligible:
            matched_str = ", ".join(career_eval["matched_skills"][:3]) if career_eval["matched_skills"] else "Technical foundation"
            reason = (
                f"Recommended because: (1) You are interested in {career_goal}; "
                f"(2) Develops essential competencies: {matched_str}; "
                f"(3) All prerequisite requirements are met; "
                f"(4) Fits timetable on {sched_display}."
            )
        else:
            reason = f"Not recommended: {prereq_eval['explanation']}"

        candidate_courses.append({
            "course_id": cid,
            "course_name": course["course_name"],
            "department": course["department"],
            "credits": course["credits"],
            "semester": course["semester"],
            "elective_group": course["elective_group"],
            "recommendation_score": final_score,
            "is_eligible": is_eligible,
            "is_recommended": is_recommended,
            "prerequisite_status": prereq_eval["status"],
            "prerequisites_needed": prereq_eval["missing_prerequisites"],
            "grade_failures": prereq_eval["grade_failures"],
            "career_relevance": round(career_score * 100, 1),
            "skills_gained": career_eval["matched_skills"],
            "learning_outcomes": course["learning_outcomes"],
            "schedule": sched_display,
            "reason": reason,
            "score_breakdown": {
                "prerequisite_score": round(prereq_score * 30, 1),
                "career_score": round(career_score * 30, 1),
                "outcome_score": round(outcome_score * 20, 1),
                "schedule_score": round(sched_score * 10, 1),
                "preference_score": round(pref_score * 10, 1)
            }
        })
        
    # Sort candidates: Eligible courses first, then by score descending
    candidate_courses.sort(key=lambda x: (x["is_eligible"], x["recommendation_score"]), reverse=True)
    
    return candidate_courses[:top_n], candidate_courses
