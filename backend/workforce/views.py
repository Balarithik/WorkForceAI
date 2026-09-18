from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Employee, Task, Assignment, Event
from .serializers import EmployeeSerializer, TaskSerializer, AssignmentSerializer, EventSerializer
from .services.ml_service import ml_service
from .services.feature_service import extract_features
from .services.allocation_service import AllocationService
from .services.reallocation_service import ReallocationService
from .services.allocation_service import pywraplp
from .services.workload_service import recalculate_employee_workload

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all().order_by('employee_id')
    serializer_class = EmployeeSerializer
    
    def perform_update(self, serializer):
        old_instance = self.get_object()
        new_instance = serializer.save()
        
        if old_instance.availability == 'AVAILABLE' and new_instance.availability == 'UNAVAILABLE':
            ReallocationService.handle_employee_unavailable(new_instance)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by('-created_at')
    serializer_class = TaskSerializer

    def perform_update(self, serializer):
        with transaction.atomic():
            task = self.get_object()
            previous_status = task.status
            updated_task = serializer.save()
            if previous_status != updated_task.status:
                active_assignments = Assignment.objects.filter(task=updated_task).select_related('employee')
                if updated_task.status in ('COMPLETED', 'CANCELLED'):
                    new_assignment_status = 'COMPLETED' if updated_task.status == 'COMPLETED' else 'CANCELLED'
                    for assignment in active_assignments.filter(status='ACTIVE'):
                        assignment.status = new_assignment_status
                        assignment.completed_at = timezone.now()
                        assignment.save(update_fields=['status', 'completed_at'])
                        recalculate_employee_workload(assignment.employee, create_event=True)

class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.select_related('employee', 'task').all().order_by('-assigned_at')
    serializer_class = AssignmentSerializer

    def perform_create(self, serializer):
        with transaction.atomic():
            task = serializer.validated_data['task']
            employee = serializer.validated_data['employee']
            if serializer.validated_data.get('status', 'ACTIVE') == 'ACTIVE':
                if task.status not in ('PENDING', 'ASSIGNED', 'IN_PROGRESS'):
                    raise serializers.ValidationError('Task cannot receive an active assignment in its current state.')
                if employee.availability != 'AVAILABLE':
                    raise serializers.ValidationError('Unavailable employees cannot receive assignments.')
                if Assignment.objects.filter(task=task, status='ACTIVE').exists():
                    raise serializers.ValidationError('Task already has an active assignment.')
            assignment = serializer.save()
            if assignment.status == 'ACTIVE':
                task.status = 'ASSIGNED'
                task.save(update_fields=['status', 'updated_at'])
            recalculate_employee_workload(employee, create_event=True)

    def perform_update(self, serializer):
        with transaction.atomic():
            previous = self.get_object()
            old_employee = previous.employee
            updated = serializer.save()
            recalculate_employee_workload(old_employee, create_event=True)
            if updated.employee_id != old_employee.id:
                recalculate_employee_workload(updated.employee, create_event=True)

    def perform_destroy(self, instance):
        employee = instance.employee
        with transaction.atomic():
            instance.delete()
            recalculate_employee_workload(employee, create_event=True)

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.select_related('employee', 'task').all().order_by('-created_at')
    serializer_class = EventSerializer


def serialize_employee(employee):
    return EmployeeSerializer(employee).data

@api_view(['GET'])
def dashboard_stats(request):
    total_employees = Employee.objects.count()
    available_employees = Employee.objects.filter(availability='AVAILABLE').count()
    active_tasks = Task.objects.filter(status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS']).count()
    critical_tasks = Task.objects.filter(priority='CRITICAL', status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS']).count()
    unassigned_tasks = Task.objects.filter(status='PENDING').count()
    
    employees = Employee.objects.all()
    avg_workload = sum(e.current_workload_percent for e in employees) / max(total_employees, 1)
    active_assignments = Assignment.objects.filter(status='ACTIVE').count()
    
    return Response({
        'total_employees': total_employees,
        'available_employees': available_employees,
        'active_tasks': active_tasks,
        'critical_tasks': critical_tasks,
        'unassigned_tasks': unassigned_tasks,
        'active_assignments': active_assignments,
        'average_workload': round(avg_workload, 2)
    })


@api_view(['GET'])
def health(request):
    try:
        Employee.objects.exists()
        database_status = 'ok'
    except Exception:
        database_status = 'error'
    ml_status = 'ok' if ml_service.models_loaded else 'error'
    ortools_status = 'ok' if pywraplp is not None else 'error'
    overall_status = 'ok' if database_status == 'ok' and ml_status == 'ok' and ortools_status == 'ok' else 'error'
    return Response({
        'status': overall_status,
        'database': database_status,
        'ml_models': ml_status,
        'ortools': ortools_status,
    }, status=status.HTTP_200_OK if overall_status == 'ok' else status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(['POST'])
def predict_allocation(request):
    try:
        task_data = request.data
        task = Task(**task_data)

        eligible_employees = [
            employee for employee in Employee.objects.filter(availability='AVAILABLE')
            if extract_features(employee, task)['skill_match_score'] >= AllocationService.MIN_SKILL_MATCH
            and AllocationService.effective_workload_hours(employee) + task.estimated_effort_hours
            <= AllocationService.MAX_WORKLOAD_PERCENT / 100 * AllocationService.HOURS_PER_WORKDAY
        ]
        if not eligible_employees:
            return Response({'error': 'No available employees found.'}, status=status.HTTP_404_NOT_FOUND)

        if not ml_service.models_loaded:
            return Response({'error': 'ML prediction failed', 'detail': 'ML models are not available.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        predictions = [
            prediction for prediction in ml_service.batch_predict(eligible_employees, task)
            if prediction['skill_match_score'] >= AllocationService.MIN_SKILL_MATCH
            and prediction['predicted_completion_hours'] <= task.sla_hours
        ]
        predictions.sort(key=lambda x: x['suitability_score'], reverse=True)

        response_data = []
        for p in predictions:
            employee = p['employee']
            response_data.append({
                'employee': serialize_employee(employee),
                'employee_id': employee.employee_id,
                'name': employee.name,
                'current_workload_percent': employee.current_workload_percent,
                'available_capacity_percent': p['available_capacity_percent'],
                'skill_match_score': p['skill_match_score'],
                'success_probability': p['success_probability'],
                'sla_probability': p['sla_probability'],
                'predicted_completion_hours': p['predicted_completion_hours'],
                'time_score': p['time_score'],
                'suitability_score': p['suitability_score'],
                'score_breakdown': p['score_breakdown'],
            })

        recommended = predictions[0]['employee'] if predictions else None
        return Response({
            'candidates': response_data,
            'recommended_employee': serialize_employee(recommended) if recommended else None,
            'prediction': {
                key: predictions[0][key]
                for key in ('success_probability', 'sla_probability', 'predicted_completion_hours', 'suitability_score')
            } if predictions else None,
        })
    except Exception as exc:
        return Response({'error': 'ML prediction failed', 'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def assign_task(request):
    try:
        task_data = request.data
        task_serializer = TaskSerializer(data=task_data)

        if not task_serializer.is_valid():
            return Response(task_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        eligible_employees = Employee.objects.filter(availability='AVAILABLE')
        if not eligible_employees.exists():
            return Response({'error': 'Assignment failed', 'detail': 'No suitable available employee found.'}, status=status.HTTP_409_CONFLICT)
        if not ml_service.models_loaded:
            return Response({'error': 'ML prediction failed', 'detail': 'ML models are not available.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        with transaction.atomic():
            task = task_serializer.save()
            requested_employee_id = task_data.get('employee_id')
            if requested_employee_id:
                eligible_employees = eligible_employees.filter(employee_id=requested_employee_id)
                if not eligible_employees.exists():
                    raise ValueError('The selected employee is unavailable or does not exist.')

            predictions = [
                prediction for prediction in ml_service.batch_predict(eligible_employees, task)
                if prediction['skill_match_score'] >= AllocationService.MIN_SKILL_MATCH
                and prediction['predicted_completion_hours'] <= task.sla_hours
            ]
            candidates_matrix = {task.id: predictions}
            optimization_results = AllocationService.optimize_allocation([task], candidates_matrix)
            if not optimization_results:
                raise ValueError('Optimization failed to find an assignment.')

            result = optimization_results[0]
            emp = result['employee']
            metrics = result['metrics']
            Assignment.objects.create(
                task=task,
                employee=emp,
                success_probability=metrics['success_probability'],
                sla_probability=metrics['sla_probability'],
                predicted_completion_hours=metrics['predicted_completion_hours'],
                suitability_score=metrics['suitability_score'],
                status='ACTIVE'
            )
            workload = recalculate_employee_workload(emp, create_event=True)
            task.status = 'ASSIGNED'
            task.save(update_fields=['status', 'updated_at'])
            Event.objects.create(
                event_type='NEW_TASK', task=task, employee=emp,
                description=f"New task '{task.title}' assigned to {emp.name}."
            )

        return Response({
            'task_id': task.task_id,
            'assigned_employee': {
                'employee_id': emp.employee_id,
                'name': emp.name,
            },
            'success_probability': metrics['success_probability'],
            'sla_probability': metrics['sla_probability'],
            'predicted_completion_hours': metrics['predicted_completion_hours'],
            'time_score': metrics['time_score'],
            'suitability_score': metrics['suitability_score'],
            'score_breakdown': metrics['score_breakdown'],
            'status': 'recommended',
            'employee': EmployeeSerializer(emp).data,
            'workload': workload,
        })
    except ValueError as exc:
        return Response({'error': 'Assignment failed', 'detail': str(exc)}, status=status.HTTP_409_CONFLICT)
    except Exception as exc:
        return Response({'error': 'Assignment failed', 'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def reallocate_task(request):
    task_id = request.data.get('task_id')
    try:
        task = Task.objects.get(task_id=task_id)
        ReallocationService.reallocate_task(task)
        return Response({'message': 'Reallocation triggered successfully.'})
    except Task.DoesNotExist:
        return Response({'error': 'Task not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as exc:
        return Response({'error': 'Reallocation failed', 'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
