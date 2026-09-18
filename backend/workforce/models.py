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
    job_title = models.CharField(max_length=150, blank=True, default='')
    phone_number = models.CharField(max_length=30, blank=True, default='')
    manager_name = models.CharField(max_length=150, blank=True, default='')
    team = models.CharField(max_length=100, blank=True, default='')
    preferred_shift = models.CharField(
        max_length=20,
        choices=[('DAY', 'Day'), ('EVENING', 'Evening'), ('NIGHT', 'Night'), ('FLEXIBLE', 'Flexible')],
        default='DAY',
        blank=True,
    )
    certifications = models.JSONField(default=list, blank=True)
    bio = models.TextField(blank=True, default='')
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
        ('SLA_RISK_HIGH', 'SLA Risk High'),
        ('NEW_CRITICAL_TASK', 'New Critical Task'),
        ('TASK_DELAYED', 'Task Delayed'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} at {self.created_at}"


class Notification(models.Model):
    SEVERITY_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    NOTIFICATION_TYPES = [
        ('SLA_RISK', 'SLA Risk'),
        ('EMPLOYEE_UNAVAILABLE', 'Employee Unavailable'),
        ('REALLOCATION', 'Reallocation'),
        ('HIGH_WORKLOAD', 'High Workload'),
        ('NEW_CRITICAL_TASK', 'New Critical Task'),
        ('TASK_ASSIGNED', 'Task Assigned'),
        ('TASK_COMPLETED', 'Task Completed'),
        ('MODEL_ALERT', 'Model Alert'),
    ]

    notification_type = models.CharField(max_length=40, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='INFO')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('notification_type', 'employee', 'task', 'event')

    def __str__(self):
        return f"{self.notification_type}: {self.title}"


class AllocationDecision(models.Model):
    TRIGGER_CHOICES = [
        ('INITIAL_ASSIGNMENT', 'Initial Assignment'),
        ('REALLOCATION', 'Reallocation'),
        ('MANUAL_RECOMMENDATION', 'Manual Recommendation'),
        ('SLA_RISK', 'SLA Risk'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('REALLOCATED', 'Reallocated'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='decision_records')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='decision_records')
    assignment = models.ForeignKey(Assignment, on_delete=models.SET_NULL, null=True, blank=True, related_name='decision_records')
    created_at = models.DateTimeField(auto_now_add=True)
    trigger_type = models.CharField(max_length=40, choices=TRIGGER_CHOICES, default='INITIAL_ASSIGNMENT')
    success_probability = models.FloatField(default=0.0)
    sla_probability = models.FloatField(default=0.0)
    predicted_completion_hours = models.FloatField(default=0.0)
    skill_match_score = models.FloatField(default=0.0)
    workload_percent = models.FloatField(default=0.0)
    available_capacity_percent = models.FloatField(default=0.0)
    suitability_score = models.FloatField(default=0.0)
    score_breakdown = models.JSONField(default=dict, blank=True)
    rank = models.IntegerField(default=1)
    decision_reason = models.TextField(blank=True)
    allocation_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    decision_context = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Decision: {self.task.task_id} -> {self.employee.employee_id}"


class TaskOutcome(models.Model):
    assignment = models.OneToOneField(Assignment, on_delete=models.CASCADE, related_name='outcome')
    predicted_success_probability = models.FloatField(default=0.0)
    predicted_sla_probability = models.FloatField(default=0.0)
    predicted_completion_hours = models.FloatField(default=0.0)
    actual_completion_hours = models.FloatField(null=True, blank=True)
    actual_sla_met = models.BooleanField(null=True, blank=True)
    actual_success = models.BooleanField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"Outcome for {self.assignment.task.task_id}"
