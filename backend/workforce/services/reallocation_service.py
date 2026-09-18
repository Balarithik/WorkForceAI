from workforce.models import Task, Employee, Assignment, Event
from .ml_service import ml_service
from .allocation_service import AllocationService
from django.utils import timezone
from .workload_service import recalculate_employee_workload

class ReallocationService:
    @staticmethod
    def handle_employee_unavailable(employee):
        """
        Triggered when an employee becomes unavailable.
        Finds all active tasks and reallocates them.
        """
        Event.objects.create(
            event_type='EMPLOYEE_UNAVAILABLE',
            employee=employee,
            description=f"Employee {employee.name} became unavailable."
        )
        
        active_assignments = Assignment.objects.filter(employee=employee, status='ACTIVE')
        for assignment in active_assignments:
            task = assignment.task
            
            # Cancel current assignment
            assignment.status = 'REALLOCATED'
            assignment.completed_at = timezone.now()
            assignment.save()
            recalculate_employee_workload(employee, create_event=True)
            
            # Reallocate
            ReallocationService.reallocate_task(task, old_employee=employee)

    @staticmethod
    def reallocate_task(task, old_employee=None):
        # Find eligible employees
        eligible_employees = Employee.objects.filter(availability='AVAILABLE')
        if not eligible_employees.exists():
            Event.objects.create(
                event_type='REALLOCATION',
                task=task,
                description=f"Task {task.task_id} requires reallocation, but no available employees found."
            )
            return None
            
        # Run ML predictions
        predictions = ml_service.batch_predict(eligible_employees, task)
        
        if not predictions:
            return None
            
        # Use OR-Tools (single task optimization is trivial, but using service for consistency)
        candidates_matrix = {task.id: predictions}
        optimization_results = AllocationService.optimize_allocation([task], candidates_matrix)
        
        if optimization_results:
            result = optimization_results[0]
            new_emp = result["employee"]
            metrics = result["metrics"]
            
            # Create new assignment
            Assignment.objects.create(
                task=task,
                employee=new_emp,
                success_probability=metrics["success_probability"],
                sla_probability=metrics["sla_probability"],
                predicted_completion_hours=metrics["predicted_completion_hours"],
                suitability_score=metrics["suitability_score"],
                status='ACTIVE'
            )
            recalculate_employee_workload(new_emp, create_event=True)
            
            task.status = 'ASSIGNED'
            task.save()
            
            old_emp_str = f" from {old_employee.name}" if old_employee else ""
            Event.objects.create(
                event_type='REALLOCATION',
                task=task,
                employee=new_emp,
                description=f"Task {task.task_id} reallocated{old_emp_str} to {new_emp.name}."
            )
            
            return new_emp
        return None
