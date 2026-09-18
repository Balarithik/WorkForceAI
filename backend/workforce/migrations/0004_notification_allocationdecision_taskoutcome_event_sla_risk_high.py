from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workforce', '0003_employee_baseline_workload_percent'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='event_type',
            field=models.CharField(choices=[('NEW_TASK', 'New Task'), ('EMPLOYEE_UNAVAILABLE', 'Employee Unavailable'), ('EMPLOYEE_AVAILABLE', 'Employee Available'), ('TASK_COMPLETED', 'Task Completed'), ('PRIORITY_CHANGED', 'Priority Changed'), ('WORKLOAD_CHANGED', 'Workload Changed'), ('SLA_CHANGED', 'SLA Changed'), ('REALLOCATION', 'Reallocation'), ('SLA_RISK_HIGH', 'SLA Risk High'), ('NEW_CRITICAL_TASK', 'New Critical Task'), ('TASK_DELAYED', 'Task Delayed')], default='NEW_TASK', max_length=50),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('SLA_RISK', 'SLA Risk'), ('EMPLOYEE_UNAVAILABLE', 'Employee Unavailable'), ('REALLOCATION', 'Reallocation'), ('HIGH_WORKLOAD', 'High Workload'), ('NEW_CRITICAL_TASK', 'New Critical Task'), ('TASK_ASSIGNED', 'Task Assigned'), ('TASK_COMPLETED', 'Task Completed'), ('MODEL_ALERT', 'Model Alert')], max_length=40)),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('severity', models.CharField(choices=[('INFO', 'Info'), ('WARNING', 'Warning'), ('HIGH', 'High'), ('CRITICAL', 'Critical')], default='INFO', max_length=20)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='workforce.employee')),
                ('event', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='workforce.event')),
                ('task', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='workforce.task')),
            ],
            options={'ordering': ['-created_at'], 'unique_together': {('notification_type', 'employee', 'task', 'event')},},
        ),
        migrations.CreateModel(
            name='AllocationDecision',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('trigger_type', models.CharField(choices=[('INITIAL_ASSIGNMENT', 'Initial Assignment'), ('REALLOCATION', 'Reallocation'), ('MANUAL_RECOMMENDATION', 'Manual Recommendation'), ('SLA_RISK', 'SLA Risk')], default='INITIAL_ASSIGNMENT', max_length=40)),
                ('success_probability', models.FloatField(default=0.0)),
                ('sla_probability', models.FloatField(default=0.0)),
                ('predicted_completion_hours', models.FloatField(default=0.0)),
                ('skill_match_score', models.FloatField(default=0.0)),
                ('workload_percent', models.FloatField(default=0.0)),
                ('available_capacity_percent', models.FloatField(default=0.0)),
                ('suitability_score', models.FloatField(default=0.0)),
                ('score_breakdown', models.JSONField(blank=True, default=dict)),
                ('rank', models.IntegerField(default=1)),
                ('decision_reason', models.TextField(blank=True)),
                ('allocation_status', models.CharField(choices=[('ACTIVE', 'Active'), ('REALLOCATED', 'Reallocated'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], default='ACTIVE', max_length=20)),
                ('decision_context', models.JSONField(blank=True, default=dict)),
                ('assignment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='decision_records', to='workforce.assignment')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='decision_records', to='workforce.employee')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='decision_records', to='workforce.task')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='TaskOutcome',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('predicted_success_probability', models.FloatField(default=0.0)),
                ('predicted_sla_probability', models.FloatField(default=0.0)),
                ('predicted_completion_hours', models.FloatField(default=0.0)),
                ('actual_completion_hours', models.FloatField(blank=True, null=True)),
                ('actual_sla_met', models.BooleanField(blank=True, null=True)),
                ('actual_success', models.BooleanField(blank=True, null=True)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('assignment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='outcome', to='workforce.assignment')),
            ],
            options={'ordering': ['-recorded_at']},
        ),
    ]
