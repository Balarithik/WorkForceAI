from django.contrib import admin
from .models import Employee, Task, Assignment, Event

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'name', 'department', 'job_title', 'availability', 'current_workload_percent')
    list_filter = ('availability', 'department', 'preferred_shift')
    search_fields = ('employee_id', 'name', 'email', 'job_title', 'team', 'manager_name')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'title', 'priority', 'status', 'deadline')
    list_filter = ('status', 'priority', 'task_type')
    search_fields = ('task_id', 'title')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('task', 'employee', 'suitability_score', 'status', 'assigned_at')
    list_filter = ('status',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'employee', 'task', 'created_at')
    list_filter = ('event_type',)
