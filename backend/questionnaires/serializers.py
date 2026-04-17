from rest_framework import serializers
from .models import Questionnaire, Question, Option, ResponseSet, Response

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'label', 'numeric_value', 'order']

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'content', 'type', 'order', 'required', 'options']

class QuestionnaireSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Questionnaire
        fields = ['id', 'title', 'description', 'is_active', 'is_baseline', 'max_completion_time', 'questions']

class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = ['id', 'question', 'selected_option', 'text_value']

class ResponseSetSerializer(serializers.ModelSerializer):
    responses = ResponseSerializer(many=True, read_only=True)
    questionnaire_title = serializers.CharField(source='questionnaire.title', read_only=True)

    class Meta:
        model = ResponseSet
        fields = ['id', 'user', 'questionnaire', 'questionnaire_title', 'status', 'started_at', 'completed_at', 'responses']
        read_only_fields = ['user', 'started_at', 'completed_at', 'status']

class ResponseBulkSerializer(serializers.Serializer):
    """
    Serializer for individual responses within a bulk submission.
    """
    question_id = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all(), source='question')
    selected_option_id = serializers.PrimaryKeyRelatedField(queryset=Option.objects.all(), source='selected_option', required=False, allow_null=True)
    text_value = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class ResponseSetSubmitSerializer(serializers.ModelSerializer):
    """
    Serializer to handle the final submission of a ResponseSet with all answers.
    """
    responses_data = ResponseBulkSerializer(many=True, write_only=True)

    class Meta:
        model = ResponseSet
        fields = ['id', 'responses_data']

    def validate(self, attrs):
        response_set = self.instance
        questionnaire = response_set.questionnaire
        responses_data = attrs.get('responses_data', [])

        # Validate that all questions belong to this questionnaire
        allowed_question_ids = set(questionnaire.questions.values_list('id', flat=True))
        for item in responses_data:
            if item['question'].id not in allowed_question_ids:
                raise serializers.ValidationError(
                    f"Question {item['question'].id} does not belong to questionnaire {questionnaire.id}"
                )
            
            # Additional validation: selected_option must belong to the question
            if item.get('selected_option') and item['selected_option'].question_id != item['question'].id:
                raise serializers.ValidationError(
                    f"Option {item['selected_option'].id} is not a valid choice for question {item['question'].id}"
                )
        
        return attrs

    def update(self, instance, validated_data):
        from django.db import transaction
        from django.utils import timezone
        from groups.services import assign_user_to_group

        responses_data = validated_data.pop('responses_data')
        
        with transaction.atomic():
            # 1. Clear any existing draft responses (if any)
            instance.responses.all().delete()
            
            # 2. Bulk create new responses
            for item in responses_data:
                Response.objects.create(
                    response_set=instance,
                    **item
                )
            
            # 3. Mark as COMPLETED
            instance.status = 'COMPLETED'
            instance.completed_at = timezone.now()
            instance.save()

            # 4. Trigger Group Assignment if Baseline
            if instance.questionnaire.is_baseline:
                assign_user_to_group(instance.user)
                instance.user.has_completed_baseline = True
                instance.user.save(update_fields=['has_completed_baseline'])

        return instance
