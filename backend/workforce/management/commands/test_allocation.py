from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from workforce.models import Employee, Task
from workforce.services.allocation_service import AllocationService, pywraplp
from workforce.services.ml_service import ml_service


TEST_TASKS = [
    ('MODEL-T1', 'Machine Learning', 'Machine Learning', ['Python', 'Machine Learning'], 'CRITICAL'),
    ('MODEL-T2', 'Java Delivery', 'Software Development', ['Java', 'Spring Boot'], 'HIGH'),
    ('MODEL-T3', 'React Delivery', 'Software Development', ['React', 'JavaScript'], 'MEDIUM'),
    ('MODEL-T4', 'Cloud Delivery', 'Cloud/DevOps', ['AWS', 'Docker'], 'HIGH'),
    ('MODEL-T5', 'Security Review', 'Cybersecurity', ['Cybersecurity', 'Linux'], 'CRITICAL'),
]


class Command(BaseCommand):
    help = 'Run OR-Tools against real SQLite employees and temporary test tasks.'

    def handle(self, *args, **options):
        if not ml_service.models_loaded:
            raise CommandError('ML models are unavailable.')
        if pywraplp is None:
            raise CommandError('OR-Tools is unavailable.')

        employees = list(Employee.objects.filter(availability='AVAILABLE'))
        tasks = []
        for task_id, title, task_type, skills, priority in TEST_TASKS:
            tasks.append(Task.objects.create(
                task_id=task_id,
                title=title,
                description='Temporary allocation validation task.',
                task_type=task_type,
                required_skills=skills,
                priority=priority,
                estimated_effort_hours=3,
                sla_hours=24,
                remaining_sla_hours=24,
                deadline=timezone.now() + timezone.timedelta(days=1),
                location='Remote',
            ))

        try:
            candidates = {}
            for task in tasks:
                candidates[task.id] = [
                    result for result in ml_service.batch_predict(employees, task)
                    if result['skill_match_score'] >= AllocationService.MIN_SKILL_MATCH
                    and result['predicted_completion_hours'] <= task.sla_hours
                ]
            results = AllocationService.optimize_allocation(tasks, candidates)
            if not results or len(results) != len(tasks):
                raise CommandError('OR-Tools did not produce one valid assignment per test task.')
            self.stdout.write('Task -> Employee -> Suitability')
            for result in results:
                self.stdout.write(f"{result['task'].task_id} -> {result['employee'].employee_id} -> {result['metrics']['suitability_score']:.2f}")
        finally:
            Task.objects.filter(pk__in=[task.pk for task in tasks]).delete()
