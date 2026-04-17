from django.urls import path
from .views import GroupListView, GroupDetailView

urlpatterns = [
    path('', GroupListView.as_view(), name='group_list'),
    path('<int:pk>/', GroupDetailView.as_view(), name='group-detail'),
]
