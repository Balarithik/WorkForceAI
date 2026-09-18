from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Employee, Task, Assignment, Event, Notification, AllocationDecision, TaskOutcome
from .serializers import EmployeeSerializer, TaskSerializer, AssignmentSerializer, EventSerializer, NotificationSerializer, AllocationDecisionSerializer, TaskOutcomeSerializer
from .services.ml_service import ml_service
from .services.feature_service import extract_features
from .services.allocation_service import AllocationService
from .services.reallocation_service import ReallocationService
from .services.allocation_service import pywraplp
from .services.workload_service import recalculate_employee_workload
from .services.explanation_service import generate_employee_explanation
from .services.sla_risk_service import calculate_sla_risk, get_sla_risks
from .services.notification_service import create_notification, get_notifications, mark_notification_read, mark_all_notifications_read
from .services.decision_service import record_decision, get_task_decision_history
from .services.outcome_service import record_task_outcome, export_training_data, calculate_prediction_metrics

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
            risk = calculate_sla_risk(p['sla_probability'])
            explanation = generate_employee_explanation(employee, task, p)
            response_data.append({
                'employee': serialize_employee(employee),
                'employee_id': employee.employee_id,
                'name': employee.name,
                'current_workload_percent': employee.current_workload_percent,
                'available_capacity_percent': p['available_capacity_percent'],
                'skill_match_score': p['skill_match_score'],
                'success_probability': p['success_probability'],
                'sla_probability': p['sla_probability'],
                'sla_risk_probability': risk['sla_risk_probability'],
                'sla_risk_level': risk['sla_risk_level'],
                'predicted_completion_hours': p['predicted_completion_hours'],
                'time_score': p['time_score'],
                'suitability_score': p['suitability_score'],
                'score_breakdown': p['score_breakdown'],
                'explanation': explanation,
            })

        recommended = predictions[0]['employee'] if predictions else None
        recommended_prediction = predictions[0] if predictions else None
        risk = calculate_sla_risk(recommended_prediction['sla_probability']) if recommended_prediction else {'sla_probability': 0, 'sla_risk_probability': 0, 'sla_risk_level': 'LOW'}
        return Response({
            'candidates': response_data,
            'recommended_employee': serialize_employee(recommended) if recommended else None,
            'prediction': {
                key: recommended_prediction[key]
                for key in ('success_probability', 'sla_probability', 'predicted_completion_hours', 'suitability_score')
            } if recommended_prediction else None,
            'sla_risk_probability': risk['sla_risk_probability'],
            'sla_risk_level': risk['sla_risk_level'],
            'explanation': generate_employee_explanation(recommended, task, recommended_prediction) if recommended_prediction else None,
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
            assignment = Assignment.objects.create(
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
            event = Event.objects.create(
                event_type='NEW_TASK', task=task, employee=emp,
                description=f"New task '{task.title}' assigned to {emp.name}."
            )
            risk = calculate_sla_risk(metrics['sla_probability'])
            explanation = generate_employee_explanation(emp, task, {
                'skill_match_score': metrics.get('skill_match_score', 0),
                'available_capacity_percent': max(100 - emp.current_workload_percent, 0),
                'current_workload_percent': emp.current_workload_percent,
                'success_probability': metrics['success_probability'],
                'sla_probability': metrics['sla_probability'],
                'predicted_completion_hours': metrics['predicted_completion_hours'],
                'time_score': metrics.get('time_score', 0),
                'suitability_score': metrics['suitability_score'],
                'experience_years': emp.experience_years,
                'historical_performance_score': emp.historical_performance_score,
            })
            record_decision(
                task=task,
                employee=emp,
                assignment=assignment,
                trigger_type='INITIAL_ASSIGNMENT',
                candidate_rank=1,
                score_breakdown=metrics.get('score_breakdown', {}),
                decision_reason=explanation['summary'],
                allocation_status='ACTIVE',
                decision_context={'task_id': task.task_id, 'employee_id': emp.employee_id},
                metrics={
                    'success_probability': metrics['success_probability'],
                    'sla_probability': metrics['sla_probability'],
                    'predicted_completion_hours': metrics['predicted_completion_hours'],
                    'skill_match_score': metrics.get('skill_match_score', 0),
                    'current_workload_percent': emp.current_workload_percent,
                    'available_capacity_percent': max(100 - emp.current_workload_percent, 0),
                    'suitability_score': metrics['suitability_score'],
                }
            )
            if risk['sla_risk_level'] in {'HIGH', 'CRITICAL'}:
                create_notification(
                    'SLA_RISK',
                    f'SLA risk detected for Task {task.task_id}.',
                    f"SLA risk for task {task.task_id} is {risk['sla_risk_level']} with risk probability {(risk['sla_risk_probability'] * 100):.1f}%.",
                    'HIGH' if risk['sla_risk_level'] == 'HIGH' else 'CRITICAL',
                    employee=emp,
                    task=task,
                    event=event,
                )

        return Response({
            'task_id': task.task_id,
            'assigned_employee': {
                'employee_id': emp.employee_id,
                'name': emp.name,
            },
            'success_probability': metrics['success_probability'],
            'sla_probability': metrics['sla_probability'],
            'sla_risk_probability': risk['sla_risk_probability'],
            'sla_risk_level': risk['sla_risk_level'],
            'predicted_completion_hours': metrics['predicted_completion_hours'],
            'time_score': metrics.get('time_score', 0),
            'suitability_score': metrics['suitability_score'],
            'score_breakdown': metrics.get('score_breakdown', {}),
            'status': 'recommended',
            'employee': EmployeeSerializer(emp).data,
            'workload': workload,
            'explanation': explanation,
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


@api_view(['GET'])
def sla_risks(request):
    return Response(get_sla_risks())


@api_view(['GET'])
def notifications(request):
    unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
    notifications_qs = get_notifications(unread_only=unread_only)
    return Response(NotificationSerializer(notifications_qs, many=True).data)


@api_view(['PATCH'])
def mark_notification_read(request, notification_id):
    notification = mark_notification_read(notification_id)
    if notification is None:
        return Response({'error': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(NotificationSerializer(notification).data)


@api_view(['POST'])
def mark_all_notifications_read(request):
    count = mark_all_notifications_read()
    return Response({'updated': count})


@api_view(['GET'])
def decisions(request):
    decisions_qs = AllocationDecision.objects.select_related('task', 'employee', 'assignment').all().order_by('-created_at')
    return Response(AllocationDecisionSerializer(decisions_qs, many=True).data)


@api_view(['GET'])
def task_decision_history(request, task_id):
    history = get_task_decision_history(task_id)
    return Response(AllocationDecisionSerializer(history, many=True).data)


@api_view(['GET'])
def task_outcomes(request):
    outcomes = TaskOutcome.objects.select_related('assignment__task', 'assignment__employee').all().order_by('-recorded_at')
    return Response(TaskOutcomeSerializer(outcomes, many=True).data)


@api_view(['GET'])
def export_training_data_api(request):
    path = export_training_data(output_path='training_data.csv')
    return Response({'path': path, 'count': TaskOutcome.objects.count()})
