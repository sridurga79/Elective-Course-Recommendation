import pytest
import os
import pandas as pd
from src.data_loader import load_raw_data
from src.data_cleaning import clean_and_validate_data
from src.prerequisite_engine import check_prerequisite_eligibility
from src.schedule_engine import check_schedule_conflicts
from src.career_engine import evaluate_career_consequence
from src.recommendation_engine import get_recommended_electives

@pytest.fixture
def dataset():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    raw = load_raw_data(data_dir)
    cleaned, _ = clean_and_validate_data(raw)
    return cleaned

def test_case_1_missing_prerequisite_blocked(dataset):
    """CASE 1: Student selects course without completing its prerequisite."""
    student = {"student_id": "S_TEST", "completed_courses": "", "grades": "", "current_semester": 5}
    res = check_prerequisite_eligibility(student, "CS301", dataset["prerequisites"], dataset["courses"])
    assert res["is_eligible"] is False
    assert res["status"] == "Missing Prerequisite"
    assert "CS201" in res["missing_prerequisites"]

def test_case_2_overlapping_schedules(dataset):
    """CASE 2: Two selected courses have overlapping schedules."""
    selected = ["CS411", "CS414"] # Intentional exact collision on Thursday 11:00-12:30
    res = check_schedule_conflicts(selected, dataset["schedules"], courses_df=dataset["courses"])
    assert res["has_conflict"] is True
    assert len(res["pairwise_conflicts"]) == 1

def test_case_3_semester_mismatch(dataset):
    """CASE 3: Student selects a course unavailable in their semester."""
    student_sem = 3
    selected = ["CS401"] # Offered in Sem 7
    res = check_schedule_conflicts(selected, dataset["schedules"], student_semester=student_sem, courses_df=dataset["courses"])
    assert len(res["semester_mismatches"]) == 1
    assert "Semester Mismatch" in res["semester_mismatches"][0]["message"]

def test_case_4_invalid_prerequisite_handling(dataset):
    """CASE 4: Course has invalid or non-existing prerequisite in database."""
    dirty_data = {k: v.copy() for k, v in dataset.items()}
    # Add an orphan prerequisite to a non-existent course
    dirty_prereqs = pd.concat([
        dirty_data["prerequisites"],
        pd.DataFrame([{"course_id": "CS101", "prerequisite_course_id": "GHOST999", "minimum_grade": "C"}])
    ], ignore_index=True)
    dirty_data["prerequisites"] = dirty_prereqs
    
    cleaned, report = clean_and_validate_data(dirty_data)
    assert report["invalid_records"] >= 1
    assert any("GHOST999" in issue for issue in report["issues"])
    # Orphan row should be filtered out safely
    assert not (cleaned["prerequisites"]["prerequisite_course_id"] == "GHOST999").any()

def test_case_5_undeclared_career_goal(dataset):
    """CASE 5: Student has no matching career goal/pathway."""
    res = evaluate_career_consequence("CS101", "Undeclared", dataset["career_paths"], dataset["career_course_mapping"], dataset["courses"])
    assert res["status"] == "General Elective"
    assert res["career_score"] == 0.50
    assert "general computing fundamentals" in res["explanation"].lower()

def test_empty_student_profile(dataset):
    """Test recommender behavior on completely empty student profile."""
    empty_student = {}
    top_recs, all_candidates = get_recommended_electives(
        empty_student, dataset["courses"], dataset["prerequisites"], dataset["schedules"], 
        dataset["career_paths"], dataset["career_course_mapping"], top_n=5
    )
    assert len(top_recs) > 0
    # Courses with missing prerequisites should not have is_recommended == True
    for rec in top_recs:
        if not rec["is_eligible"]:
            assert rec["is_recommended"] is False
