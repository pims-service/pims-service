import logging
from rest_framework import serializers
from .models import Questionnaire, Question, Option, ResponseSet, Response
from .scoring import calculate_and_save_scores

logger = logging.getLogger(__name__)


def check_and_trigger_risk_protocol(response_set):
    """
    Checks if the response set contains a high risk answer:
    - PHQ-9 Item 9 >= 1
    - SIDAS Item 3 > 0
    - SIDAS Total >= 21
    and triggers a risk-protocol alert if found.
    """
    from django.core.cache import cache
    from django.contrib.auth import get_user_model
    from notifications.models import Notification
    from django.utils import timezone

    triggered = False
    reasons = []

    # 1. PHQ-9 Item 9 >= 1
    item_9_response = Response.objects.filter(
        response_set=response_set,
        question__order=32
    ).first()
    if not item_9_response:
        item_9_response = Response.objects.filter(
            response_set=response_set,
            question__content__icontains="[PHQ-9]"
        ).filter(
            question__content__icontains="dead"
        ).first()

    if item_9_response and item_9_response.selected_option:
        val = item_9_response.selected_option.numeric_value
        if val >= 1:
            triggered = True
            reasons.append(f"PHQ-9 Item 9 with score {val} (Suicidal Ideation/Self-Harm)")

    # 2. SIDAS Item 3 > 0 (closeness to attempt)
    sidas_3_response = Response.objects.filter(
        response_set=response_set,
        question__order=77
    ).first()
    if sidas_3_response and sidas_3_response.selected_option:
        val_sidas_3 = sidas_3_response.selected_option.numeric_value
        if val_sidas_3 > 0:
            triggered = True
            reasons.append(f"SIDAS Item 3 with score {val_sidas_3} (Closeness to suicide attempt)")

    # 3. SIDAS Total >= 21
    sidas_total = response_set.scores.get('SIDAS_TOTAL')
    if sidas_total is not None and sidas_total >= 21:
        triggered = True
        reasons.append(f"SIDAS Total with score {sidas_total} (High suicide risk)")

    if triggered:
        cache_key = f"risk_alert_triggered_{response_set.id}"
        
        if not cache.get(cache_key):
            cache.set(cache_key, True, timeout=86400)
            
            user = response_set.user
            reasons_str = ", ".join(reasons)
            
            logger.critical(
                "RISK PROTOCOL ALERT: User %s (ID: %s, Email: %s) flagged for suicidal risk: %s.",
                user.username, user.id, user.email, reasons_str
            )
            
            User = get_user_model()
            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    n_type='email',
                    message=(
                        f"CRITICAL SAFETY ALERT: Participant '{user.username}' (ID: {user.id}) "
                        f"has triggered suicidal risk protocols. Reasons: {reasons_str}. "
                        f"Immediate clinical follow-up required."
                    ),
                    scheduled_time=timezone.now(),
                    status='pending'
                )


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
        fields = ['id', 'title', 'description', 'is_active', 'is_posttest', 'assessment_type', 'max_completion_time', 'questions']

class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = ['id', 'question', 'selected_option', 'text_value']

class ResponseSetSerializer(serializers.ModelSerializer):
    responses = ResponseSerializer(many=True, read_only=True)
    questionnaire_title = serializers.CharField(source='questionnaire.title', read_only=True)
    milestone = serializers.CharField(required=False, allow_null=True, allow_blank=True, default=None)

    class Meta:
        model = ResponseSet
        fields = ['id', 'user', 'questionnaire', 'questionnaire_title', 'status', 'started_at', 'completed_at', 'responses', 'milestone']
        read_only_fields = ['user', 'started_at', 'completed_at', 'status']

class ResponseSetDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer with nested questionnaire for the Results page."""
    responses = ResponseSerializer(many=True, read_only=True)
    questionnaire = QuestionnaireSerializer(read_only=True)

    class Meta:
        model = ResponseSet
        fields = ['id', 'user', 'questionnaire', 'status', 'started_at', 'completed_at', 'responses']

class AdminResponseSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.content', read_only=True)
    question_type = serializers.CharField(source='question.type', read_only=True)
    selected_option_label = serializers.CharField(source='selected_option.label', read_only=True, allow_null=True, default=None)

    class Meta:
        model = Response
        fields = ['id', 'question', 'question_text', 'question_type', 'selected_option', 'selected_option_label', 'text_value']

class AdminResponseSetSerializer(serializers.ModelSerializer):
    responses = AdminResponseSerializer(many=True, read_only=True)
    full_name = serializers.CharField(source='user.display_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    whatsapp_number = serializers.CharField(source='user.whatsapp_number', read_only=True)
    questionnaire_title = serializers.CharField(source='questionnaire.title', read_only=True)
    group_name = serializers.SerializerMethodField()

    class Meta:
        model = ResponseSet
        fields = [
            'id', 'user', 'full_name', 'username', 'whatsapp_number',
            'questionnaire', 'questionnaire_title', 
            'group_name',
            'status', 'started_at', 'completed_at', 
            'responses'
        ]

    def get_group_name(self, obj):
        if hasattr(obj.user, 'group') and obj.user.group:
            return obj.user.group.name
        return None

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

        # Validate that all questions belong to this questionnaire and no duplicates exist
        allowed_question_ids = set(questionnaire.questions.values_list('id', flat=True))
        seen_questions = set()

        for item in responses_data:
            q_id = item['question'].id
            if q_id not in allowed_question_ids:
                raise serializers.ValidationError(
                    f"Question {q_id} does not belong to questionnaire {questionnaire.id}"
                )
            
            if q_id in seen_questions:
                raise serializers.ValidationError(
                    f"Duplicate answer submitted for question {q_id}. Only one answer per question is allowed."
                )
            seen_questions.add(q_id)
            
            # Additional validation: selected_option must belong to the question
            if item.get('selected_option') and item['selected_option'].question_id != q_id:
                raise serializers.ValidationError(
                    f"Option {item['selected_option'].id} is not a valid choice for question {q_id}"
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

            # 4. Handle Onboarding Completions (Sociodemographic)
            user = instance.user
            if instance.questionnaire.assessment_type == 'SOCIODEMOGRAPHIC':
                is_disqualified = False
                for item in responses_data:
                    option = item.get('selected_option')
                    if option and 'DISQUALIFY' in option.label:
                        is_disqualified = True
                        break
                
                if is_disqualified:
                    user.is_disqualified = True
                    user.disqualification_reason = "Answered YES to eligibility screener."
                    user.save(update_fields=['is_disqualified', 'disqualification_reason'])
                else:
                    assign_user_to_group(user)
                    user.has_completed_sociodemographic = True
                    user.save(update_fields=['has_completed_sociodemographic'])

            # 4.5. Set onboarding_completed_at when SIGNUP milestone of PSYCHOMETRIC questionnaire is completed
            if instance.milestone == 'SIGNUP' and instance.questionnaire.assessment_type == 'PSYCHOMETRIC':
                user.onboarding_completed_at = timezone.now()
                user.save(update_fields=['onboarding_completed_at'])

            # 5. Mark post-test completed if milestone is '7_DAYS' or is_legacy_posttest
            is_legacy_posttest = instance.questionnaire.is_posttest
            if instance.milestone == '7_DAYS' or is_legacy_posttest:
                user.has_completed_posttest = True
                user.posttest_completed_at = timezone.now()
                user.save(update_fields=['has_completed_posttest', 'posttest_completed_at'])

            # Invalidate cached due milestone on submission
            from django.core.cache import cache
            cache.delete(f"user_{user.id}_due_milestone")

            # Calculate and save scores
            calculate_and_save_scores(instance)

            # Check and trigger risk-protocol alert
            check_and_trigger_risk_protocol(instance)

        return instance

class ResponseSetDraftSerializer(serializers.ModelSerializer):
    """
    Serializer to handle incremental saving of a ResponseSet (auto-save),
    without marking it as COMPLETED.
    """
    responses_data = ResponseBulkSerializer(many=True, write_only=True)

    class Meta:
        model = ResponseSet
        fields = ['id', 'responses_data']

    def validate(self, attrs):
        response_set = self.instance
        questionnaire = response_set.questionnaire
        responses_data = attrs.get('responses_data', [])

        allowed_question_ids = set(questionnaire.questions.values_list('id', flat=True))
        seen_questions = set()

        for item in responses_data:
            q_id = item['question'].id
            if q_id not in allowed_question_ids:
                raise serializers.ValidationError(
                    f"Question {q_id} does not belong to questionnaire {questionnaire.id}"
                )
            
            if q_id in seen_questions:
                raise serializers.ValidationError(
                    f"Duplicate answer submitted for question {q_id}. Only one answer per question is allowed."
                )
            seen_questions.add(q_id)
            
            if item.get('selected_option') and item['selected_option'].question_id != q_id:
                raise serializers.ValidationError(
                    f"Option {item['selected_option'].id} is not a valid choice for question {q_id}"
                )
        
        return attrs

    def update(self, instance, validated_data):
        from django.db import transaction

        responses_data = validated_data.pop('responses_data', [])
        
        with transaction.atomic():
            # Clear existing draft responses and replace them
            instance.responses.all().delete()
            
            for item in responses_data:
                Response.objects.create(
                    response_set=instance,
                    **item
                )
            
            # Note: We do NOT mark status = 'COMPLETED' or set completed_at
            instance.save()

            # Calculate and save scores on draft saving
            calculate_and_save_scores(instance)

            # Check and trigger risk-protocol alert on draft saving
            check_and_trigger_risk_protocol(instance)

        return instance
