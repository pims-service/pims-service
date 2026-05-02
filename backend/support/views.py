from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import SupportTicket
from .serializers import SupportTicketSerializer, AdminSupportTicketSerializer

class SupportTicketViewSet(viewsets.ModelViewSet):
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role == 'Admin':
            return SupportTicket.objects.all()
        return SupportTicket.objects.filter(user=self.request.user)
    
    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve', 'mark_read', 'unread_count']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.request.user.is_staff or self.request.user.role == 'Admin':
            return AdminSupportTicketSerializer
        return SupportTicketSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        ticket = self.get_object()
        ticket.is_read_by_user = True
        ticket.save()
        return Response({'status': 'marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(admin_reply__isnull=False, is_read_by_user=False).exclude(admin_reply='').count()
        return Response({'count': count})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def open_count(self, request):
        count = SupportTicket.objects.filter(status__in=['Open', 'In Progress']).count()
        return Response({'count': count})

