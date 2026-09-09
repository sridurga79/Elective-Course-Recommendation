import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from src.data_loader import load_raw_data
from src.data_cleaning import clean_and_validate_data
from src.baseline import get_baseline_recommendations
from src.recommendation_engine import get_recommended_electives
from src.prerequisite_engine import check_prerequisite_eligibility
from src.schedule_engine import check_schedule_conflicts

def evaluate_selection_quality(course_ids, student_profile, cleaned_data):
    """
    Calculates overall course choice quality score (0 to 100) for a set of courses.
    Formula:
    - Prerequisite compliance: 40%
    - Schedule feasibility: 30%
    - Career alignment: 30%
    """
    if not course_ids:
        return 0.0
        
    courses_df = cleaned_data["courses"]
    prereqs_df = cleaned_data["prerequisites"]
    schedules_df = cleaned_data["schedules"]
    career_paths_df = cleaned_data["career_paths"]
    mapping_df = cleaned_data["career_course_mapping"]
    
    # 1. Prerequisite compliance (40%)
    prereq_penalties = 0
    for cid in course_ids:
        res = check_prerequisite_eligibility(student_profile, cid, prereqs_df, courses_df)
        if not res["is_eligible"]:
            prereq_penalties += 1
    prereq_score = max(0.0, 1.0 - (prereq_penalties / len(course_ids))) * 40.0
    
    # 2. Schedule conflicts (30%)
    sched_res = check_schedule_conflicts(
        course_ids, schedules_df, 
        student_semester=student_profile.get("current_semester"),
        available_credits=student_profile.get("available_credits"),
        courses_df=courses_df
    )
    sched_score = 30.0
    if sched_res["has_conflict"]:
        sched_score -= min(30.0, len(sched_res["pairwise_conflicts"]) * 15.0 + len(sched_res["semester_mismatches"]) * 10.0)
    if sched_res["credit_info"]["is_overload"]:
        sched_score -= 10.0
    sched_score = max(0.0, sched_score)
    
    # 3. Career score (30%)
    career_goal = student_profile.get("career_goal", "Software Developer")
    c_match = career_paths_df[career_paths_df["career_name"].str.lower() == str(career_goal).lower()]
    career_id = c_match.iloc[0]["career_id"] if not c_match.empty else "CAR01"
    
    avg_relevance = 0.0
    for cid in course_ids:
        m = mapping_df[(mapping_df["career_id"] == career_id) & (mapping_df["course_id"] == cid)]
        if not m.empty:
            avg_relevance += float(m.iloc[0]["relevance_score"])
        else:
            avg_relevance += 40.0
    career_score = (avg_relevance / (len(course_ids) * 100.0)) * 30.0
    
    quality_score = round(prereq_score + sched_score + career_score, 1)
    return quality_score

def run_evaluation_experiment(data_dir=None, output_csv_path=None):
    """
    Runs comprehensive comparative evaluation across all 20 synthetic students.
    Generates evaluation/evaluation_results.csv and summary performance metrics.
    """
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    if output_csv_path is None:
        output_csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evaluation", "evaluation_results.csv")
        
    raw_data = load_raw_data(data_dir)
    cleaned_data, _ = clean_and_validate_data(raw_data)
    
    students_df = cleaned_data["students"]
    courses_df = cleaned_data["courses"]
    prereqs_df = cleaned_data["prerequisites"]
    schedules_df = cleaned_data["schedules"]
    career_paths_df = cleaned_data["career_paths"]
    mapping_df = cleaned_data["career_course_mapping"]
    
    records = []
    
    base_prereq_conflicts_total = 0
    proto_prereq_conflicts_total = 0
    base_sched_conflicts_total = 0
    proto_sched_conflicts_total = 0
    base_valid_recs_total = 0
    proto_valid_recs_total = 0
    total_recs = 0
    
    base_career_scores = []
    proto_career_scores = []
    base_quality_scores = []
    proto_quality_scores = []
    
    for _, student in students_df.iterrows():
        s_profile = student.to_dict()
        sid = s_profile["student_id"]
        
        # 1. Generate Baseline Recommendations (Top 3)
        base_recs = get_baseline_recommendations(s_profile, courses_df, mapping_df, career_paths_df, top_n=3)
        base_cids = [r["course_id"] for r in base_recs]
        
        # 2. Generate Proposed Prototype Recommendations (Top 3)
        # Match semester first, fallback to all electives if needed
        top_sem, _ = get_recommended_electives(s_profile, courses_df, prereqs_df, schedules_df, career_paths_df, mapping_df, top_n=3, filter_semester=True)
        proto_cids = [c["course_id"] for c in top_sem if c["is_eligible"]]
        
        if len(proto_cids) < 3:
            top_all, _ = get_recommended_electives(s_profile, courses_df, prereqs_df, schedules_df, career_paths_df, mapping_df, top_n=6, filter_semester=False)
            for c in top_all:
                if c["is_eligible"] and c["course_id"] not in proto_cids:
                    proto_cids.append(c["course_id"])
                if len(proto_cids) >= 3:
                    break
        proto_cids = proto_cids[:3]
        
        # Prerequisite conflict checks
        base_prereq_conf = sum(1 for cid in base_cids if not check_prerequisite_eligibility(s_profile, cid, prereqs_df, courses_df)["is_eligible"])
        proto_prereq_conf = sum(1 for cid in proto_cids if not check_prerequisite_eligibility(s_profile, cid, prereqs_df, courses_df)["is_eligible"])
        
        # Schedule conflict checks
        base_sched_res = check_schedule_conflicts(base_cids, schedules_df, s_profile["current_semester"], s_profile["available_credits"], courses_df)
        proto_sched_res = check_schedule_conflicts(proto_cids, schedules_df, s_profile["current_semester"], s_profile["available_credits"], courses_df)
        
        base_sched_conf = 1 if base_sched_res["has_conflict"] else 0
        proto_sched_conf = 1 if proto_sched_res["has_conflict"] else 0
        
        # Career scores
        c_match = career_paths_df[career_paths_df["career_name"].str.lower() == str(s_profile.get("career_goal", "")).lower()]
        cid_match = c_match.iloc[0]["career_id"] if not c_match.empty else "CAR01"
        
        def calc_avg_career(cids):
            scores = []
            for c in cids:
                m = mapping_df[(mapping_df["career_id"] == cid_match) & (mapping_df["course_id"] == c)]
                scores.append(float(m.iloc[0]["relevance_score"]) if not m.empty else 40.0)
            return round(float(np.mean(scores)), 1) if scores else 40.0

        base_car_score = calc_avg_career(base_cids)
        proto_car_score = calc_avg_career(proto_cids)
        
        # Choice quality scores
        base_qual = evaluate_selection_quality(base_cids, s_profile, cleaned_data)
        proto_qual = evaluate_selection_quality(proto_cids, s_profile, cleaned_data)
        
        # Valid recommendations
        base_valid = sum(1 for cid in base_cids if check_prerequisite_eligibility(s_profile, cid, prereqs_df, courses_df)["is_eligible"])
        proto_valid = sum(1 for cid in proto_cids if check_prerequisite_eligibility(s_profile, cid, prereqs_df, courses_df)["is_eligible"])
        
        base_prereq_conflicts_total += base_prereq_conf
        proto_prereq_conflicts_total += proto_prereq_conf
        base_sched_conflicts_total += base_sched_conf
        proto_sched_conflicts_total += proto_sched_conf
        base_valid_recs_total += base_valid
        proto_valid_recs_total += proto_valid
        total_recs += len(proto_cids)
        
        base_career_scores.append(base_car_score)
        proto_career_scores.append(proto_car_score)
        base_quality_scores.append(base_qual)
        proto_quality_scores.append(proto_qual)
        
        records.append({
            "student_id": sid,
            "baseline_course": ";".join(base_cids),
            "prototype_course": ";".join(proto_cids),
            "baseline_prerequisite_conflict": base_prereq_conf,
            "prototype_prerequisite_conflict": proto_prereq_conf,
            "baseline_schedule_conflict": base_sched_conf,
            "prototype_schedule_conflict": proto_sched_conf,
            "baseline_career_score": base_car_score,
            "prototype_career_score": proto_car_score,
            "baseline_quality_score": base_qual,
            "prototype_quality_score": proto_qual
        })
        
    df_eval = pd.DataFrame(records)
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    df_eval.to_csv(output_csv_path, index=False)
    
    # Calculate Aggregate Metrics
    prereq_reduction = ((base_prereq_conflicts_total - proto_prereq_conflicts_total) / max(base_prereq_conflicts_total, 1)) * 100.0
    proto_valid_rate = (proto_valid_recs_total / max(total_recs, 1)) * 100.0
    base_valid_rate = (base_valid_recs_total / max(total_recs, 1)) * 100.0
    
    mean_base_career = float(np.mean(base_career_scores))
    mean_proto_career = float(np.mean(proto_career_scores))
    career_improvement = ((mean_proto_career - mean_base_career) / max(mean_base_career, 1)) * 100.0
    
    mean_base_quality = float(np.mean(base_quality_scores))
    mean_proto_quality = float(np.mean(proto_quality_scores))
    
    metrics = {
        "prereq_reduction": round(prereq_reduction, 1),
        "proto_valid_rate": round(proto_valid_rate, 1),
        "base_valid_rate": round(base_valid_rate, 1),
        "base_prereq_conflict_rate": round((base_prereq_conflicts_total / max(total_recs, 1)) * 100.0, 1),
        "proto_prereq_conflict_rate": round((proto_prereq_conflicts_total / max(total_recs, 1)) * 100.0, 1),
        "career_improvement": round(career_improvement, 1),
        "mean_base_career": round(mean_base_career, 1),
        "mean_proto_career": round(mean_proto_career, 1),
        "mean_base_quality": round(mean_base_quality, 1),
        "mean_proto_quality": round(mean_proto_quality, 1),
        "targets": {
            "prereq_reduction_target": 70.0,
            "valid_rate_target": 90.0,
            "career_improvement_target": 20.0,
            "quality_target": 80.0
        },
        "status": {
            "prereq_reduction": "PASS" if prereq_reduction >= 70.0 else "FAIL",
            "valid_rate": "PASS" if proto_valid_rate >= 90.0 else "FAIL",
            "career_improvement": "PASS" if career_improvement >= 20.0 else "FAIL",
            "quality_score": "PASS" if mean_proto_quality >= 80.0 else "FAIL"
        }
    }
    
    return df_eval, metrics

if __name__ == "__main__":
    df_res, summary = run_evaluation_experiment()
    print("=== EVALUATION BENCHMARK SUMMARY ===")
    print(f"Prerequisite Conflict Reduction: {summary['prereq_reduction']}% (Baseline: {summary['base_prereq_conflict_rate']}%, Proto: {summary['proto_prereq_conflict_rate']}%) -> {summary['status']['prereq_reduction']}")
    print(f"Valid Recommendation Rate: {summary['proto_valid_rate']}% (Target: >=90%) -> {summary['status']['valid_rate']}")
    print(f"Career Alignment: Baseline {summary['mean_base_career']}% vs Prototype {summary['mean_proto_career']}% (Impr: {summary['career_improvement']}%) -> {summary['status']['career_improvement']}")
    print(f"Overall Choice Quality: Baseline {summary['mean_base_quality']}/100 vs Prototype {summary['mean_proto_quality']}/100 -> {summary['status']['quality_score']}")
