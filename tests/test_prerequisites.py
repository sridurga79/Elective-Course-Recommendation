import pytest
import os
import pandas as pd
from src.data_loader import load_raw_data
from src.data_cleaning import clean_and_validate_data
from src.prerequisite_engine import check_prerequisite_eligibility, get_prerequisite_chain

@pytest.fixture
def dataset():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    raw = load_raw_data(data_dir)
    cleaned, _ = clean_and_validate_data(raw)
    return cleaned

def test_no_prerequisite_course(dataset):
    """CS101 has no prerequisites; should always be eligible."""
    student = {"completed_courses": "", "grades": ""}
    res = check_prerequisite_eligibility(student, "CS101", dataset["prerequisites"], dataset["courses"])
    assert res["is_eligible"] is True
    assert res["status"] == "Eligible"
    assert "no prerequisite" in res["explanation"].lower()

def test_valid_prerequisite_completed(dataset):
    """CS201 requires CS101. Student with CS101:A should be eligible."""
    student = {"completed_courses": "CS101", "grades": "CS101:A"}
    res = check_prerequisite_eligibility(student, "CS201", dataset["prerequisites"], dataset["courses"])
    assert res["is_eligible"] is True
    assert res["status"] == "Eligible"
    assert "all prerequisites satisfied" in res["explanation"].lower()

def test_missing_prerequisite(dataset):
    """CS301 requires CS201. Student with only CS101 should be missing CS201."""
    student = {"completed_courses": "CS101", "grades": "CS101:A"}
    res = check_prerequisite_eligibility(student, "CS301", dataset["prerequisites"], dataset["courses"])
    assert res["is_eligible"] is False
    assert res["status"] == "Missing Prerequisite"
    assert "CS201" in res["missing_prerequisites"]
    assert "requires CS201" in res["explanation"]

def test_grade_threshold_failure(dataset):
    """CS301 requires CS201 with minimum grade C. Student has CS201:D -> Not satisfied."""
    student = {"completed_courses": "CS101;CS201", "grades": "CS101:A;CS201:D"}
    res = check_prerequisite_eligibility(student, "CS301", dataset["prerequisites"], dataset["courses"])
    assert res["is_eligible"] is False
    assert res["status"] == "Prerequisite Grade Not Satisfied"
    assert len(res["grade_failures"]) == 1
    assert res["grade_failures"][0]["student_grade"] == "D"
    assert "requires grade 'C'" in res["explanation"]

def test_multi_hop_prerequisite_chain(dataset):
    """Verify recursive traversal of multi-tier prerequisite chain."""
    chain = get_prerequisite_chain("CS303", dataset["prerequisites"])
    # CS303 -> CS302 -> CS201, MATH201
    assert len(chain) > 0
    p_ids = [item["prerequisite_course_id"] for item in chain]
    assert "CS302" in p_ids
    sub_prereqs = chain[0]["sub_prerequisites"]
    sub_ids = [item["prerequisite_course_id"] for item in sub_prereqs]
    assert "CS201" in sub_ids


def test_downstream_course_unlock(dataset):
    """Taking CS302 (Machine Learning) should unlock CS401, CS402, CS403, and CS423."""
    from src.prerequisite_engine import get_unlocked_courses
    unlocked = get_unlocked_courses(["CS302"], dataset["prerequisites"], dataset["courses"])
    unlocked_ids = [u["unlocked_course_id"] for u in unlocked]
    assert "CS401" in unlocked_ids
    assert "CS402" in unlocked_ids
    assert "CS403" in unlocked_ids


def test_prerequisite_dag_construction(dataset):
    """Verify DAG structure generation for multi-tier course."""
    from src.prerequisite_engine import build_prerequisite_dag
    nodes, edges, coords = build_prerequisite_dag("CS401", dataset["prerequisites"], {"CS101", "CS201"})
    assert "CS401" in nodes
    assert "CS302" in nodes
    assert "CS201" in nodes
    assert nodes["CS201"]["status"] == "Completed"
    assert nodes["CS302"]["status"] == "Missing"
    assert len(edges) >= 3
