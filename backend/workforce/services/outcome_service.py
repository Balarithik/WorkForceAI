import csv
import os
from collections import defaultdict

from django.db.models import Avg, F, Q

from workforce.models import Assignment, TaskOutcome


def record_task_outcome(assignment, actual_completion_hours=None, actual_sla_met=None, actual_success=None):
    if assignment is None:
        return None
    outcome, _ = TaskOutcome.objects.get_or_create(
        assignment=assignment,
        defaults={
            'predicted_success_probability': float(assignment.success_probability),
            'predicted_sla_probability': float(assignment.sla_probability),
            'predicted_completion_hours': float(assignment.predicted_completion_hours),
            'actual_completion_hours': actual_completion_hours,
            'actual_sla_met': actual_sla_met,
            'actual_success': actual_success,
        },
    )
    if actual_completion_hours is not None:
        outcome.actual_completion_hours = actual_completion_hours
    if actual_sla_met is not None:
        outcome.actual_sla_met = actual_sla_met
    if actual_success is not None:
        outcome.actual_success = actual_success
    outcome.predicted_success_probability = float(assignment.success_probability)
    outcome.predicted_sla_probability = float(assignment.sla_probability)
    outcome.predicted_completion_hours = float(assignment.predicted_completion_hours)
    outcome.save()
    return outcome


def calculate_prediction_metrics():
    outcomes = TaskOutcome.objects.filter(actual_completion_hours__isnull=False)
    if not outcomes.exists():
        return {
            'total_outcomes': 0,
            'mae': 0.0,
            'rmse': 0.0,
            'sla_precision': 0.0,
            'sla_recall': 0.0,
        }
    completion_errors = []
    for outcome in outcomes:
        completion_errors.append((outcome.predicted_completion_hours - outcome.actual_completion_hours) ** 2)
    mae = sum(abs(outcome.predicted_completion_hours - outcome.actual_completion_hours) for outcome in outcomes) / outcomes.count()
    rmse = (sum(error for error in completion_errors) / outcomes.count()) ** 0.5
    actual_sla_count = outcomes.filter(actual_sla_met=True).count()
    predicted_sla_count = outcomes.filter(predicted_sla_probability__gte=0.5).count()
    true_positive = outcomes.filter(actual_sla_met=True, predicted_sla_probability__gte=0.5).count()
    precision = true_positive / predicted_sla_count if predicted_sla_count else 0.0
    recall = true_positive / actual_sla_count if actual_sla_count else 0.0
    return {
        'total_outcomes': outcomes.count(),
        'mae': round(float(mae), 4),
        'rmse': round(float(rmse), 4),
        'sla_precision': round(float(precision), 4),
        'sla_recall': round(float(recall), 4),
    }


def export_training_data(output_path='training_data.csv'):
    rows = TaskOutcome.objects.select_related('assignment__task', 'assignment__employee').filter(actual_completion_hours__isnull=False)
    fieldnames = [
        'task_id', 'employee_id', 'priority', 'task_type', 'required_skills', 'estimated_effort_hours',
        'sla_hours', 'skill_match_score', 'current_workload_percent', 'availability', 'experience_years',
        'historical_performance_score', 'predicted_success_probability', 'predicted_sla_probability',
        'predicted_completion_hours', 'actual_completion_hours', 'actual_sla_met', 'actual_success'
    ]
    with open(output_path, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for outcome in rows:
            assignment = outcome.assignment
            task = assignment.task
            worker = assignment.employee
            writer.writerow({
                'task_id': task.task_id,
                'employee_id': worker.employee_id,
                'priority': task.priority,
                'task_type': task.task_type,
                'required_skills': '|'.join(task.required_skills),
                'estimated_effort_hours': task.estimated_effort_hours,
                'sla_hours': task.sla_hours,
                'skill_match_score': assignment.suitability_score / 100.0,
                'current_workload_percent': worker.current_workload_percent,
                'availability': worker.availability,
                'experience_years': worker.experience_years,
                'historical_performance_score': worker.historical_performance_score,
                'predicted_success_probability': outcome.predicted_success_probability,
                'predicted_sla_probability': outcome.predicted_sla_probability,
                'predicted_completion_hours': outcome.predicted_completion_hours,
                'actual_completion_hours': outcome.actual_completion_hours,
                'actual_sla_met': outcome.actual_sla_met,
                'actual_success': outcome.actual_success,
            })
    return output_path
