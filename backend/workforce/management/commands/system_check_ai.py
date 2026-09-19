from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

from workforce.models import Assignment, Employee, Event, Task
from workforce.services.allocation_service import pywraplp
from workforce.services.ml_service import ml_service


class Command(BaseCommand):
    help = 'Check database, models, ML runtime, OR-Tools, and deployment configuration.'

    def report(self, label, condition, detail=''):
        if condition:
            self.stdout.write(self.style.SUCCESS(f'[PASS] {label}'))
            return True
        self.stdout.write(self.style.ERROR(f'[FAIL] {label}{": " + detail if detail else ""}'))
        return False

    def handle(self, *args, **options):
        checks = []
        model_dir = settings.ML_MODEL_DIR
        model_paths = {
            'task_success_model.pkl': model_dir / 'task_success_model.pkl',
            'sla_model.pkl': model_dir / 'sla_model.pkl',
            'completion_time_model.pkl': model_dir / 'completion_time_model.pkl',
        }
        self.stdout.write(f'BASE_DIR: {settings.BASE_DIR}')
        self.stdout.write(f'ML_MODEL_DIR: {model_dir}')
        self.stdout.write(f'ML_MODEL_DIR exists: {model_dir.exists()}')
        for filename, path in model_paths.items():
            self.stdout.write(f'{filename} exists: {path.exists()}')
        self.stdout.write(f'task_success_model class: {type(ml_service.success_model).__name__}')
        self.stdout.write(f'sla_model class: {type(ml_service.sla_model).__name__}')
        self.stdout.write(f'completion_time_model class: {type(ml_service.completion_model).__name__}')
        try:
            connection.ensure_connection()
            checks.append(self.report('Database', True))
        except Exception as exc:
            checks.append(self.report('Database', False, str(exc)))

        table_names = connection.introspection.table_names()
        checks.extend([
            self.report('Employee table', Employee._meta.db_table in table_names),
            self.report('Task table', Task._meta.db_table in table_names),
            self.report('Assignment table', Assignment._meta.db_table in table_names),
            self.report('Event table', Event._meta.db_table in table_names),
            self.report('Success model', ml_service.success_model is not None),
            self.report('SLA model', ml_service.sla_model is not None),
            self.report('Completion model', ml_service.completion_model is not None),
            self.report('OR-Tools', pywraplp is not None),
            self.report('Static files', bool(getattr(settings, 'STATIC_ROOT', None))),
            self.report('Environment configuration', bool(settings.SECRET_KEY and settings.ALLOWED_HOSTS)),
        ])

        if ml_service.models_loaded:
            employee = Employee.objects.filter(availability='AVAILABLE').first()
            task = Task.objects.first()
            try:
                prediction = ml_service.predict_employee_task(employee, task)
                checks.append(self.report('ML prediction', employee is not None and task is not None and 0 <= prediction['suitability_score'] <= 100))
            except Exception as exc:
                checks.append(self.report('ML prediction', False, str(exc)))
        else:
            checks.append(self.report('ML prediction', False, 'Models could not be loaded in this runtime.'))

        self.stdout.write(f'AI system checks: {sum(checks)}/{len(checks)} passed')
        if not all(checks):
            raise SystemExit(1)
