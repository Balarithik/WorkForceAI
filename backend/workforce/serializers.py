from rest_framework import serializers
from .models import Employee, Task, Assignment, Event

class EmployeeSerializer(serializers.ModelSerializer):
    available_capacity_percent = serializers.SerializerMethodField()
    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ('available_capacity_percent',)

    def get_available_capacity_percent(self, employee):
        if employee.availability != 'AVAILABLE':
            return 0
        return max(100 - employee.current_workload_percent, 0)

    def validate_current_workload_percent(self, value):
        if not 0 <= value <= 100:
            raise serializers.ValidationError('Workload must be between 0 and 100.')
        return value

    def validate_experience_years(self, value):
        if value < 0:
            raise serializers.ValidationError('Experience cannot be negative.')
        return value

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

    def validate_estimated_effort_hours(self, value):
        if value <= 0:
            raise serializers.ValidationError('Estimated effort must be greater than zero.')
        return value

    def validate_sla_hours(self, value):
        if value <= 0:
            raise serializers.ValidationError('SLA hours must be greater than zero.')
        return value

    def validate_required_skills(self, value):
        if not isinstance(value, list) or not all(str(skill).strip() for skill in value):
            raise serializers.ValidationError('Required skills must be a non-empty list of names.')
        return [str(skill).strip() for skill in value]

class AssignmentSerializer(serializers.ModelSerializer):
    employee_details = EmployeeSerializer(source='employee', read_only=True)
    task_details = TaskSerializer(source='task', read_only=True)
    
    class Meta:
        model = Assignment
        fields = '__all__'

class EventSerializer(serializers.ModelSerializer):
    employee_details = EmployeeSerializer(source='employee', read_only=True)
    task_details = TaskSerializer(source='task', read_only=True)
    
    class Meta:
        model = Event
        fields = '__all__'
