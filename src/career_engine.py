import pandas as pd

def get_career_by_name_or_id(career_query, career_paths_df):
    """Finds career path row by ID or Name."""
    if not career_query or pd.isna(career_query) or career_query.strip().lower() in ["undeclared", "none", "unknown"]:
        return None
    career_query = career_query.strip()
    match = career_paths_df[(career_paths_df["career_id"].str.upper() == career_query.upper()) | 
                            (career_paths_df["career_name"].str.lower() == career_query.lower())]
    if not match.empty:
        return match.iloc[0]
    return None

def evaluate_career_consequence(course_id, career_goal, career_paths_df, mapping_df, courses_df):
    """
    Evaluates relevance, skill overlap, and outcome match for a course given a student's career goal.
    """
    course_id = course_id.upper()
    c_row = courses_df[courses_df["course_id"] == course_id]
    if c_row.empty:
        return {
            "career_score": 0.0,
            "outcome_score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "status": "Not Recommended",
            "explanation": "Course not found in catalog."
        }
    
    course = c_row.iloc[0]
    career = get_career_by_name_or_id(career_goal, career_paths_df)
    
    # Fallback if no specific career goal declared
    if career is None:
        return {
            "career_score": 0.50,
            "outcome_score": 0.50,
            "matched_skills": ["Foundational Computing", "Problem Solving"],
            "missing_skills": [],
            "status": "General Elective",
            "explanation": "No specific career declared. Course provides general computing fundamentals."
        }

    career_id = career["career_id"]
    career_name = career["career_name"]
    req_skills = [s.strip() for s in career["required_skills"].split(";") if s.strip()]
    
    # Check direct mapping table
    mapping = mapping_df[(mapping_df["career_id"] == career_id) & (mapping_df["course_id"] == course_id)]
    
    relevance_score = 0.0
    skills_covered = []
    rationale = ""
    
    if not mapping.empty:
        m_row = mapping.iloc[0]
        relevance_score = float(m_row["relevance_score"]) / 100.0
        skills_covered = [s.strip() for s in str(m_row["skills_covered"]).split(";") if s.strip()]
        rationale = str(m_row["rationale"])
    else:
        # Keyword heuristic across outcomes & description
        outcomes_text = (str(course["learning_outcomes"]) + " " + str(course["description"])).lower()
        matched = [skill for skill in req_skills if skill.lower() in outcomes_text]
        if matched:
            relevance_score = min(0.85, 0.4 + 0.15 * len(matched))
            skills_covered = matched
            rationale = f"Aligns with {len(matched)} target skills ({', '.join(matched)})."
        else:
            relevance_score = 0.20
            skills_covered = []
            rationale = f"Limited direct relevance to {career_name} career competencies."

    # Skill match breakdown
    matched_skills = [s for s in skills_covered if any(s.lower() in req.lower() or req.lower() in s.lower() for req in req_skills)]
    missing_skills = [s for s in req_skills if not any(s.lower() in ms.lower() for ms in matched_skills)]

    # Learning outcome score
    outcomes_str = str(course["learning_outcomes"]).lower()
    outcome_hits = sum(1 for req in req_skills if req.lower() in outcomes_str)
    outcome_score = min(1.0, 0.30 + outcome_hits * 0.25) if outcome_hits > 0 else 0.30

    if relevance_score >= 0.85:
        rec_status = "HIGHLY RECOMMENDED"
    elif relevance_score >= 0.70:
        rec_status = "RECOMMENDED"
    else:
        rec_status = "OPTIONAL"

    explanation = f"Recommended for {career_name}: {rationale}" if relevance_score >= 0.70 else f"Low relevance for {career_name}."

    return {
        "career_score": round(relevance_score, 2),
        "outcome_score": round(outcome_score, 2),
        "matched_skills": matched_skills if matched_skills else skills_covered,
        "missing_skills": missing_skills[:4],
        "status": rec_status,
        "explanation": explanation
    }
