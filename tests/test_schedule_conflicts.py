import pytest
import os
import pandas as pd
from src.data_loader import load_raw_data
from src.data_cleaning import clean_and_validate_data
from src.schedule_engine import check_schedule_conflicts, check_time_overlap

@pytest.fixture
def dataset():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    raw = load_raw_data(data_dir)
    cleaned, _ = clean_and_validate_data(raw)
    return cleaned

def test_time_overlap_function():
    """Unit test for boundary time overlap logic."""
    assert check_time_overlap("10:00", "11:30", "10:30", "12:00") is True
    assert check_time_overlap("10:00", "11:30", "11:30", "13:00") is False  # Back-to-back
    assert check_time_overlap("14:00", "15:30", "16:00", "17:30") is False  # Disjoint
    assert check_time_overlap("11:00", "12:30", "11:00", "12:30") is True   # Exact match

def test_intentional_schedule_conflict_detection(dataset):
    """CS302 (Mon 10:00-11:30) and CS304 (Mon 10:30-12:00) should trigger schedule conflict."""
    selected = ["CS302", "CS304"]
    res = check_schedule_conflicts(selected, dataset["schedules"], student_semester=5, available_credits=15, courses_df=dataset["courses"])
    assert res["has_conflict"] is True
    assert len(res["pairwise_conflicts"]) >= 1
    conflict = res["pairwise_conflicts"][0]
    assert conflict["day"] == "Monday"
    assert "overlaps with" in conflict["message"]

def test_no_schedule_conflict(dataset):
    """CS301 (Mon 13:00-14:30) and CS420 (Fri 10:00-11:30) should have no schedule conflict."""
    selected = ["CS301", "CS420"]
    res = check_schedule_conflicts(selected, dataset["schedules"], student_semester=5, available_credits=15, courses_df=dataset["courses"])
    assert len(res["pairwise_conflicts"]) == 0

def test_semester_mismatch_detection(dataset):
    """Student in Semester 5 selecting CS401 (offered in Semester 7)."""
    selected = ["CS401"]
    res = check_schedule_conflicts(selected, dataset["schedules"], student_semester=5, available_credits=15, courses_df=dataset["courses"])
    assert len(res["semester_mismatches"]) == 1
    assert res["semester_mismatches"][0]["course_id"] == "CS401"
    assert "Semester Mismatch" in res["semester_mismatches"][0]["message"]

def test_credit_overload_detection(dataset):
    """Total credits exceeding student's available credits."""
    # CS301 (3), CS302 (3), CS304 (3) = 9 credits. Available: 6 credits.
    selected = ["CS301", "CS302", "CS304"]
    res = check_schedule_conflicts(selected, dataset["schedules"], student_semester=5, available_credits=6, courses_df=dataset["courses"])
    assert res["credit_info"]["is_overload"] is True
    assert res["credit_info"]["total_credits"] == 9
    assert res["credit_info"]["overload_credits"] == 3
