from django.core.management.base import BaseCommand, CommandError
from workforce.models import Assignment, Employee, Event
from workforce.services.reallocation_service import ReallocationService
from workforce.services.ml_service import ml_service
from workforce.services.allocation_service import pywraplp


class Command(BaseCommand):
    help = 'Exercise dynamic reallocation with a real active SQLite assignment and restore its state.'

    def handle(self, *args, **options):
        if not ml_service.models_loaded:
            raise CommandError('ML models are unavailable.')
        if pywraplp is None:
            raise CommandError('OR-Tools is unavailable.')

        assignment = Assignment.objects.filter(status='ACTIVE').select_related('employee', 'task').first()
        if assignment is None:
            raise CommandError('No active assignment exists for reallocation validation.')

        employee = assignment.employee
        task = assignment.task
        original_availability = employee.availability
        original_assignments = {
            item.id: (item.status, item.completed_at)
            for item in Assignment.objects.filter(employee=employee)
        }
        original_task_statuses = {
            item.task_id: item.task.status
            for item in Assignment.objects.filter(employee=employee).select_related('task')
        }
        event_ids_before = set(Event.objects.values_list('id', flat=True))
        replacement_ids_before = set(Assignment.objects.values_list('id', flat=True))

        self.stdout.write(f'BEFORE: {task.task_id} -> {employee.employee_id} ({employee.name})')
        try:
            employee.availability = 'UNAVAILABLE'
            employee.save(update_fields=['availability', 'updated_at'])
            self.stdout.write(f'EVENT: {employee.employee_id} became unavailable')
            ReallocationService.handle_employee_unavailable(employee)
            replacement = Assignment.objects.filter(task=task, status='ACTIVE').exclude(employee=employee).select_related('employee').first()
            if replacement is None:
                raise CommandError('No replacement assignment was created.')
            self.stdout.write(f'AFTER: {task.task_id} -> {replacement.employee.employee_id} ({replacement.employee.name})')
            self.stdout.write(f'New suitability: {replacement.suitability_score:.2f}')
        finally:
            Assignment.objects.exclude(id__in=replacement_ids_before).delete()
            for assignment_id, (original_status, original_completed_at) in original_assignments.items():
                Assignment.objects.filter(id=assignment_id).update(status=original_status, completed_at=original_completed_at)
            for task_id, original_status in original_task_statuses.items():
                from workforce.models import Task
                Task.objects.filter(id=task_id).update(status=original_status)
            employee.availability = original_availability
            employee.save(update_fields=['availability', 'updated_at'])
            Event.objects.exclude(id__in=event_ids_before).delete()
