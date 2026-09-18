from workforce.models import Employee, Task, Assignment


def get_workforce_twin_summary():
    employees = list(Employee.objects.all().order_by('department', 'name'))
    total = len(employees)
    available = sum(1 for employee in employees if employee.availability == 'AVAILABLE')
    avg_workload = round(sum(employee.current_workload_percent for employee in employees) / total, 2) if total else 0
    overloaded = [employee for employee in employees if employee.current_workload_percent > 80]
    critical = [employee for employee in employees if employee.current_workload_percent >= 90]
    sla_risk_tasks = sum(1 for task in Task.objects.filter(status__in=['PENDING', 'ASSIGNED', 'IN_PROGRESS']) if task.assignments.filter(status='ACTIVE').exists())
    unassigned_tasks = Task.objects.filter(status='PENDING').count()

    nodes = []
    for employee in employees:
        workload_state = 'LOW'
        if employee.current_workload_percent >= 90:
            workload_state = 'CRITICAL'
        elif employee.current_workload_percent >= 70:
            workload_state = 'HIGH'
        elif employee.current_workload_percent >= 40:
            workload_state = 'NORMAL'
        nodes.append({
            'id': employee.id,
            'employee_id': employee.employee_id,
            'name': employee.name,
            'department': employee.department,
            'location': employee.location,
            'skills': employee.skills,
            'workload_percent': employee.current_workload_percent,
            'available_capacity_percent': max(100 - employee.current_workload_percent, 0),
            'availability': employee.availability,
            'active_tasks': Assignment.objects.filter(employee=employee, status='ACTIVE').count(),
            'performance': employee.historical_performance_score,
            'workload_state': workload_state,
        })

    return {
        'total_employees': total,
        'available_employees': available,
        'average_workload': avg_workload,
        'overloaded_employees': len(overloaded),
        'critical_workload_employees': len(critical),
        'sla_risk_tasks': sla_risk_tasks,
        'unassigned_tasks': unassigned_tasks,
        'employees': nodes,
    }
