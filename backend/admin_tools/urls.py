from django.urls import path
from .views import (
    ExportDataCSVView, 
    AdminDashboardAnalyticsView, 
    ExportT0DataCSVView,
    ExportT1DataCSVView,
    ExportTFirstMonthDataCSVView,
    ExportT2DataCSVView,
    ExportT3DataCSVView,
    ExportT4DataCSVView,
    ExportLongitudinalDataCSVView,
    ExportDailyEntriesDataCSVView,
    ExportTaskStatusView
)

urlpatterns = [
    path('export/csv/', ExportDataCSVView.as_view(), name='export_csv'),
    path('export/t0/csv/', ExportT0DataCSVView.as_view(), name='export_t0_csv'),
    path('export/t1/csv/', ExportT1DataCSVView.as_view(), name='export_t1_csv'),
    path('export/t-first-month/csv/', ExportTFirstMonthDataCSVView.as_view(), name='export_t_first_month_csv'),
    path('export/t2/csv/', ExportT2DataCSVView.as_view(), name='export_t2_csv'),
    path('export/t3/csv/', ExportT3DataCSVView.as_view(), name='export_t3_csv'),
    path('export/t4/csv/', ExportT4DataCSVView.as_view(), name='export_t4_csv'),
    path('export/longitudinal/csv/', ExportLongitudinalDataCSVView.as_view(), name='export_longitudinal_csv'),
    path('export/daily-entries/csv/', ExportDailyEntriesDataCSVView.as_view(), name='export_daily_entries_csv'),
    path('export/status/<uuid:task_id>/', ExportTaskStatusView.as_view(), name='export_task_status'),
    path('dashboard-analytics/', AdminDashboardAnalyticsView.as_view(), name='dashboard_analytics'),
]
