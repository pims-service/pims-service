from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response as DRFResponse
from django.db.models import Count
from .models import Group
from .serializers import GroupSerializer

class GroupListView(generics.ListAPIView):
    """Publicly accessible list of active groups."""
    queryset = Group.objects.filter(is_active=True).annotate(
        member_count=Count('participants')
    )
    serializer_class = GroupSerializer
    permission_classes = (permissions.IsAuthenticated,)

class GroupAdminViewSet(viewsets.ModelViewSet):
    """
    Administrative interface for managing groups.
    Only accessible by staff/admin users (except for retrieve).
    """
    queryset = Group.objects.annotate(
        member_count=Count('participants')
    ).order_by('name')
    serializer_class = GroupSerializer
    lookup_field = 'group_id'

    def get_permissions(self):
        """
        Custom permissions:
        - Authenticated users can retrieve details.
        - Only admins can perform other actions (create, update, delete, toggle_active).
        """
        if self.action == 'retrieve':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, group_id=None):
        group = self.get_object()
        group.is_active = not group.is_active
        group.save(update_fields=['is_active'])
        
        status_text = 'active' if group.is_active else 'inactive'
        return DRFResponse({
            'status': status_text,
            'is_active': group.is_active
        })
