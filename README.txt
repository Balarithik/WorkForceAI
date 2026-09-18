AI-04 Synthetic Training Dataset
==================================

Files
-----
employees.csv
    300 employee master records.

tasks.csv
    5,000 synthetic task records.

historical_assignments.csv
    20,000 synthetic historical employee-task assignment outcomes.
    This is the primary ML training file.

Recommended targets
-------------------
Classification:
    task_success
    sla_met

Regression:
    actual_completion_hours

Recommended features
--------------------
task_type
task_priority
required_skills (or use skill_match_score)
experience_years
skill_match_score
employee_workload_percent
employee_availability
employee_performance_score
employee_location
task_location
distance_km
similar_tasks_completed
similar_tasks_success_rate
estimated_effort_hours
sla_hours
remaining_sla_hours
workload_capacity
availability_score
location_compatibility
experience_performance_score
sla_urgency_ratio
workload_effort_ratio

Do NOT use:
    record_id
    employee_id
    task_id

These are identifiers, not predictive features.

Important
---------
This dataset is synthetic and intended for prototyping/model-development.
It intentionally contains realistic relationships so that ML models can learn
non-random patterns. It is not real company/employee data.
