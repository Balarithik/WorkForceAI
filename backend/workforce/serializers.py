from rest_framework import serializers
from .models import Employee, Task, Assignment, Event

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'

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
