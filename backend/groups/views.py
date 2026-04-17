from rest_framework import generics, permissions
from .models import Group
from .serializers import GroupSerializer, GroupDetailSerializer

class GroupListView(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return super().get_permissions()

class GroupDetailView(generics.RetrieveAPIView):
    """
    Detailed view of a single group, including its participants.
    Only accessible by administrators.
    """
    queryset = Group.objects.all()
    serializer_class = GroupDetailSerializer
    permission_classes = (permissions.IsAdminUser,)

