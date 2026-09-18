import joblib
import pandas as pd

success_model = joblib.load("task_success_model.pkl")
sla_model = joblib.load("sla_model.pkl")
completion_model = joblib.load("completion_time_model.pkl")

# Add your real employees here later.
employees = [
    {
        "employee_id": "E001",
        "experience_years": 4,
        "current_workload_percent": 30,
        "availability": 1,
        "historical_performance_score": 9.0,
        "location": "Coimbatore",
        "similar_tasks_completed": 12,
        "similar_tasks_success_rate": 0.92,
        "skill_match_score": 1.0
    },
    {
        "employee_id": "E002",
        "experience_years": 3,
        "current_workload_percent": 70,
        "availability": 1,
        "historical_performance_score": 8.4,
        "location": "Chennai",
        "similar_tasks_completed": 9,
        "similar_tasks_success_rate": 0.82,
        "skill_match_score": 0.75
    },
    {
        "employee_id": "E003",
        "experience_years": 6,
        "current_workload_percent": 20,
        "availability": 1,
        "historical_performance_score": 9.2,
        "location": "Bangalore",
        "similar_tasks_completed": 18,
        "similar_tasks_success_rate": 0.95,
        "skill_match_score": 1.0
    }
]

task = {
    "task_type": "Machine Learning",
    "task_priority": "Critical",
    "required_skills": "Python|Machine Learning",
    "estimated_effort_hours": 8,
    "sla_hours": 24,
    "remaining_sla_hours": 24,
    "task_location": "Remote",
    "distance_km": 0.0,
    "location_compatibility": 1.0
}

rows = []
for e in employees:
    X = pd.DataFrame([{
        "task_type": task["task_type"],
        "task_priority": task["task_priority"],
        "experience_years": e["experience_years"],
        "skill_match_score": e["skill_match_score"],
        "employee_workload_percent": e["current_workload_percent"],
        "employee_availability": e["availability"],
        "employee_performance_score": e["historical_performance_score"],
        "employee_location": e["location"],
        "task_location": task["task_location"],
        "distance_km": task["distance_km"],
        "similar_tasks_completed": e["similar_tasks_completed"],
        "similar_tasks_success_rate": e["similar_tasks_success_rate"],
        "estimated_effort_hours": task["estimated_effort_hours"],
        "sla_hours": task["sla_hours"],
        "remaining_sla_hours": task["remaining_sla_hours"],
        "workload_capacity": 100 - e["current_workload_percent"],
        "availability_score": e["availability"],
        "location_compatibility": task["location_compatibility"],
        "experience_performance_score": e["experience_years"] * e["historical_performance_score"],
        "sla_urgency_ratio": task["remaining_sla_hours"] / max(task["estimated_effort_hours"], 1),
        "workload_effort_ratio": e["current_workload_percent"] / max(task["estimated_effort_hours"], 1),
        "required_skill_count": len(task["required_skills"].split("|"))
    }])

    success = float(success_model.predict_proba(X)[0][1])
    sla = float(sla_model.predict_proba(X)[0][1])
    hours = float(completion_model.predict(X)[0])

    time_score = min(1.0, task["sla_hours"] / max(hours, 0.1))
    suitability = 100 * (0.50*success + 0.30*sla + 0.20*time_score)

    rows.append({
        "employee_id": e["employee_id"],
        "success_probability": success,
        "sla_probability": sla,
        "predicted_hours": hours,
        "suitability_score": suitability
    })

result = pd.DataFrame(rows).sort_values("suitability_score", ascending=False)

print(result.to_string(index=False, formatters={
    "success_probability": "{:.2%}".format,
    "sla_probability": "{:.2%}".format,
    "predicted_hours": "{:.2f}".format,
    "suitability_score": "{:.2f}".format
}))
