from django.urls import path
from .views import (
    ExportDataCSVView, 
    AdminDashboardAnalyticsView, 
    ExportBaselineDataCSVView,
    ExportPosttestDataCSVView,
    ExportTaskStatusView
)

urlpatterns = [
    path('export/csv/', ExportDataCSVView.as_view(), name='export_csv'),
    path('export/baselines/csv/', ExportBaselineDataCSVView.as_view(), name='export_baseline_csv'),
    path('export/posttests/csv/', ExportPosttestDataCSVView.as_view(), name='export_posttest_csv'),
    path('export/status/<uuid:task_id>/', ExportTaskStatusView.as_view(), name='export_task_status'),
    path('dashboard-analytics/', AdminDashboardAnalyticsView.as_view(), name='dashboard_analytics'),
]
