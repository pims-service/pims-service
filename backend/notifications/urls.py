from django.urls import path
from .views import NotificationListView, AdminScheduleNotificationView

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('admin/schedule/', AdminScheduleNotificationView.as_view(), name='admin_schedule'),
]
