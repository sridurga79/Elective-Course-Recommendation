import pytest
import os
import pandas as pd
from src.data_loader import load_raw_data
from src.data_cleaning import clean_and_validate_data
from src.recommendation_engine import get_recommended_electives, compute_recommendation_score

@pytest.fixture
def dataset():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    raw = load_raw_data(data_dir)
    cleaned, _ = clean_and_validate_data(raw)
    return cleaned

def test_recommendation_scoring_formula():
    """Verify exact formula: 0.30*prereq + 0.30*career + 0.20*outcome + 0.10*sched + 0.10*pref."""
    score = compute_recommendation_score(1.0, 1.0, 1.0, 1.0, 1.0)
    assert score == 100.0
    
    score_half = compute_recommendation_score(1.0, 0.5, 0.5, 0.5, 0.5)
    # 0.30*1 + 0.30*0.5 + 0.20*0.5 + 0.10*0.5 + 0.10*0.5 = 0.30 + 0.15 + 0.10 + 0.05 + 0.05 = 0.65 -> 65.0
    assert score_half == 65.0

def test_unmet_prerequisite_receives_zero_eligibility(dataset):
    """Verify that courses with unmet prerequisites have is_eligible=False and low scores."""
    student = {
        "student_id": "TEST_STUDENT",
        "completed_courses": "CS101",
        "grades": "CS101:B",
        "current_semester": 5,
        "career_goal": "Data Scientist"
    }
    top_recs, all_candidates = get_recommended_electives(
        student, dataset["courses"], dataset["prerequisites"], dataset["schedules"],
        dataset["career_paths"], dataset["career_course_mapping"], top_n=5, filter_semester=False
    )
    # Find CS302 (requires CS201 & MATH201, which student hasn't completed)
    cs302_cand = next((c for c in all_candidates if c["course_id"] == "CS302"), None)
    assert cs302_cand is not None
    assert cs302_cand["is_eligible"] is False
    assert cs302_cand["score_breakdown"]["prerequisite_score"] == 0.0

def test_top_n_recommendations_order(dataset):
    """Top recommendations should be ranked with highest eligible score first."""
    student = {
        "student_id": "S101",
        "completed_courses": "CS101;MATH101;CS102;MATH201;CS201",
        "grades": "CS101:A;MATH101:A;CS102:B;MATH201:A;CS201:A",
        "current_semester": 5,
        "career_goal": "Data Scientist"
    }
    top_recs, _ = get_recommended_electives(
        student, dataset["courses"], dataset["prerequisites"], dataset["schedules"],
        dataset["career_paths"], dataset["career_course_mapping"], top_n=5
    )
    assert len(top_recs) == 5
    # Scores should be in descending order
    scores = [r["recommendation_score"] for r in top_recs]
    assert scores == sorted(scores, reverse=True)
    # First recommendation should be highly career aligned for Data Scientist (e.g. CS302 or CS307)
    assert top_recs[0]["course_id"] in ["CS302", "CS307", "CS301"]
