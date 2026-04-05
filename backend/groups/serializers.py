from rest_framework import serializers
from .models import Group


class ParticipantSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    full_name = serializers.CharField()


class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = ['group_id', 'name', 'description', 'created_at', 'member_count']


class GroupDetailSerializer(GroupSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)

    class Meta(GroupSerializer.Meta):
        fields = GroupSerializer.Meta.fields + ['participants']
