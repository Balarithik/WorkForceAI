from django.db import models

class Employee(models.Model):
    AVAILABILITY_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('UNAVAILABLE', 'Unavailable'),
        ('ON_LEAVE', 'On Leave'),
    ]

    employee_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)
    skills = models.JSONField(default=list)  # Using JSONField for skills
    experience_years = models.FloatField()
    current_workload_percent = models.IntegerField(default=0)
    baseline_workload_percent = models.FloatField(null=True, blank=True)
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='AVAILABLE')
    location = models.CharField(max_length=100)
    historical_performance_score = models.FloatField(default=0.0)
    similar_tasks_completed = models.IntegerField(default=0)
    similar_tasks_success_rate = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.employee_id})"


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    task_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    task_type = models.CharField(max_length=100)
    required_skills = models.JSONField(default=list)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    estimated_effort_hours = models.FloatField()
    sla_hours = models.FloatField()
    remaining_sla_hours = models.FloatField()
    deadline = models.DateTimeField()
    location = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Assignment(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('REALLOCATED', 'Reallocated'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='assignments')
    success_probability = models.FloatField()
    sla_probability = models.FloatField()
    predicted_completion_hours = models.FloatField()
    suitability_score = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.task.task_id} -> {self.employee.employee_id}"


class Event(models.Model):
    EVENT_TYPES = [
        ('NEW_TASK', 'New Task'),
        ('EMPLOYEE_UNAVAILABLE', 'Employee Unavailable'),
        ('EMPLOYEE_AVAILABLE', 'Employee Available'),
        ('TASK_COMPLETED', 'Task Completed'),
        ('PRIORITY_CHANGED', 'Priority Changed'),
        ('WORKLOAD_CHANGED', 'Workload Changed'),
        ('SLA_CHANGED', 'SLA Changed'),
        ('REALLOCATION', 'Reallocation'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} at {self.created_at}"
