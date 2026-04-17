from rest_framework import serializers
from .models import Group
from django.db.models import Count

class UserMinimalSerializer(serializers.Serializer):
    """
    Minimal user representation for nested group data.
    """
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)

class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True, default=0)
    participants = UserMinimalSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = [
            'group_id', 
            'name', 
            'description', 
            'capacity', 
            'is_active', 
            'member_count', 
            'participants',
            'created_at'
        ]
        read_only_fields = ['created_at', 'member_count', 'participants']
