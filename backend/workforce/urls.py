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
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('allocation/predict/', views.predict_allocation, name='predict-allocation'),
    path('allocation/assign/', views.assign_task, name='assign-task'),
    path('allocation/reallocate/', views.reallocate_task, name='reallocate-task'),
]
