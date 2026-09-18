import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from workforce.models import Employee, Task, Assignment

class Command(BaseCommand):
    help = 'Seed the database with synthetic employee and task data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing existing data...')
        Assignment.objects.all().delete()
        Task.objects.all().delete()
        Employee.objects.all().delete()

        first_names = ['Arun', 'Priya', 'Rahul', 'Sneha', 'Vikram', 'Anjali', 'Karthik', 'Neha', 'Suresh', 'Kavita',
                       'Ravi', 'Pooja', 'Amit', 'Divya', 'Sanjay', 'Ritu', 'Manish', 'Anita', 'Sunil', 'Kiran']
        last_names = ['Kumar', 'Sharma', 'Patel', 'Singh', 'Reddy', 'Rao', 'Gupta', 'Desai', 'Joshi', 'Nair']
        departments = ['Engineering', 'Data Science', 'DevOps', 'QA']
        locations = ['Bangalore', 'Hyderabad', 'Pune', 'Remote', 'Chennai']
        all_skills = ['Python', 'Machine Learning', 'SQL', 'React', 'Django', 'AWS', 'Docker', 'Kubernetes', 'Java', 'C++']

        self.stdout.write('Creating employees...')
        employees = []
        for i in range(1, 41):
            emp = Employee.objects.create(
                employee_id=f'E{i:03d}',
                name=f"{random.choice(first_names)} {random.choice(last_names)}",
                email=f"employee{i}@example.com",
                department=random.choice(departments),
                skills=random.sample(all_skills, k=random.randint(2, 5)),
                experience_years=round(random.uniform(1.0, 15.0), 1),
                current_workload_percent=random.randint(10, 80),
                availability='AVAILABLE' if random.random() > 0.1 else 'UNAVAILABLE',
                location=random.choice(locations),
                historical_performance_score=round(random.uniform(6.0, 10.0), 1),
                similar_tasks_completed=random.randint(5, 50),
                similar_tasks_success_rate=round(random.uniform(0.7, 1.0), 2)
            )
            employees.append(emp)

        self.stdout.write('Creating tasks...')
        tasks = []
        for i in range(1, 26):
            priority = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
            task = Task.objects.create(
                task_id=f'T{i:03d}',
                title=f"Project Task {i}",
                description="Synthetic task description for testing purposes.",
                task_type=random.choice(['Backend Development', 'Machine Learning', 'Frontend UI', 'Infrastructure']),
                required_skills=random.sample(all_skills, k=random.randint(1, 3)),
                priority=priority,
                estimated_effort_hours=random.randint(4, 40),
                sla_hours=random.randint(24, 120),
                remaining_sla_hours=random.randint(12, 100),
                deadline=timezone.now() + timezone.timedelta(days=random.randint(1, 14)),
                location=random.choice(locations),
                status='PENDING'
            )
            tasks.append(task)

        self.stdout.write(self.style.SUCCESS('Successfully seeded data.'))
