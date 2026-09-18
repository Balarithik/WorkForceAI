from django.core.management.base import BaseCommand
from workforce.models import Task


class Command(BaseCommand):
    help = 'Repair tasks marked ASSIGNED without an ACTIVE assignment, preserving assignment history.'

    def handle(self, *args, **options):
        repaired = 0
        for task in Task.objects.filter(status='ASSIGNED'):
            if not task.assignments.filter(status='ACTIVE').exists():
                task.status = 'PENDING'
                task.save(update_fields=['status', 'updated_at'])
                repaired += 1
                self.stdout.write(f'Repaired {task.task_id}: ASSIGNED -> PENDING')
        self.stdout.write(self.style.SUCCESS(f'Consistency repair complete: {repaired} task(s) repaired.'))
