from django.test import TestCase
from unittest.mock import patch
from workforce.models import Employee, Task, Assignment
from workforce.services.reallocation_service import ReallocationService
from workforce.services.workload_service import recalculate_employee_workload

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

    def test_assigned_task_has_active_assignment(self):
        Assignment.objects.create(
            task=self.task1, employee=self.emp1, success_probability=0.9,
            sla_probability=0.9, predicted_completion_hours=5, suitability_score=90.0,
            status='ACTIVE'
        )
        self.task1.status = 'ASSIGNED'
        self.task1.save()
        self.assertTrue(self.task1.assignments.filter(status='ACTIVE').exists())

    @patch('workforce.views.ml_service.models_loaded', False)
    def test_assignment_does_not_persist_when_ml_unavailable(self):
        from rest_framework.test import APIClient

        response = APIClient().post('/api/allocation/assign/', {
            'task_id': 'ML-DOWN', 'title': 'ML unavailable task', 'description': '',
            'task_type': 'Machine Learning', 'required_skills': ['Python'],
            'priority': 'HIGH', 'estimated_effort_hours': 2, 'sla_hours': 8,
            'remaining_sla_hours': 8, 'deadline': '2026-09-30T10:00:00Z', 'location': 'Remote',
        }, format='json')
        self.assertEqual(response.status_code, 503)
        self.assertFalse(Task.objects.filter(task_id='ML-DOWN').exists())

    def test_assignment_updates_employee_workload_and_completion_releases_it(self):
        self.emp1.baseline_workload_percent = 30
        self.emp1.save(update_fields=['baseline_workload_percent'])
        Assignment.objects.create(
            task=self.task1, employee=self.emp1, success_probability=0.9,
            sla_probability=0.9, predicted_completion_hours=5, suitability_score=90.0,
            status='ACTIVE'
        )
        workload = recalculate_employee_workload(self.emp1)
        self.emp1.refresh_from_db()
        self.assertEqual(workload['new'], 55)
        self.assertEqual(workload['capacity'], 45)

        self.task1.status = 'COMPLETED'
        self.task1.save(update_fields=['status', 'updated_at'])
        assignment = self.task1.assignments.get()
        assignment.status = 'COMPLETED'
        assignment.save(update_fields=['status'])
        recalculate_employee_workload(self.emp1)
        self.emp1.refresh_from_db()
        self.assertEqual(self.emp1.current_workload_percent, 30)

    def test_cancellation_reduces_workload(self):
        self.emp1.baseline_workload_percent = 30
        self.emp1.save(update_fields=['baseline_workload_percent'])
        Assignment.objects.create(
            task=self.task1, employee=self.emp1, success_probability=0.9,
            sla_probability=0.9, predicted_completion_hours=5, suitability_score=90.0,
            status='ACTIVE'
        )
        recalculate_employee_workload(self.emp1)
        assignment = self.task1.assignments.get()
        assignment.status = 'CANCELLED'
        assignment.save(update_fields=['status'])
        recalculate_employee_workload(self.emp1)
        self.emp1.refresh_from_db()
        self.assertEqual(self.emp1.current_workload_percent, 30)

    def test_reassignment_updates_both_employees(self):
        emp2 = Employee.objects.create(
            employee_id='E002', name='Test Emp 2', department='Engineering', email='t2@example.com',
            skills=['Python'], experience_years=5, current_workload_percent=20,
            baseline_workload_percent=20, availability='AVAILABLE', location='Remote'
        )
        self.emp1.baseline_workload_percent = 30
        self.emp1.save(update_fields=['baseline_workload_percent'])
        old_assignment = Assignment.objects.create(
            task=self.task1, employee=self.emp1, success_probability=0.9,
            sla_probability=0.9, predicted_completion_hours=5, suitability_score=90.0,
            status='ACTIVE'
        )
        recalculate_employee_workload(self.emp1)
        old_assignment.status = 'REALLOCATED'
        old_assignment.save(update_fields=['status'])
        Assignment.objects.create(
            task=self.task1, employee=emp2, success_probability=0.9,
            sla_probability=0.9, predicted_completion_hours=5, suitability_score=90.0,
            status='ACTIVE'
        )
        recalculate_employee_workload(self.emp1)
        recalculate_employee_workload(emp2)
        self.emp1.refresh_from_db()
        emp2.refresh_from_db()
        self.assertEqual(self.emp1.current_workload_percent, 30)
        self.assertEqual(emp2.current_workload_percent, 45)
