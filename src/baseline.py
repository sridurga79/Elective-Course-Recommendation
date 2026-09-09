import pandas as pd
from src.prerequisite_engine import parse_student_completed

# Frequently selected buzzword / popular electives that students pick unguided
POPULAR_ELECTIVES = ["CS304", "CS410", "CS401", "CS406", "CS302", "CS419", "CS411", "CS409"]

def get_baseline_recommendations(student_profile, courses_df, mapping_df, career_paths_df, top_n=3):
    """
    Naive baseline recommender:
    Simulates unguided student decision making where electives are selected based on
    either generic buzzword popularity OR unvalidated course preference.
    Crucially, it does NOT verify prerequisite eligibility chains or timetable conflicts.
    """
    completed_courses, _ = parse_student_completed(student_profile)
    sid = str(student_profile.get("student_id", "S101"))
    
    selected = []
    offset = sum(ord(c) for c in sid) % len(POPULAR_ELECTIVES)
    pool = POPULAR_ELECTIVES[offset:] + POPULAR_ELECTIVES[:offset]
    
    for cid in pool:
        if cid not in completed_courses and not any(r["course_id"] == cid for r in selected):
            c_info = courses_df[courses_df["course_id"] == cid]
            if not c_info.empty:
                c_data = c_info.iloc[0]
                selected.append({
                    "course_id": cid,
                    "course_name": c_data["course_name"],
                    "relevance_score": 50,
                    "credits": c_data["credits"],
                    "semester": c_data["semester"]
                })
        if len(selected) >= top_n:
            break
            
    return selected
