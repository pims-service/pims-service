from django.urls import path
from .views import ExportDataCSVView, AdminDashboardAnalyticsView, ExportBaselineDataCSVView

urlpatterns = [
    path('export/csv/', ExportDataCSVView.as_view(), name='export_csv'),
    path('export/baselines/csv/', ExportBaselineDataCSVView.as_view(), name='export_baseline_csv'),
    path('dashboard-analytics/', AdminDashboardAnalyticsView.as_view(), name='dashboard_analytics'),
]
