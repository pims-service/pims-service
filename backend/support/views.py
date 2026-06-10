from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from .models import SupportTicket
from .serializers import SupportTicketSerializer, AdminSupportTicketSerializer

class SupportTicketPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'results': data
        })

class SupportTicketViewSet(viewsets.ModelViewSet):
    pagination_class = SupportTicketPagination
    
    def get_queryset(self):
        if self.request.user.is_staff or (self.request.user.role and self.request.user.role.name == 'Admin'):
            return SupportTicket.objects.all()
        return SupportTicket.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if request.user.is_staff or (request.user.role and request.user.role.name == 'Admin'):
            queryset = queryset.exclude(subject__icontains="Call Protocol")
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve', 'mark_read', 'unread_count']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.request.user.is_staff or (self.request.user.role and self.request.user.role.name == 'Admin'):
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
        count = SupportTicket.objects.filter(status__in=['Open', 'In Progress']).exclude(subject__icontains="Call Protocol").count()
        return Response({'count': count})

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def follow_ups(self, request):
        tickets = SupportTicket.objects.filter(subject__icontains="Call Protocol")
        page = self.paginate_queryset(tickets)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(tickets, many=True)
        return Response(serializer.data)


