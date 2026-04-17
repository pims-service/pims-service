from django.urls import path
from .views import (
    QuestionnaireListView, 
    QuestionnaireDetailView, 
    ResponseSetCreateView,
    ResponseSetSubmitView
)
from .analytics_views import (
    QuestionnaireExportView,
    QuestionnaireAnalyticsSummaryView
)

urlpatterns = [
    path('', QuestionnaireListView.as_view(), name='questionnaire_list'),
    path('<uuid:pk>/', QuestionnaireDetailView.as_view(), name='questionnaire_detail'),
    path('response-sets/', ResponseSetCreateView.as_view(), name='response_set_create'),
    
    # Response Management
    path('response-sets/<uuid:pk>/submit/', ResponseSetSubmitView.as_view(), name='response_set_submit'),
    
    # Analytics & Export
    path('<uuid:pk>/export/', QuestionnaireExportView.as_view(), name='questionnaire_export'),
    path('<uuid:pk>/analytics/', QuestionnaireAnalyticsSummaryView.as_view(), name='questionnaire_analytics'),
]
