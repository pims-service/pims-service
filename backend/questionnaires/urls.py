from django.urls import path
# Administrative Data Routing
from .views import (
    QuestionnaireListView, 
    QuestionnaireDetailView, 
    ResponseSetListCreateView,
    ResponseSetDetailView,
    ResponseSetSubmitView,
    ResponseSetSaveDraftView,
    AdminT0ResponseListView,
    AdminT0ResponseDetailView,
    AdminT1ResponseListView,
    AdminT1ResponseDetailView,
    AdminT2ResponseListView,
    AdminT2ResponseDetailView,
    AdminT3ResponseListView,
    AdminT3ResponseDetailView,
    AdminT4ResponseListView,
    AdminT4ResponseDetailView,
    DueMilestoneView
)
from .analytics_views import (
    QuestionnaireExportView,
    QuestionnaireAnalyticsSummaryView,
    GlobalQuestionnaireAnalyticsView
)

urlpatterns = [
    # Admin & Research Data (Prioritized)
    path('t0-results/', AdminT0ResponseListView.as_view(), name='admin_t0_list'),
    path('t0-results/<uuid:pk>/', AdminT0ResponseDetailView.as_view(), name='admin_t0_detail'),
    path('t1-results/', AdminT1ResponseListView.as_view(), name='admin_t1_list'),
    path('t1-results/<uuid:pk>/', AdminT1ResponseDetailView.as_view(), name='admin_t1_detail'),
    path('t2-results/', AdminT2ResponseListView.as_view(), name='admin_t2_list'),
    path('t2-results/<uuid:pk>/', AdminT2ResponseDetailView.as_view(), name='admin_t2_detail'),
    path('t3-results/', AdminT3ResponseListView.as_view(), name='admin_t3_list'),
    path('t3-results/<uuid:pk>/', AdminT3ResponseDetailView.as_view(), name='admin_t3_detail'),
    path('t4-results/', AdminT4ResponseListView.as_view(), name='admin_t4_list'),
    path('t4-results/<uuid:pk>/', AdminT4ResponseDetailView.as_view(), name='admin_t4_detail'),

    path('due/', DueMilestoneView.as_view(), name='due_milestone'),
    path('', QuestionnaireListView.as_view(), name='questionnaire_list'),
    path('<uuid:pk>/', QuestionnaireDetailView.as_view(), name='questionnaire_detail'),
    path('response-sets/', ResponseSetListCreateView.as_view(), name='response_set_list_create'),
    path('response-sets/<uuid:pk>/', ResponseSetDetailView.as_view(), name='response_set_detail'),
    
    # Response Management
    path('response-sets/<uuid:pk>/submit/', ResponseSetSubmitView.as_view(), name='response_set_submit'),
    path('response-sets/<uuid:pk>/save-draft/', ResponseSetSaveDraftView.as_view(), name='response_set_save_draft'),
    
    # Analytics & Export
    path('analytics/all/', GlobalQuestionnaireAnalyticsView.as_view(), name='global_questionnaire_analytics'),
    path('<uuid:pk>/export/', QuestionnaireExportView.as_view(), name='questionnaire_export'),
    path('<uuid:pk>/analytics/', QuestionnaireAnalyticsSummaryView.as_view(), name='questionnaire_analytics'),
]
