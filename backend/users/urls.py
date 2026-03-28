from django.urls import path
from .views import RegisterView, ProfileView, AdminUserListView, AdminUserUpdateView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/<int:pk>/', AdminUserUpdateView.as_view(), name='admin_user_update'),
]
