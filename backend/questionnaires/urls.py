from django.urls import path
# Administrative Data Routing
from .views import (
    QuestionnaireListView, 
    QuestionnaireDetailView, 
    ResponseSetListCreateView,
    ResponseSetDetailView,
    ResponseSetSubmitView,
    AdminBaselineResponseListView,
    AdminBaselineResponseDetailView,
    AdminPosttestResponseListView,
    AdminPosttestResponseDetailView
)
from .analytics_views import (
    QuestionnaireExportView,
    QuestionnaireAnalyticsSummaryView,
    GlobalQuestionnaireAnalyticsView
)

urlpatterns = [
    # Admin & Research Data (Prioritized)
    path('baselines/', AdminBaselineResponseListView.as_view(), name='admin_baseline_list'),
    path('baselines/<uuid:pk>/', AdminBaselineResponseDetailView.as_view(), name='admin_baseline_detail'),
    path('posttests/', AdminPosttestResponseListView.as_view(), name='admin_posttest_list'),
    path('posttests/<uuid:pk>/', AdminPosttestResponseDetailView.as_view(), name='admin_posttest_detail'),

    path('', QuestionnaireListView.as_view(), name='questionnaire_list'),
    path('<uuid:pk>/', QuestionnaireDetailView.as_view(), name='questionnaire_detail'),
    path('response-sets/', ResponseSetListCreateView.as_view(), name='response_set_list_create'),
    path('response-sets/<uuid:pk>/', ResponseSetDetailView.as_view(), name='response_set_detail'),
    
    # Response Management
    path('response-sets/<uuid:pk>/submit/', ResponseSetSubmitView.as_view(), name='response_set_submit'),
    
    # Analytics & Export
    path('analytics/all/', GlobalQuestionnaireAnalyticsView.as_view(), name='global_questionnaire_analytics'),
    path('<uuid:pk>/export/', QuestionnaireExportView.as_view(), name='questionnaire_export'),
    path('<uuid:pk>/analytics/', QuestionnaireAnalyticsSummaryView.as_view(), name='questionnaire_analytics'),
]
