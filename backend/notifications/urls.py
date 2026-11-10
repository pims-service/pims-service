from django.urls import path
from .views import (
    NotificationListView,
    AdminScheduleNotificationView,
    AdminManualEmailRecipientsView,
    AdminManualEmailTestView,
    AdminManualEmailSendView,
    AdminManualEmailHistoryView,
    UnsubscribeView,
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('admin/schedule/', AdminScheduleNotificationView.as_view(), name='admin_schedule'),
    path('admin/manual-email/recipients/', AdminManualEmailRecipientsView.as_view(), name='manual_email_recipients'),
    path('admin/manual-email/test/', AdminManualEmailTestView.as_view(), name='manual_email_test'),
    path('admin/manual-email/send/', AdminManualEmailSendView.as_view(), name='manual_email_send'),
    path('admin/manual-email/history/', AdminManualEmailHistoryView.as_view(), name='manual_email_history'),
    path('unsubscribe/<str:token>/', UnsubscribeView.as_view(), name='manual_email_unsubscribe'),
]
