from django.urls import path
from .views import QuestionnaireDetailView, ResponseCreateView

urlpatterns = [
    path('<int:pk>/', QuestionnaireDetailView.as_view(), name='questionnaire_detail'),
    path('submit/', ResponseCreateView.as_view(), name='response_create'),
]
