from django.urls import path
from .views import GroupListView

urlpatterns = [
    path('', GroupListView.as_view(), name='group_list'),
]
