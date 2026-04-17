from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GroupListView, GroupAdminViewSet

router = DefaultRouter()
router.register(r'', GroupAdminViewSet, basename='group-admin')

urlpatterns = [
    # Public endpoints
    path('', GroupListView.as_view(), name='group-list'),
    
    # Administrative endpoints
    path('', include(router.urls)),
]
