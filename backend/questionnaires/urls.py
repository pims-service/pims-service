from django.urls import path
# Administrative Data Routing
from .views import (
    QuestionnaireListView, 
    QuestionnaireDetailView, 
    ResponseSetListCreateView,
    ResponseSetDetailView,
    ResponseSetSubmitView,
    AdminBaselineResponseListView,
    AdminBaselineResponseDetailView
)
from .analytics_views import (
    QuestionnaireExportView,
    QuestionnaireAnalyticsSummaryView
)

urlpatterns = [
    # Admin & Research Data (Prioritized)
    path('baselines/', AdminBaselineResponseListView.as_view(), name='admin_baseline_list'),
    path('baselines/<uuid:pk>/', AdminBaselineResponseDetailView.as_view(), name='admin_baseline_detail'),

    path('', QuestionnaireListView.as_view(), name='questionnaire_list'),
    path('<uuid:pk>/', QuestionnaireDetailView.as_view(), name='questionnaire_detail'),
    path('response-sets/', ResponseSetListCreateView.as_view(), name='response_set_list_create'),
    path('response-sets/<uuid:pk>/', ResponseSetDetailView.as_view(), name='response_set_detail'),
    
    # Response Management
    path('response-sets/<uuid:pk>/submit/', ResponseSetSubmitView.as_view(), name='response_set_submit'),
    
    # Analytics & Export
    path('<uuid:pk>/export/', QuestionnaireExportView.as_view(), name='questionnaire_export'),
    path('<uuid:pk>/analytics/', QuestionnaireAnalyticsSummaryView.as_view(), name='questionnaire_analytics'),
]
