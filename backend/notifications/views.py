from rest_framework import generics, permissions
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class AdminScheduleNotificationView(generics.CreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAdminUser,)
