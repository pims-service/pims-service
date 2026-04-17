from rest_framework import serializers
from .models import Group

class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(source='participants.count', read_only=True)

    class Meta:
        model = Group
        fields = ('group_id', 'name', 'description', 'member_count', 'created_at')

class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        # Import inside to avoid circular dependency if needed, 
        # but User is already used in others or we can use settings.AUTH_USER_MODEL
        from users.models import User
        model = User
        fields = ('user_id', 'full_name', 'username')

class GroupDetailSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    member_count = serializers.IntegerField(source='participants.count', read_only=True)

    class Meta:
        model = Group
        fields = ('group_id', 'name', 'description', 'member_count', 'participants', 'created_at')

