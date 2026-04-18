from django.urls import path
from .views import ExportDataCSVView, AdminDashboardAnalyticsView

urlpatterns = [
    path('export/csv/', ExportDataCSVView.as_view(), name='export_csv'),
    path('dashboard-analytics/', AdminDashboardAnalyticsView.as_view(), name='dashboard_analytics'),
]
