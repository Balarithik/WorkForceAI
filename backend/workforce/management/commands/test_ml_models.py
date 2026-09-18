from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from workforce.models import Employee, Task
from workforce.services.feature_service import extract_features
from workforce.services.ml_service import ml_service


class Command(BaseCommand):
    help = 'Run all serialized ML models against one real employee and a test task.'

    def handle(self, *args, **options):
        if not ml_service.models_loaded:
            raise CommandError('ML models could not be loaded in this runtime.')

        employee = Employee.objects.filter(availability='AVAILABLE').first()
        if employee is None:
            raise CommandError('No available employee exists in SQLite.')

        task = Task(
            task_id='MODEL-CHECK',
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
        features = extract_features(employee, task)
        missing = [name for name in ('task_type', 'task_priority', 'experience_years', 'skill_match_score', 'employee_workload_percent', 'employee_availability', 'employee_performance_score', 'employee_location', 'task_location', 'distance_km', 'similar_tasks_completed', 'similar_tasks_success_rate', 'estimated_effort_hours', 'sla_hours', 'remaining_sla_hours', 'workload_capacity', 'availability_score', 'location_compatibility', 'experience_performance_score', 'sla_urgency_ratio', 'workload_effort_ratio', 'required_skill_count') if name not in features]
        if missing:
            raise CommandError(f'Missing generated features: {missing}')

        result = ml_service.predict_employee_task(employee, task)
        if not 0 <= result['success_probability'] <= 1 or not 0 <= result['sla_probability'] <= 1 or result['predicted_completion_hours'] <= 0 or not 0 <= result['suitability_score'] <= 100:
            raise CommandError(f'Invalid prediction result: {result}')

        self.stdout.write('========================================')
        self.stdout.write('AI MODEL TEST')
        self.stdout.write(f'Employee: {employee.employee_id} - {employee.name}')
        self.stdout.write(f'Task: {task.title}')
        self.stdout.write(f'SUCCESS MODEL: {result["success_probability"] * 100:.2f}%')
        self.stdout.write(f'SLA MODEL: {result["sla_probability"] * 100:.2f}%')
        self.stdout.write(f'COMPLETION MODEL: {result["predicted_completion_hours"]:.2f} hours')
        self.stdout.write(f'SUITABILITY: {result["suitability_score"]:.2f} / 100')
        self.stdout.write('========================================')
        self.stdout.write(self.style.SUCCESS('All models working successfully.'))
