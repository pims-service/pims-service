from django.urls import path
from .views import PhaseListView, CurrentPhaseView

urlpatterns = [
    path('', PhaseListView.as_view(), name='phase_list'),
    path('current/', CurrentPhaseView.as_view(), name='current_phase'),
]
