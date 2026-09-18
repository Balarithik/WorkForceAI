import joblib
import pandas as pd

# ------------------------------------------------------------
# AI-04 local model test
# ------------------------------------------------------------
# Put these three .pkl files in the same folder as this script:
#   task_success_model.pkl
#   sla_model.pkl
#   completion_time_model.pkl
#
# IMPORTANT:
# These models were trained with scikit-learn 1.6.1.
# ------------------------------------------------------------

SUCCESS_MODEL = "task_success_model.pkl"
SLA_MODEL = "sla_model.pkl"
COMPLETION_MODEL = "completion_time_model.pkl"

# ------------------------------------------------------------
# 1. Define the correct paths using r"..." for raw strings
# ------------------------------------------------------------
BASE_DIR = r"E:\projects\WorkForceAI"
SUCCESS_MODEL = BASE_DIR + "\\task_success_model.pkl"
SLA_MODEL = BASE_DIR + "\\sla_model.pkl"
COMPLETION_MODEL = BASE_DIR + "\\completion_time_model.pkl"

# ------------------------------------------------------------
# 2. Load the models
# ------------------------------------------------------------
try:
    success_model = joblib.load(SUCCESS_MODEL)
    sla_model = joblib.load(SLA_MODEL)
    completion_model = joblib.load(COMPLETION_MODEL)
    print("All 3 models loaded successfully.\n")
except FileNotFoundError as e:
    print(f"Error loading models: {e}")
    print("Please ensure the model files are in the correct directory.")
    exit(1) # Exit if models cannot be loaded

# Example employee + task
employee = {
    "experience_years": 4,
    "current_workload_percent": 30,
    "availability": 1,
    "historical_performance_score": 9.0,
    "location": "Coimbatore",

    # These are historical/context fields used by the trained model.
    # For a first prototype, you can supply reasonable values.
    "similar_tasks_completed": 12,
    "similar_tasks_success_rate": 0.92
}

task = {
    "task_type": "Machine Learning",
    "task_priority": "Critical",
    "required_skills": "Python|Machine Learning",
    "estimated_effort_hours": 8,
    "sla_hours": 24,
    "remaining_sla_hours": 24,
    "task_location": "Remote",

    # Example context values.
    # Replace with your real matching/calculation logic later.
    "skill_match_score": 1.0,
    "distance_km": 0.0,
    "location_compatibility": 1.0
}

required_skill_count = len(task["required_skills"].split("|"))

row = {
    "task_type": task["task_type"],
    "task_priority": task["task_priority"],
    "experience_years": employee["experience_years"],
    "skill_match_score": task["skill_match_score"],
    "employee_workload_percent": employee["current_workload_percent"],
    "employee_availability": employee["availability"],
    "employee_performance_score": employee["historical_performance_score"],
    "employee_location": employee["location"],
    "task_location": task["task_location"],
    "distance_km": task["distance_km"],
    "similar_tasks_completed": employee["similar_tasks_completed"],
    "similar_tasks_success_rate": employee["similar_tasks_success_rate"],
    "estimated_effort_hours": task["estimated_effort_hours"],
    "sla_hours": task["sla_hours"],
    "remaining_sla_hours": task["remaining_sla_hours"],
    "workload_capacity": 100 - employee["current_workload_percent"],
    "availability_score": employee["availability"],
    "location_compatibility": task["location_compatibility"],
    "experience_performance_score":
        employee["experience_years"] * employee["historical_performance_score"],
    "sla_urgency_ratio":
        task["remaining_sla_hours"] / max(task["estimated_effort_hours"], 1),
    "workload_effort_ratio":
        employee["current_workload_percent"] / max(task["estimated_effort_hours"], 1),
    "required_skill_count": required_skill_count
}

X = pd.DataFrame([row])

success_probability = float(success_model.predict_proba(X)[0][1])
sla_probability = float(sla_model.predict_proba(X)[0][1])
predicted_hours = float(completion_model.predict(X)[0])

# Same suitability concept used during model development.
time_score = min(1.0, task["sla_hours"] / max(predicted_hours, 0.1))
suitability_score = 100 * (
    0.50 * success_probability +
    0.30 * sla_probability +
    0.20 * time_score
)

print("===== AI-04 Prediction =====")
print(f"Success probability      : {success_probability:.2%}")
print(f"SLA probability          : {sla_probability:.2%}")
print(f"Predicted completion     : {predicted_hours:.2f} hours")
print(f"Suitability score        : {suitability_score:.2f}/100")

print("\n===== Decision =====")
if employee["availability"] != 1:
    print("Employee is unavailable -> DO NOT ASSIGN")
elif suitability_score >= 80:
    print("Highly suitable candidate")
elif suitability_score >= 60:
    print("Potential candidate")
else:
    print("Low suitability -> consider another employee")
