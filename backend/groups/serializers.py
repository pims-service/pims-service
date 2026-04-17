from rest_framework import serializers
from .models import Group

class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        from users.models import User
        model = User
        fields = ['user_id', 'full_name', 'username']
        extra_kwargs = {
            'full_name': {'allow_blank': True, 'required': False},
        }

class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = ['group_id', 'name', 'description', 'created_at', 'member_count']

class GroupDetailSerializer(GroupSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)

    class Meta(GroupSerializer.Meta):
        fields = GroupSerializer.Meta.fields + ['participants']
