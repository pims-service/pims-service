from django.urls import path
from .views import ProfileView, AdminUserListView, AdminUserUpdateView, AdminUserDeleteView

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/<int:pk>/', AdminUserUpdateView.as_view(), name='admin_user_update'),
    path('admin/users/<int:pk>/delete/', AdminUserDeleteView.as_view(), name='admin_user_delete'),
]
