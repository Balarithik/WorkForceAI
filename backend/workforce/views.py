from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Employee, Task, Assignment, Event
from .serializers import EmployeeSerializer, TaskSerializer, AssignmentSerializer, EventSerializer
from .services.ml_service import ml_service
from .services.feature_service import extract_features
from .services.allocation_service import AllocationService
from .services.reallocation_service import ReallocationService

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    
    def perform_update(self, serializer):
        old_instance = self.get_object()
        new_instance = serializer.save()
        
        if old_instance.availability == 'AVAILABLE' and new_instance.availability == 'UNAVAILABLE':
            ReallocationService.handle_employee_unavailable(new_instance)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

@api_view(['GET'])
def dashboard_stats(request):
    total_employees = Employee.objects.count()
    available_employees = Employee.objects.filter(availability='AVAILABLE').count()
    active_tasks = Task.objects.filter(status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS']).count()
    critical_tasks = Task.objects.filter(priority='CRITICAL', status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS']).count()
    unassigned_tasks = Task.objects.filter(status='PENDING').count()
    
    employees = Employee.objects.all()
    avg_workload = sum([e.current_workload_percent for e in employees]) / max(total_employees, 1)
    
    return Response({
        'total_employees': total_employees,
        'available_employees': available_employees,
        'active_tasks': active_tasks,
        'critical_tasks': critical_tasks,
        'unassigned_tasks': unassigned_tasks,
        'average_workload': round(avg_workload, 2)
    })

@api_view(['POST'])
def predict_allocation(request):
    try:
        task_data = request.data
        task = Task(**task_data)

        eligible_employees = Employee.objects.filter(availability='AVAILABLE')
        if not eligible_employees.exists():
            return Response({'error': 'No available employees found.'}, status=status.HTTP_404_NOT_FOUND)

        if not ml_service.models_loaded:
            return Response({'error': 'ML prediction failed', 'detail': 'ML models are not available.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        predictions = ml_service.batch_predict(eligible_employees, task)
        predictions.sort(key=lambda x: x['suitability_score'], reverse=True)

        response_data = []
        for p in predictions:
            response_data.append({
                'employee_id': p['employee'].employee_id,
                'name': p['employee'].name,
                'current_workload_percent': p['employee'].current_workload_percent,
                'skill_match_score': extract_features(p['employee'], task)['skill_match_score'],
                'success_probability': p['success_probability'],
                'sla_probability': p['sla_probability'],
                'predicted_completion_hours': p['predicted_completion_hours'],
                'suitability_score': p['suitability_score'],
            })

        return Response({'candidates': response_data})
    except Exception as exc:
        return Response({'error': 'ML prediction failed', 'detail': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def assign_task(request):
    try:
        task_data = request.data
        task_serializer = TaskSerializer(data=task_data)

        if not task_serializer.is_valid():
            return Response(task_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        task = task_serializer.save()

        eligible_employees = Employee.objects.filter(availability='AVAILABLE')
        if not eligible_employees.exists():
            return Response({'error': 'No available employee was found for this task.'}, status=status.HTTP_404_NOT_FOUND)

        if not ml_service.models_loaded:
            return Response({'error': 'ML prediction failed', 'detail': 'ML models are not available.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        predictions = ml_service.batch_predict(eligible_employees, task)

        if not predictions:
            return Response({'error': 'ML prediction failed', 'detail': 'Could not generate predictions.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        candidates_matrix = {task.id: predictions}
        optimization_results = AllocationService.optimize_allocation([task], candidates_matrix)

        if not optimization_results:
            return Response({'error': 'Allocation failed', 'detail': 'Optimization failed to find an assignment.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

        task.status = 'ASSIGNED'
        task.save()

        Event.objects.create(
            event_type='NEW_TASK',
            task=task,
            employee=emp,
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
            'suitability_score': metrics['suitability_score'],
            'status': 'recommended',
        })
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
