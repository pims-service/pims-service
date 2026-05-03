from rest_framework import serializers
from .models import Activity, Submission
from django.utils import timezone

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['id', 'title', 'description', 'activity_type', 'day_number']

class DailySubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['id', 'activity', 'content', 'submission_date']
        read_only_fields = ['submission_date']

    def validate(self, data):
        user = self.context['request'].user
        activity = data['activity']
        current_day = user.current_experiment_day
        
        # Ensure activity belongs to user's group or is global
        if activity.group and activity.group != user.group:
            raise serializers.ValidationError("This activity is not assigned to your group.")
            
        # Ensure activity matches the user's current experiment day
        if activity.day_number and activity.day_number != current_day:
            raise serializers.ValidationError(f"You can only submit for Day {current_day}. This activity is for Day {activity.day_number}.")
            
        return data

class SubmissionSerializer(serializers.ModelSerializer):
    activity_title = serializers.CharField(source='activity.title', read_only=True)

    class Meta:
        model = Submission
        fields = ['id', 'activity', 'activity_title', 'content', 'submission_date']
        read_only_fields = ['submission_date']
