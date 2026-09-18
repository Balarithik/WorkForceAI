from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from workforce.models import Employee, Task
from workforce.services.ml_service import ml_service


class Command(BaseCommand):
    help = 'Rank all available SQLite employees for a real ML test task.'

    def handle(self, *args, **options):
        if not ml_service.models_loaded:
            raise CommandError('ML models could not be loaded in this runtime.')

        employees = list(Employee.objects.filter(availability='AVAILABLE'))
        if not employees:
            raise CommandError('No available employees exist in SQLite.')

        task = Task(
            task_id='RANKING-CHECK',
            title='Build ML Recommendation Engine',
            description='',
            task_type='Machine Learning',
            required_skills=['Python', 'Machine Learning', 'SQL'],
            priority='CRITICAL',
            estimated_effort_hours=8,
            sla_hours=24,
            remaining_sla_hours=24,
            deadline=timezone.now() + timezone.timedelta(days=1),
            location='Remote',
        )
        ranking = ml_service.batch_predict(employees, task)
        ranking.sort(key=lambda item: item['suitability_score'], reverse=True)
        self.stdout.write('Employee Success SLA Completion Suitability')
        for item in ranking[:10]:
            employee = item['employee']
            self.stdout.write(
                f'{employee.employee_id} {item["success_probability"] * 100:.1f}% '
                f'{item["sla_probability"] * 100:.1f}% '
                f'{item["predicted_completion_hours"]:.1f}h '
                f'{item["suitability_score"]:.1f}'
            )
