from django.urls import path
from .views import ActivityListView, SubmissionCreateView, UserSubmissionListView

urlpatterns = [
    path('', ActivityListView.as_view(), name='activity_list'),
    path('submit/', SubmissionCreateView.as_view(), name='submission_create'),
    path('submissions/', UserSubmissionListView.as_view(), name='user_submissions'),
]
