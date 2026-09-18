import os
from django.db.models import Q

from workforce.models import Assignment, Task, Employee


DEFAULT_THRESHOLDS = {
    'LOW': 0.20,
    'MEDIUM': 0.50,
    'HIGH': 0.75,
    'CRITICAL': 1.0,
}


def get_risk_thresholds():
    configured = os.getenv('SLA_RISK_THRESHOLDS', '')
    if not configured:
        return DEFAULT_THRESHOLDS
    thresholds = {}
    for item in configured.split(','):
        if not item or ':' not in item:
            continue
        key, value = item.split(':', 1)
        key = key.strip().upper()
        try:
            thresholds[key] = float(value)
        except ValueError:
            continue
    if not thresholds:
        return DEFAULT_THRESHOLDS
    return thresholds


def calculate_sla_risk(sla_probability):
    probability = max(0.0, min(1.0, float(sla_probability or 0.0)))
    risk_probability = 1.0 - probability
    thresholds = get_risk_thresholds()
    low = float(thresholds.get('LOW', 0.20))
    medium = float(thresholds.get('MEDIUM', 0.50))
    high = float(thresholds.get('HIGH', 0.75))
    if risk_probability <= low:
        level = 'LOW'
    elif risk_probability <= medium:
        level = 'MEDIUM'
    elif risk_probability <= high:
        level = 'HIGH'
    else:
        level = 'CRITICAL'
    return {
        'sla_probability': probability,
        'sla_risk_probability': risk_probability,
        'sla_risk_level': level,
    }


def get_sla_risks():
    tasks = Task.objects.filter(status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS'])
    result = []
    for task in tasks:
        assignment = Assignment.objects.filter(task=task, status='ACTIVE').select_related('employee').first()
        employee = assignment.employee if assignment else None
        sla_probability = float(assignment.sla_probability) if assignment else 0.0
        risk = calculate_sla_risk(sla_probability)
        remaining_sla_hours = max(float(task.remaining_sla_hours or 0), 0)
        predicted_hours = float(assignment.predicted_completion_hours) if assignment else 0.0
        result.append({
            'task_id': task.task_id,
            'title': task.title,
            'priority': task.priority,
            'status': task.status,
            'deadline': task.deadline,
            'remaining_sla_hours': remaining_sla_hours,
            'predicted_completion_hours': predicted_hours,
            'sla_probability': risk['sla_probability'],
            'sla_risk_probability': risk['sla_risk_probability'],
            'sla_risk_level': risk['sla_risk_level'],
            'employee': {
                'employee_id': employee.employee_id,
                'name': employee.name,
                'availability': employee.availability,
            } if employee else None,
        })
    return sorted(result, key=lambda item: item['sla_risk_probability'], reverse=True)
