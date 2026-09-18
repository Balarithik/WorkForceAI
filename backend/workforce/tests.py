from django.test import TestCase
from workforce.models import Employee, Task, Assignment
from workforce.services.reallocation_service import ReallocationService

class WorkforceTests(TestCase):
    def setUp(self):
        self.emp1 = Employee.objects.create(
            employee_id="E001", name="Test Emp 1", department="Engineering", email="t1@example.com",
            skills=["Python"], experience_years=5, current_workload_percent=30, availability='AVAILABLE',
            location="Remote"
        )
        self.task1 = Task.objects.create(
            task_id="T001", title="Test Task", task_type="Dev", required_skills=["Python"],
            priority="HIGH", estimated_effort_hours=10, sla_hours=24, remaining_sla_hours=24,
            deadline="2026-09-30T10:00:00Z", location="Remote", status="PENDING"
        )

    def test_employee_creation(self):
        self.assertEqual(Employee.objects.count(), 1)
        self.assertEqual(self.emp1.name, "Test Emp 1")

    def test_task_creation(self):
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(self.task1.status, "PENDING")

    def test_reallocation_triggers_when_unavailable(self):
        Assignment.objects.create(
            task=self.task1, employee=self.emp1, success_probability=0.9,
            sla_probability=0.9, predicted_completion_hours=5, suitability_score=90.0, status='ACTIVE'
        )
        self.task1.status = 'ASSIGNED'
        self.task1.save()
        
        # When employee becomes unavailable
        self.emp1.availability = 'UNAVAILABLE'
        self.emp1.save()
        
        # Manually trigger the service as the API view handles it in real code, 
        # but let's test the service method directly.
        ReallocationService.handle_employee_unavailable(self.emp1)
        
        # The assignment should be cancelled
        a = Assignment.objects.get(task=self.task1, employee=self.emp1)
        self.assertEqual(a.status, 'REALLOCATED')
