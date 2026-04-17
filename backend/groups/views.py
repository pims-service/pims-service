from django.db.models import Count
from rest_framework import generics, permissions
from .models import Group
from .serializers import GroupSerializer, GroupDetailSerializer


class GroupListView(generics.ListCreateAPIView):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Group.objects.annotate(member_count=Count('participants'))

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return super().get_permissions()

class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GroupDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Group.objects.annotate(member_count=Count('participants')).prefetch_related('participants')


    def get_permissions(self):
        if self.request.method in ('PATCH', 'PUT', 'DELETE'):
            return [permissions.IsAdminUser()]
        return super().get_permissions()

