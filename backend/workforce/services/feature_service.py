def normalize_required_skills(value):
    if not value:
        return []
    if isinstance(value, str):
        candidate = value.replace('|', ',')
        return [item.strip() for item in candidate.split(',') if item and item.strip()]
    return [str(item).strip() for item in value if str(item).strip()]


def normalize_task_priority(value):
    if not value:
        return 'Medium'
    text = str(value).strip()
    mapping = {
        'LOW': 'Low',
        'MEDIUM': 'Medium',
        'HIGH': 'High',
        'CRITICAL': 'Critical',
        'low': 'Low',
        'medium': 'Medium',
        'high': 'High',
        'critical': 'Critical',
    }
    if text in mapping:
        return mapping[text]
    return text.title()


def normalize_task_type(value):
    if not value:
        return 'Software Development'
    text = str(value).strip()
    mapping = {
        'Backend Development': 'Software Development',
        'Frontend UI': 'Software Development',
        'Frontend Development': 'Software Development',
        'Infrastructure': 'Cloud/DevOps',
        'DevOps': 'Cloud/DevOps',
        'Data Science': 'Data Engineering',
        'Data Engineering': 'Data Engineering',
        'Machine Learning': 'Machine Learning',
        'ML': 'Machine Learning',
        'Cybersecurity': 'Cybersecurity',
        'Database': 'Database',
        'Testing': 'Testing',
        'Support': 'Support',
        'Bug Fix': 'Bug Fix',
        'Bug Fixes': 'Bug Fix',
    }
    return mapping.get(text, text)


def calculate_skill_match_score(employee_skills, task_required_skills):
    if not task_required_skills:
        return 1.0

    emp_skills_lower = [s.lower() for s in employee_skills]
    task_skills_lower = [s.lower() for s in task_required_skills]

    match_count = sum(1 for s in task_skills_lower if s in emp_skills_lower)
    return match_count / len(task_required_skills)


def calculate_distance_km(employee_location, task_location):
    if not task_location:
        return 0.0
    if str(task_location).lower() == 'remote':
        return 0.0
    if str(employee_location).lower() == str(task_location).lower():
        return 0.0
    return 50.0


def calculate_location_compatibility(employee_location, task_location):
    if not task_location:
        return 1.0
    if str(task_location).lower() == 'remote':
        return 1.0
    if str(employee_location).lower() == str(task_location).lower():
        return 1.0
    return 0.5


def extract_features(employee, task):
    required_skills = normalize_required_skills(getattr(task, 'required_skills', []))
    required_skill_count = len(required_skills)

    skill_match_score = calculate_skill_match_score(employee.skills or [], required_skills)
    distance_km = calculate_distance_km(employee.location, task.location)
    location_compatibility = calculate_location_compatibility(employee.location, task.location)

    availability = 1 if getattr(employee, 'availability', 'AVAILABLE') == 'AVAILABLE' else 0
    workload_capacity = max(100 - employee.current_workload_percent, 0)

    experience_performance_score = employee.experience_years * employee.historical_performance_score
    sla_urgency_ratio = task.remaining_sla_hours / max(task.estimated_effort_hours, 1)
    workload_effort_ratio = employee.current_workload_percent / max(task.estimated_effort_hours, 1)

    task_priority = normalize_task_priority(getattr(task, 'priority', 'Medium'))
    task_type = normalize_task_type(getattr(task, 'task_type', 'Software Development'))

    base = {
        'task_type': task_type,
        'task_priority': task_priority,
        'experience_years': employee.experience_years,
        'skill_match_score': skill_match_score,
        'employee_workload_percent': employee.current_workload_percent,
        'employee_availability': availability,
        'employee_performance_score': employee.historical_performance_score,
        'employee_location': employee.location,
        'task_location': task.location,
        'distance_km': distance_km,
        'similar_tasks_completed': employee.similar_tasks_completed,
        'similar_tasks_success_rate': employee.similar_tasks_success_rate,
        'estimated_effort_hours': task.estimated_effort_hours,
        'sla_hours': task.sla_hours,
        'remaining_sla_hours': task.remaining_sla_hours,
        'workload_capacity': workload_capacity,
        'availability_score': availability,
        'location_compatibility': location_compatibility,
        'experience_performance_score': experience_performance_score,
        'sla_urgency_ratio': sla_urgency_ratio,
        'workload_effort_ratio': workload_effort_ratio,
        'required_skill_count': required_skill_count,
        'experience_years_x': employee.experience_years,
        'estimated_effort_hours_y': task.estimated_effort_hours,
        'sla_hours_y': task.sla_hours,
        'task_type_y': task_type,
        'task_priority_y': task_priority,
        'historical_performance_score': employee.historical_performance_score,
    }
    return base
