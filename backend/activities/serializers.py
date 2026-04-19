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
        
        # Enforce Once per Day logic (Midnight Reset)
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        already_submitted = Submission.objects.filter(
            user=user,
            submission_date__gte=today_start
        ).exists()
        
        if already_submitted:
            raise serializers.ValidationError("You have already submitted an activity for today. Please wait until tomorrow.")

        # Ensure activity belongs to user's group or is global
        if activity.group and activity.group != user.group:
            raise serializers.ValidationError("This activity is not assigned to your group.")
            
        return data
