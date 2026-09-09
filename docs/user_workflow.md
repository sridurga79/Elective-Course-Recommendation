# User Workflow: Student Journey and System Dynamics

## 1. End-to-End User Journey Flowchart

```text
[Student Opens Application]
            │
            ▼
[Profile Setup / Selection] ──► (Select Synthetic Persona OR Input Custom Completed Courses & Grades)
            │
            ▼
[Career Goal Declaration] ───► (Select from 8 Specializations: AI, Data Science, Cyber Sec, etc.)
            │
            ▼
[Automated Catalog Ingestion & Diagnostic Validation]
            │
            ▼
[Multi-Tier Prerequisite Filtering] ──► Disqualifies Ineligible Courses (Sets Prereq Score = 0)
            │
            ▼
[Timetable Conflict & Schedule Matching] ──► Evaluates Preferred Days & Overlap Potential
            │
            ▼
[Career Competency & Outcome Scoring] ──► Matches Course Learning Outcomes to Industry Skills
            │
            ▼
[Transparent Recommendation Ranking] ──► Ranks Top 5 Electives with "Why This Course?" Rationales
            │
            ▼
[Interactive Course Comparison] ──► Side-by-Side Analysis of 2–3 Electives
            │
            ▼
[Selection Basket & Validation] ──► Student Clicks "Validate My Electives"
            │
            ▼
[Comprehensive Quality Report] ──► Final Choice Quality Score (0–100) + Warnings & Overload Alerts
```

## 2. Decision Points & State Transitions

| Step | User Action | System State | Output / Visual Feedback |
| :--- | :--- | :--- | :--- |
| **1. Profile Selection** | Selects S101 or creates custom student profile | Ingests completed courses, grades, credits, semester | Profile card updates; completed course count displayed |
| **2. Career Alignment** | Selects target career pathway (e.g. Data Scientist) | Career engine queries career mapping table and competency requirements | Target skills loaded; skill gap radar initialized |
| **3. Recommendation** | Reviews ranked cards in Tab 1 | Recommender applies 5-part weighted scoring formula | Top 5 electives shown with eligibility badges and score breakdowns |
| **4. Prerequisite Audit** | Selects any catalog course in Tab 2 | Engine recursively traverses prerequisite graph | Full ancestry tree rendered; exact missing courses or grade failures explained |
| **5. Timetable Audit** | Selects tentative courses in Tab 3 | Schedule engine tests pairwise interval overlaps | Overlapping lecture hours and room locations flagged in red |
| **6. Comparison** | Selects 2-3 electives in Tab 5 | Course comparator extracts metadata side-by-side | Direct comparison matrix showing credits, difficulty, outcomes, and scores |
| **7. Final Basket Validation**| Clicks "Validate My Electives" in Tab 6 | System executes holistic validation audit | Overall Choice Quality Score (0–100) with green/yellow/red badges |

## 3. Failure States & System Handling

1. **Missing Prerequisite**: 
   - *State*: Student has not completed a required ancestor course.
   - *System Action*: Block recommendation, award 0 prerequisite score, display natural language warning: `"NOT ELIGIBLE: Course CS301 requires CS201, which has not been completed."`
2. **Prerequisite Grade Not Satisfied**:
   - *State*: Student completed prerequisite course but obtained a grade below the required threshold (e.g., Grade D vs required Grade C).
   - *System Action*: Block recommendation and display: `"NOT ELIGIBLE: Requires grade 'C' in CS201, but student achieved 'D'."`
3. **Timetable Collision**:
   - *State*: Two selected electives share the same day and have overlapping start/end intervals.
   - *System Action*: Display red alert highlighting both courses, start/end intervals, and conflicting classrooms.
4. **Credit Overload**:
   - *State*: Enrolled credit sum exceeds student's allowed budget (e.g. 18 cr enrolled vs 15 cr budget).
   - *System Action*: Flag excess credit amount and apply quality penalty in final validation score.
5. **Undeclared Career Goal**:
   - *State*: Student has not decided on a specialization.
   - *System Action*: Fall back gracefully to foundational core computing electives with moderate neutral scores.
