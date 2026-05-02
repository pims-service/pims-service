from rest_framework import serializers
from .models import SupportTicket

class SupportTicketSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = SupportTicket
        fields = ['id', 'ticket_number', 'user_email', 'user_full_name', 'subject', 'message', 'status', 'admin_reply', 'is_read_by_user', 'created_at', 'updated_at']
        read_only_fields = ['ticket_number', 'status', 'admin_reply', 'is_read_by_user', 'created_at', 'updated_at']

class AdminSupportTicketSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = SupportTicket
        fields = ['id', 'ticket_number', 'user_email', 'user_full_name', 'subject', 'message', 'status', 'admin_notes', 'admin_reply', 'is_read_by_user', 'created_at', 'updated_at']
        read_only_fields = ['ticket_number', 'subject', 'message', 'created_at', 'updated_at']

