from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DailyActivityViewSet

router = DefaultRouter()
router.register(r'daily', DailyActivityViewSet, basename='daily-activity')

urlpatterns = [
    path('', include(router.urls)),
]
