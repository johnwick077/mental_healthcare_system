from django.urls import path
from .views import (
    DailyObservationReportView, WeeklyObservationReportView, MonthlyObservationReportView,
    PatientProgressReportView, InventoryReportView, ResourceUsageReportView
)

app_name = 'reports'

urlpatterns = [
    path('daily/', DailyObservationReportView.as_view(), name='daily_report'),
    path('weekly/', WeeklyObservationReportView.as_view(), name='weekly_report'),
    path('monthly/', MonthlyObservationReportView.as_view(), name='monthly_report'),
    path('patient/<int:patient_id>/progress/', PatientProgressReportView.as_view(), name='patient_progress_report'),
    path('inventory/', InventoryReportView.as_view(), name='inventory_report'),
    path('resource-usage/', ResourceUsageReportView.as_view(), name='resource_usage_report'),
]