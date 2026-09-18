import json
from django.db import transaction

from workforce.models import AllocationDecision, Assignment


def record_decision(task, employee, assignment=None, trigger_type='INITIAL_ASSIGNMENT', candidate_rank=1,
                   score_breakdown=None, decision_reason='', allocation_status='ACTIVE', decision_context=None,
                   metrics=None):
    metrics = metrics or {}
    decision_context = decision_context or {}
    score_breakdown = score_breakdown or {}

    decision = AllocationDecision.objects.create(
        task=task,
        employee=employee,
        assignment=assignment,
        trigger_type=trigger_type,
        success_probability=float(metrics.get('success_probability', assignment.success_probability if assignment else 0.0)),
        sla_probability=float(metrics.get('sla_probability', assignment.sla_probability if assignment else 0.0)),
        predicted_completion_hours=float(metrics.get('predicted_completion_hours', assignment.predicted_completion_hours if assignment else 0.0)),
        skill_match_score=float(metrics.get('skill_match_score', 0.0)),
        workload_percent=float(metrics.get('current_workload_percent', employee.current_workload_percent)),
        available_capacity_percent=float(metrics.get('available_capacity_percent', max(100 - employee.current_workload_percent, 0))),
        suitability_score=float(metrics.get('suitability_score', assignment.suitability_score if assignment else 0.0)),
        score_breakdown=dict(score_breakdown),
        rank=int(candidate_rank),
        decision_reason=decision_reason,
        allocation_status=allocation_status,
        decision_context=dict(decision_context),
    )
    return decision


def get_task_decision_history(task_id):
    return AllocationDecision.objects.filter(task_id=task_id).select_related('task', 'employee', 'assignment').order_by('created_at')


def get_decision_replay(task_id):
    decisions = get_task_decision_history(task_id)
    history = []
    for decision in decisions:
        history.append({
            'id': decision.id,
            'created_at': decision.created_at,
            'trigger_type': decision.trigger_type,
            'employee': {
                'id': decision.employee.id,
                'employee_id': decision.employee.employee_id,
                'name': decision.employee.name,
            },
            'suitability_score': decision.suitability_score,
            'skill_match_score': decision.skill_match_score,
            'sla_probability': decision.sla_probability,
            'success_probability': decision.success_probability,
            'predicted_completion_hours': decision.predicted_completion_hours,
            'decision_reason': decision.decision_reason,
            'rank': decision.rank,
            'allocation_status': decision.allocation_status,
            'score_breakdown': decision.score_breakdown,
        })
    return history
