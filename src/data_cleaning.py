import pandas as pd
import numpy as np

REQUIRED_COLUMNS = {
    "courses": ["course_id", "course_name", "department", "credits", "course_type", "description", "learning_outcomes", "difficulty", "semester", "elective_group"],
    "prerequisites": ["course_id", "prerequisite_course_id", "minimum_grade"],
    "schedules": ["course_id", "day", "start_time", "end_time", "semester", "room"],
    "career_paths": ["career_id", "career_name", "required_skills", "recommended_courses", "importance_score"],
    "career_course_mapping": ["career_id", "course_id", "relevance_score", "skills_covered", "rationale"],
    "students": ["student_id", "name", "completed_courses", "grades", "current_semester", "career_goal", "available_credits", "preferred_days"]
}

def clean_and_validate_data(raw_data):
    """
    Cleans datasets, checks schemas, normalizes IDs, checks relational integrity,
    and returns (cleaned_data, quality_report).
    """
    cleaned = {}
    total_records = 0
    missing_values = 0
    duplicate_records = 0
    invalid_records = 0
    issues = []

    # 1. Schema check & normalization
    for key, req_cols in REQUIRED_COLUMNS.items():
        df = raw_data[key].copy()
        total_records += len(df)
        
        # Missing columns check
        missing_cols = [c for c in req_cols if c not in df.columns]
        if missing_cols:
            issues.append(f"Table '{key}' is missing required columns: {missing_cols}")
            invalid_records += len(df)
            continue
            
        # Count and log missing values
        null_count = df.isnull().sum().sum()
        missing_values += int(null_count)
        
        # Deduplication
        initial_len = len(df)
        df = df.drop_duplicates()
        dups = initial_len - len(df)
        duplicate_records += dups
        if dups > 0:
            issues.append(f"Table '{key}' contained {dups} duplicate records (removed).")
            
        # String normalization
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
                
        cleaned[key] = df

    # Normalize Course IDs uppercase
    if "courses" in cleaned:
        cleaned["courses"]["course_id"] = cleaned["courses"]["course_id"].str.upper()
        # Handle missing descriptions or outcomes with sensible defaults
        cleaned["courses"]["description"] = cleaned["courses"]["description"].fillna("No description available.")
        cleaned["courses"]["learning_outcomes"] = cleaned["courses"]["learning_outcomes"].fillna("Foundational concepts.")

    if "prerequisites" in cleaned:
        cleaned["prerequisites"]["course_id"] = cleaned["prerequisites"]["course_id"].str.upper()
        cleaned["prerequisites"]["prerequisite_course_id"] = cleaned["prerequisites"]["prerequisite_course_id"].str.upper()
        cleaned["prerequisites"]["minimum_grade"] = cleaned["prerequisites"]["minimum_grade"].str.upper()

    if "schedules" in cleaned:
        cleaned["schedules"]["course_id"] = cleaned["schedules"]["course_id"].str.upper()

    if "career_course_mapping" in cleaned:
        cleaned["career_course_mapping"]["course_id"] = cleaned["career_course_mapping"]["course_id"].str.upper()
        cleaned["career_course_mapping"]["career_id"] = cleaned["career_course_mapping"]["career_id"].str.upper()

    # Relational integrity validation
    valid_course_ids = set(cleaned["courses"]["course_id"].unique()) if "courses" in cleaned else set()

    # Check prerequisites foreign keys
    if "prerequisites" in cleaned:
        p_df = cleaned["prerequisites"]
        invalid_mask = (~p_df["course_id"].isin(valid_course_ids)) | (~p_df["prerequisite_course_id"].isin(valid_course_ids))
        invalid_p = p_df[invalid_mask]
        if len(invalid_p) > 0:
            invalid_records += len(invalid_p)
            for _, row in invalid_p.iterrows():
                issues.append(f"Invalid prerequisite relation: {row['course_id']} -> {row['prerequisite_course_id']} (course not found in catalog).")
            cleaned["prerequisites"] = p_df[~invalid_mask]

    # Check schedules foreign keys
    if "schedules" in cleaned:
        s_df = cleaned["schedules"]
        invalid_sched_mask = ~s_df["course_id"].isin(valid_course_ids)
        invalid_s = s_df[invalid_sched_mask]
        if len(invalid_s) > 0:
            invalid_records += len(invalid_s)
            for _, row in invalid_s.iterrows():
                issues.append(f"Invalid schedule slot: Course {row['course_id']} not found in catalog.")
            cleaned["schedules"] = s_df[~invalid_sched_mask]

    valid_records = total_records - invalid_records - duplicate_records

    quality_report = {
        "total_records": int(total_records),
        "valid_records": int(valid_records),
        "invalid_records": int(invalid_records),
        "missing_values": int(missing_values),
        "duplicate_records": int(duplicate_records),
        "issues": issues
    }

    return cleaned, quality_report
