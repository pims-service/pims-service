from django.urls import path
from .views import QuestionnaireListView, QuestionnaireDetailView, ResponseSetCreateView

urlpatterns = [
    path('', QuestionnaireListView.as_view(), name='questionnaire_list'),
    path('<uuid:pk>/', QuestionnaireDetailView.as_view(), name='questionnaire_detail'),
    path('response-sets/', ResponseSetCreateView.as_view(), name='response_set_create'),
]
