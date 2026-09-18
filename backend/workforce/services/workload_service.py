import os

from django.db import transaction
from django.utils import timezone

from workforce.models import Assignment, Employee, Event

STANDARD_WORK_HOURS_PER_PERIOD = float(os.getenv('STANDARD_WORK_HOURS_PER_PERIOD', '40'))


def active_assignment_hours(employee):
    return sum(
        assignment.task.estimated_effort_hours
        for assignment in Assignment.objects.filter(employee=employee, status='ACTIVE').select_related('task')
    )


def recalculate_employee_workload(employee, create_event=False):
    """Persist workload as baseline workload plus all active assignment effort."""
    active_hours = active_assignment_hours(employee)
    baseline = employee.baseline_workload_percent
    if baseline is None:
        baseline = max(employee.current_workload_percent - active_hours / STANDARD_WORK_HOURS_PER_PERIOD * 100, 0)
        employee.baseline_workload_percent = round(baseline, 2)

    previous = employee.current_workload_percent
    calculated = baseline + active_hours / STANDARD_WORK_HOURS_PER_PERIOD * 100
    employee.current_workload_percent = min(round(calculated), 100)
    employee.save(update_fields=['baseline_workload_percent', 'current_workload_percent', 'updated_at'])

    if create_event and previous != employee.current_workload_percent:
        Event.objects.create(
            event_type='WORKLOAD_CHANGED',
            employee=employee,
            description=(
                f'{employee.name} workload changed from {previous}% to '
                f'{employee.current_workload_percent}%.'
            ),
        )
    return {
        'previous': previous,
        'new': employee.current_workload_percent,
        'capacity': max(100 - employee.current_workload_percent, 0),
        'active_assignment_hours': active_hours,
    }


def recalculate_employees(*employees):
    return [recalculate_employee_workload(employee) for employee in employees]
