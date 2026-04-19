from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DailyActivityViewSet, ActivityViewSet, SubmissionViewSet

router = DefaultRouter()
router.register(r'daily', DailyActivityViewSet, basename='daily-activity')
router.register(r'all', ActivityViewSet, basename='activity')
router.register(r'all-submissions', SubmissionViewSet, basename='submission')

urlpatterns = [
    path('', include(router.urls)),
    # Manual aliases for backward compatibility with established test names
    path('list/', ActivityViewSet.as_view({'get': 'list'}), name='activity_list'),
    path('submit/', SubmissionViewSet.as_view({'post': 'create'}), name='submission_create'),
]
