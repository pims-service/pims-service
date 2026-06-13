from rest_framework import serializers
from .models import Group

class ParticipantSerializer(serializers.ModelSerializer):
    submission_count = serializers.SerializerMethodField()

    class Meta:
        from users.models import User
        model = User
        fields = ['user_id', 'full_name', 'username', 'email', 'whatsapp_number', 'submission_count', 'has_completed_sociodemographic', 'current_experiment_day', 'is_disqualified']
        extra_kwargs = {
            'full_name': {'allow_blank': True, 'required': False},
        }

    def get_submission_count(self, obj):
        return obj.submissions.count()

class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = ['group_id', 'name', 'description', 'created_at', 'member_count']

class GroupDetailSerializer(GroupSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)

    class Meta(GroupSerializer.Meta):
        fields = GroupSerializer.Meta.fields + ['participants']
