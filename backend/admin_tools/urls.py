from django.urls import path
from .views import ExportDataCSVView

urlpatterns = [
    path('export/csv/', ExportDataCSVView.as_view(), name='export_csv'),
]
