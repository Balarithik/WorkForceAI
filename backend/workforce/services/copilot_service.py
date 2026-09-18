from __future__ import annotations

from workforce.models import Employee, Task, Assignment, Event
from workforce.services.sla_risk_service import get_sla_risks
from workforce.services.decision_service import get_decision_replay


def get_employee_summary():
    return list(Employee.objects.all().values(
        'id', 'employee_id', 'name', 'department', 'availability', 'location',
        'current_workload_percent', 'historical_performance_score', 'experience_years'
    ))


def get_task_summary(task=None):
    if task is not None:
        return {
            'task_id': task.task_id,
            'title': task.title,
            'status': task.status,
            'priority': task.priority,
            'required_skills': task.required_skills,
            'estimated_effort_hours': task.estimated_effort_hours,
            'sla_hours': task.sla_hours,
            'remaining_sla_hours': task.remaining_sla_hours,
            'deadline': task.deadline,
            'assigned_employee': task.assignments.filter(status='ACTIVE').first().employee.name if task.assignments.filter(status='ACTIVE').exists() else None,
        }
    return list(Task.objects.all().values('id', 'task_id', 'title', 'priority', 'status', 'required_skills'))


def get_current_assignments():
    return list(Assignment.objects.filter(status='ACTIVE').select_related('employee', 'task').values(
        'id', 'task_id', 'employee_id', 'status', 'suitability_score', 'success_probability', 'sla_probability'
    ))


def get_candidate_ranking(task_id=None):
    if task_id is None:
        return []
    task = Task.objects.filter(task_id=task_id).first()
    if task is None:
        return []
    from workforce.services.ml_service import ml_service
    eligible = Employee.objects.filter(availability='AVAILABLE')
    candidates = []
    for employee in eligible:
        feature = __import__('workforce.services.feature_service', fromlist=['extract_features']).extract_features(employee, task)
        current = {'employee': employee, 'skill_match_score': feature['skill_match_score'], 'available_capacity_percent': max(100 - employee.current_workload_percent, 0)}
        candidates.append(current)
    candidates.sort(key=lambda item: item['skill_match_score'], reverse=True)
    return [
        {
            'employee_id': candidate['employee'].employee_id,
            'name': candidate['employee'].name,
            'skill_match_score': candidate['skill_match_score'],
            'available_capacity_percent': candidate['available_capacity_percent'],
            'current_workload_percent': candidate['employee'].current_workload_percent,
        }
        for candidate in candidates
    ]


def query_copilot(question):
    normalized = (question or '').strip().lower()
    if not normalized:
        return {'answer': "I don't have enough current workforce data to answer that."}

    if 'critical' in normalized and 'python' in normalized and 'take' in normalized:
        employees = Employee.objects.filter(availability='AVAILABLE')
        matched = [e for e in employees if 'Python' in (e.skills or [])]
        if not matched:
            return {'answer': "I don't have enough current workforce data to answer that."}
        ordered = sorted(matched, key=lambda e: (e.current_workload_percent, -e.historical_performance_score))
        best = ordered[0]
        return {
            'answer': f"{len(matched)} employees currently satisfy the availability and skill requirements. {best.name} has the lowest current workload among eligible employees and {max(matched, key=lambda e: e.historical_performance_score).name} has the highest historical performance among eligible candidates.",
        }

    if 'why was' in normalized and 'assigned' in normalized:
        for token in ['task ', 'task']:
            if token in normalized:
                task_id = normalized.split('task', 1)[1].strip().split()[0].upper()
                break
        else:
            task_id = None
        if task_id:
            task = Task.objects.filter(task_id__iexact=task_id).first()
            if task:
                decision = task.decision_records.order_by('-created_at').first()
                if decision:
                    return {'answer': f"{task.task_id} was assigned to {decision.employee.name} because they had the required skills, {decision.available_capacity_percent:.0f}% available capacity, and the highest suitability score among eligible employees."}
        return {'answer': "I don't have enough current workforce data to answer that."}

    if 'unavailable' in normalized and 'happen' in normalized:
        return {'answer': 'The allocation engine would re-evaluate the affected task against the remaining eligible employees while preserving the existing ML and OR-Tools decision flow.'}

    if 'high sla risk' in normalized or 'sla risk' in normalized:
        risks = get_sla_risks()
        high_risk = [item for item in risks if item['sla_risk_level'] in {'HIGH', 'CRITICAL'}]
        if not high_risk:
            return {'answer': 'There are no active high-risk SLA tasks in the current workforce data.'}
        first = high_risk[0]
        return {'answer': f"The current high-risk tasks include {first['task_id']} with {first['sla_risk_probability'] * 100:.0f}% risk and {first['priority']} priority."}

    if 'overloaded' in normalized:
        loaded = Employee.objects.filter(current_workload_percent__gt=80)
        if not loaded.exists():
            return {'answer': 'There are no overloaded employees in the current workforce data.'}
        names = ', '.join(e.name for e in loaded[:5])
        return {'answer': f"Currently overloaded employees include {names}."}

    if 'what changed' in normalized and 'task' in normalized:
        task_id = None
        for part in normalized.split():
            if part.startswith('t') and part[1:].isdigit():
                task_id = part.upper()
                break
        if task_id:
            history = get_decision_replay(task_id)
            if history:
                return {'answer': f"Task {task_id} has {len(history)} recorded decision updates. The latest decision was made by {history[-1]['employee']['name']} with suitability score {history[-1]['suitability_score']:.1f}."}
        return {'answer': "I don't have enough current workforce data to answer that."}

    if 'why was' in normalized and 'reallocated' in normalized:
        return {'answer': 'The system reallocates work when a current allocation is invalidated by real workforce events such as unavailability, critical-task pressure, or SLA risk, and it re-runs the existing ML and optimization logic before confirming a replacement assignment.'}

    return {'answer': "I don't have enough current workforce data to answer that."}
