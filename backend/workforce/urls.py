from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'assignments', views.AssignmentViewSet)
router.register(r'events', views.EventViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.health, name='health'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('allocation/predict/', views.predict_allocation, name='predict-allocation'),
    path('allocation/assign/', views.assign_task, name='assign-task'),
    path('allocation/reallocate/', views.reallocate_task, name='reallocate-task'),
    path('sla-risks/', views.sla_risks, name='sla-risks'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark-notification-read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark-all-notifications-read'),
    path('decisions/', views.decisions, name='decisions'),
    path('tasks/<str:task_id>/decision-history/', views.task_decision_history, name='task-decision-history'),
    path('copilot/query/', views.copilot_query, name='copilot-query'),
    path('workforce-twin/', views.workforce_twin, name='workforce-twin'),
    path('outcomes/', views.task_outcomes, name='task-outcomes'),
    path('training/export/', views.export_training_data_api, name='export-training-data'),
]
