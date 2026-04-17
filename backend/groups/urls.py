from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GroupListView, GroupDetailView, GroupViewSet

router = DefaultRouter()
router.register(r'admin', GroupViewSet, basename='group-admin')

urlpatterns = [
    # Administrative endpoints (matches /api/groups/admin/*)
    path('admin/', include(router.urls)),
    path('', GroupListView.as_view(), name='group_list'),
    path('<int:pk>/', GroupDetailView.as_view(), name='group-detail'),
]
