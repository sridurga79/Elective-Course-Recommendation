# Problem Analysis: University Elective Selection Friction

## 1. Problem Definition
Higher education institutions worldwide are shifting toward flexible, modular degree structures that offer students extensive elective choices across diverse computing tracks (e.g., Artificial Intelligence, Data Science, Cyber Security, Cloud Computing, Software Engineering). While flexibility is pedagogically desirable, it introduces high cognitive load and significant decision friction for students. 

Students frequently select electives based on peer buzzwords, convenience, or perceived ease without understanding:
1. **Prerequisite Requirements**: Deep, multi-tier dependency chains where advanced electives require foundational courses with specific minimum grade thresholds.
2. **Timetable & Schedule Clashes**: Uncoordinated scheduling slots leading to same-day, overlapping lectures or lab sessions.
3. **Course Learning Outcomes**: What technical competencies and practical skills the course actually develops.
4. **Long-Term Career Consequences**: How elective choices compound to qualify or disqualify students for specific industry roles upon graduation.

## 2. Target Users & Stakeholder Personas
- **Undergraduate Students (Semesters 3–7)**: Need transparent guidance on which courses they are eligible to take and how each option aligns with their career aspirations.
- **Academic Advisors**: Often overwhelmed during 2-week enrollment windows, spending up to 30 minutes per student manually cross-referencing degree audits, timetable spreadsheets, and course prerequisites.
- **Department Chairs & Curriculum Committees**: Require empirical visibility into enrollment bottlenecks, elective demand, and curriculum alignment.
- **Transfer / Lateral Entry Students**: Face complex credit-transfer mappings that make prerequisite eligibility ambiguous.

## 3. Root Causes of Course Choice Failure
- **Information Asymmetry**: Course descriptions, prerequisite requirements, timetable schedules, and career roadmaps reside in disparate, static PDF catalogs or disjointed portal pages.
- **Cognitive Overload**: A catalog of 40+ electives across 8+ specialized pathways overwhelms students, driving them toward superficial selection criteria.
- **Lack of Feedback Mechanisms**: Traditional enrollment portals only validate prerequisites at the moment of enrollment submission, leading to last-minute rejections, panic drops, and credit underload.
- **Implicit Career Pathways**: Universities rarely publish granular, skill-level mappings connecting elective learning outcomes to specific industry role requirements.

## 4. Proposed Intervention
The **Prerequisite & Career-Consequence Explorer** is a lightweight, rule-based decision support system that unites:
- Multi-tier recursive prerequisite chain validation (with minimum grade compliance).
- Pairwise timetable conflict and credit overload detection.
- Quantitative career competency and learning outcome keyword matching.
- A transparent, weighted recommendation engine:
  $$\text{Score} = 0.30 \cdot \text{Prereq} + 0.30 \cdot \text{Career} + 0.20 \cdot \text{Outcome} + 0.10 \cdot \text{Schedule} + 0.10 \cdot \text{Preference}$$
- Natural language pedagogical explanations ("Why this course?" and "Why not recommended?").

## 5. Success Metrics & Targets
- **Prerequisite Conflict Reduction**: $\ge 70\%$ reduction compared to unguided student baseline.
- **Valid Recommendation Rate**: $\ge 90\%$ of recommended electives must be 100% prerequisite-cleared.
- **Career Alignment Improvement**: $\ge 20\%$ improvement in target career competency coverage.
- **Course Choice Quality Score**: Overall selection quality score $\ge 80 / 100$.

## 6. Institutional Constraints
- **Zero Cost Infrastructure**: Must run on standard laboratory desktop computers without expensive cloud hosting or paid SaaS licenses.
- **No External API Dependencies**: Must not depend on commercial LLM APIs, external database servers, or paid microservices.
- **Auditability & Explainability**: The scoring model must be completely transparent and explainable to students and faculty without black-box opacity.
