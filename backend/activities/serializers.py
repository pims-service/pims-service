import re
from rest_framework import serializers
from .models import Activity, Submission
from django.utils import timezone

def clean_group_from_title(title):
    if not title:
        return title
    # Replace " - Group X - " with " - "
    cleaned = re.sub(r'\s*-\s*Group\s+\d+\s*-\s*', ' - ', title)
    # Replace " - Group X" or "Group X - " with a space or empty string
    cleaned = re.sub(r'\s*-\s*Group\s+\d+\s*', ' ', cleaned)
    cleaned = re.sub(r'\bGroup\s+\d+\b', '', cleaned)
    return re.sub(r'\s+', ' ', cleaned).strip()

class ActivitySerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    class Meta:
        model = Activity
        fields = ['id', 'title', 'description', 'activity_type', 'day_number', 'group_name']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if 'title' in rep and rep['title']:
            rep['title'] = clean_group_from_title(rep['title'])
        return rep

def count_words(text):
    if not text:
        return 0
    return len(text.strip().split())

class DailySubmissionSerializer(serializers.ModelSerializer):
    content = serializers.CharField(required=False, allow_blank=True)
    class Meta:
        model = Submission
        fields = ['id', 'activity', 'entry_1', 'entry_2', 'entry_3', 'content', 'submission_date']
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
            
        entry_1 = data.get('entry_1', '')
        entry_2 = data.get('entry_2', '')
        entry_3 = data.get('entry_3', '')

        # If any of the entry fields are provided, validate word counts for all three
        if 'entry_1' in data or 'entry_2' in data or 'entry_3' in data:
            for field_name, entry_text in [('entry_1', entry_1), ('entry_2', entry_2), ('entry_3', entry_3)]:
                words = count_words(entry_text)
                if words < 20:
                    raise serializers.ValidationError({field_name: "Minimum word count per entry is 20 words."})
                if words > 200:
                    raise serializers.ValidationError({field_name: "Maximum word count per entry is 200 words."})

        return data

class SubmissionSerializer(serializers.ModelSerializer):
    activity_title = serializers.CharField(source='activity.title', read_only=True)
    content = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Submission
        fields = ['id', 'activity', 'activity_title', 'entry_1', 'entry_2', 'entry_3', 'content', 'submission_date']
        read_only_fields = ['submission_date']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if 'activity_title' in rep and rep['activity_title']:
            rep['activity_title'] = clean_group_from_title(rep['activity_title'])
        return rep
