from rest_framework import serializers
from .models import Group
from django.db.models import Count

class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        from users.models import User
        model = User
        fields = ['user_id', 'full_name', 'username']
        extra_kwargs = {
            'full_name': {'allow_blank': True, 'required': False},
        }

class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True, default=0)
    participants = ParticipantSerializer(many=True, read_only=True)

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
