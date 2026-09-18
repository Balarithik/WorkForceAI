from django.core.management.base import BaseCommand
from workforce.models import Employee


DEPARTMENTS = [
    'Software Development', 'AI/ML', 'Data Engineering', 'QA/Testing',
    'Cloud/DevOps', 'Cybersecurity', 'Database', 'Support',
]
LOCATIONS = ['Chennai', 'Coimbatore', 'Bangalore', 'Hyderabad', 'Pune', 'Mumbai', 'Delhi']
FIRST_NAMES = ['Arun', 'Meera', 'Kiran', 'Nisha', 'Vikram', 'Ananya', 'Rohan', 'Isha', 'Dev', 'Priya']
LAST_NAMES = ['Kumar', 'Shah', 'Rao', 'Nair', 'Patel', 'Iyer', 'Singh', 'Menon', 'Das', 'Joshi']
SKILLS = [
    'Python', 'Java', 'JavaScript', 'React', 'Node.js', 'SQL', 'Machine Learning',
    'Deep Learning', 'TensorFlow', 'PyTorch', 'AWS', 'Azure', 'Docker', 'Kubernetes',
    'Linux', 'Spark', 'Power BI', 'Selenium', 'Cybersecurity', 'PostgreSQL',
    'MongoDB', 'Spring Boot', 'C++',
]


def profile(index):
    skill_start = (index * 3) % len(SKILLS)
    skills = [SKILLS[(skill_start + offset * 5) % len(SKILLS)] for offset in range(4)]
    availability = 'AVAILABLE' if index <= 40 else 'UNAVAILABLE' if index <= 45 else 'ON_LEAVE'
    return {
        'name': f'{FIRST_NAMES[(index - 1) % len(FIRST_NAMES)]} {LAST_NAMES[((index - 1) // len(FIRST_NAMES)) % len(LAST_NAMES)]}',
        'email': f'synthetic.employee{index:03d}@example.test',
        'department': DEPARTMENTS[(index - 1) % len(DEPARTMENTS)],
        'skills': skills,
        'experience_years': float(1 + ((index * 7) % 12)),
        'current_workload_percent': 10 + ((index * 13) % 81),
        'availability': availability,
        'location': LOCATIONS[(index - 1) % len(LOCATIONS)],
        'historical_performance_score': round(6.0 + ((index * 17) % 39) / 10, 1),
        'similar_tasks_completed': 5 + ((index * 11) % 46),
        'similar_tasks_success_rate': round(0.70 + ((index * 7) % 31) / 100, 2),
    }


class Command(BaseCommand):
    help = 'Create or update exactly 50 deterministic synthetic employee profiles.'

    def add_arguments(self, parser):
        parser.add_argument('--start-id', default='E001', help='Prefix followed by a three-digit employee number.')

    def handle(self, *args, **options):
        created = updated = skipped = 0
        start_id = options['start_id']
        prefix = ''.join(character for character in start_id if not character.isdigit()) or 'E'

        for index in range(1, 51):
            employee_id = f'{prefix}{index:03d}'
            employee, was_created = Employee.objects.update_or_create(
                employee_id=employee_id,
                defaults=profile(index),
            )
            if was_created:
                created += 1
            elif employee:
                updated += 1

        total = Employee.objects.count()
        self.stdout.write(f'Employees created: {created}')
        self.stdout.write(f'Employees updated: {updated}')
        self.stdout.write(f'Employees skipped: {skipped}')
        self.stdout.write(f'Total employees: {total}')
        if total != 50:
            self.stdout.write(self.style.WARNING('Existing employee IDs outside the seeded range were preserved.'))
        else:
            self.stdout.write(self.style.SUCCESS('Employee seed complete: database contains exactly 50 employees.'))
