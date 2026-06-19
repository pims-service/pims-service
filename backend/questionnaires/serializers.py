import logging
from rest_framework import serializers
from .models import Questionnaire, Question, Option, ResponseSet, Response
from .scoring import calculate_and_save_scores

logger = logging.getLogger(__name__)


def check_and_trigger_risk_protocol(response_set, *, notify_participant=True):
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

    # 1. PHQ-9 Item 9 >= 1  (order 33 after section-header insertion)
    item_9_response = Response.objects.filter(
        response_set=response_set,
        question__order=33
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

    # 2. SIDAS Item 3 > 0 (closeness to attempt, order 80 after section-header insertion)
    sidas_3_response = Response.objects.filter(
        response_set=response_set,
        question__order=80
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
        if not response_set.suicide_risk_triggered:
            response_set.suicide_risk_triggered = True
            response_set.save(update_fields=['suicide_risk_triggered'])

        user = response_set.user
        reasons_str = ", ".join(reasons)
        from django.db import transaction
        from notifications.tasks import send_notification

        # 1. Notify admins (only once per response set)
        admin_cache_key = f"risk_admin_alerted_{response_set.id}"
        if not cache.get(admin_cache_key):
            cache.set(admin_cache_key, True, timeout=86400)
            
            logger.critical(
                "RISK PROTOCOL ALERT: User %s (ID: %s, Email: %s) flagged for suicidal risk: %s.",
                user.username, user.id, user.email, reasons_str
            )
            
            # Notify admins
            User = get_user_model()
            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                admin_notif = Notification.objects.create(
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
                transaction.on_commit(
                    lambda admin_notif_id=admin_notif.id: send_notification.delay(admin_notif_id)
                )

            from .tasks import refresh_suicide_risk_admin_cache_task
            transaction.on_commit(lambda: refresh_suicide_risk_admin_cache_task.delay())

        # 2. Notify participant (only if notify_participant=True and not already notified)
        if notify_participant:
            part_cache_key = f"risk_participant_alerted_{response_set.id}"
            if not cache.get(part_cache_key):
                cache.set(part_cache_key, True, timeout=86400)
                
                from emails.tasks import send_support_email_task
                transaction.on_commit(
                    lambda user_id=user.user_id: send_support_email_task.delay(user_id)
                )

                participant_message = (
                    "Your responses suggest you may be experiencing distress. To protect your well-being, "
                    "please reach out to one of the support services below. You are not alone.\n\n"
                    "Umang 0311-7786264 (24/7, free, multilingual)\n"
                    "Taskeen 0316-8275336 (Mon–Sat 11am–11pm) + 24/7 chatbot at taskeen.org\n"
                    "Rozan 0304-1118666 / 0800-22444 (Mon–Sat)\n"
                    "Emergency Rescue 1122, Edhi 115, Chhipa 1020"
                )

                p_whatsapp = Notification.objects.create(
                    user=user,
                    n_type='whatsapp',
                    message=participant_message,
                    scheduled_time=timezone.now(),
                    status='pending'
                )
                transaction.on_commit(lambda notif_id=p_whatsapp.id: send_notification.delay(notif_id))


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
        fields = ['id', 'user', 'questionnaire', 'questionnaire_title', 'status', 'started_at', 'completed_at', 'responses', 'milestone', 'suicide_risk_triggered', 'suicide_risk_opt_in']
        read_only_fields = ['user', 'started_at', 'completed_at', 'status', 'suicide_risk_triggered', 'suicide_risk_opt_in']

class ResponseSetDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer with nested questionnaire for the Results page."""
    responses = ResponseSerializer(many=True, read_only=True)
    questionnaire = QuestionnaireSerializer(read_only=True)

    class Meta:
        model = ResponseSet
        fields = ['id', 'user', 'questionnaire', 'status', 'started_at', 'completed_at', 'responses', 'suicide_risk_triggered', 'suicide_risk_opt_in']

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

class AdminResponseSetListSerializer(serializers.ModelSerializer):
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
            'status', 'started_at', 'completed_at'
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
        fields = ['id', 'responses_data', 'suicide_risk_triggered', 'suicide_risk_opt_in']
        read_only_fields = ['suicide_risk_triggered', 'suicide_risk_opt_in']

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
            # Lock the parent response set row to prevent concurrent conflicts
            ResponseSet.objects.select_for_update().get(id=instance.id)

            # 1. Clear any existing draft responses (if any)
            instance.responses.all().delete()
            
            # 2. Bulk create new responses
            responses_to_create = []
            for item in responses_data:
                q = item.get('question')
                opt = item.get('selected_option')
                responses_to_create.append(Response(
                    response_set=instance,
                    question=q,
                    selected_option=opt,
                    text_value=item.get('text_value'),
                    question_text=q.content if q else None,
                    question_order=q.order if q else None,
                    selected_option_value=opt.numeric_value if opt else None,
                    selected_option_label=opt.label if opt else None
                ))
            Response.objects.bulk_create(responses_to_create)
            
            # 3. Mark as COMPLETED
            instance.status = 'COMPLETED'
            instance.completed_at = timezone.now()
            instance.save()

            user = instance.user
            socio_disqualified = False
            if instance.questionnaire.assessment_type == 'SOCIODEMOGRAPHIC':
                is_disqualified = False
                for item in responses_data:
                    option = item.get('selected_option')
                    question = item.get('question')
                    if option:
                        if 'DISQUALIFY' in option.label:
                            is_disqualified = True
                            break
                        if question and question.order in (11, 12) and option.numeric_value == 1:
                            is_disqualified = True
                            break
                
                if is_disqualified:
                    user.is_disqualified = True
                    user.disqualification_reason = "Answered YES to eligibility screener."
                    user.save(update_fields=['is_disqualified', 'disqualification_reason'])
                    socio_disqualified = True
                else:
                    assign_user_to_group(user)
                    user.has_completed_sociodemographic = True
                    user.save(update_fields=['has_completed_sociodemographic'])

            # 4.5. Set onboarding_completed_at when SIGNUP milestone of PSYCHOMETRIC questionnaire is completed
            is_new_onboarding = False
            if instance.milestone == 'SIGNUP' and instance.questionnaire.assessment_type == 'PSYCHOMETRIC':
                is_new_onboarding = user.onboarding_completed_at is None
                user.onboarding_completed_at = timezone.now()
                user.save(update_fields=['onboarding_completed_at'])

            # 5. Mark post-test completed only when the explicit '7_DAYS' milestone is submitted.
            # NOTE: Do NOT use questionnaire.is_posttest here — that legacy flag caused every
            # user who submitted the baseline PSYCHOMETRIC questionnaire (SIGNUP milestone) to be
            # incorrectly marked as posttest-complete, skipping their entire PRE_T1 activity block.
            if instance.milestone == '7_DAYS':
                user.has_completed_posttest = True
                user.posttest_completed_at = timezone.now()
                user.save(update_fields=['has_completed_posttest', 'posttest_completed_at'])

            # Invalidate cached due milestone and activity state on submission
            from django.core.cache import cache
            cache.delete(f"user_{user.id}_due_milestone")
            cache.delete(f"user_{user.id}_activity_state")
            cache.delete(f"user_{user.id}_exp_day")

            # Calculate and save scores
            calculate_and_save_scores(instance)

            # Check and trigger risk-protocol alert
            check_and_trigger_risk_protocol(instance)

            if socio_disqualified:
                from emails.tasks import send_socio_disqualification_email_task
                transaction.on_commit(
                    lambda user_id=user.user_id: send_socio_disqualification_email_task.delay(user_id)
                )
            elif is_new_onboarding and not user.is_disqualified:
                from emails.tasks import send_welcome_email_task
                transaction.on_commit(
                    lambda user_id=user.user_id: send_welcome_email_task.delay(user_id)
                )

            if (
                instance.questionnaire.assessment_type == 'PSYCHOMETRIC'
                and instance.milestone in ('7_DAYS', '1_MONTH', '6_MONTHS', '1_YEAR')
            ):
                from emails.booster_schedule import MILESTONE_PHASE_COMPLETE
                from emails.booster_tasks import send_phase_complete_email_task

                template_key = MILESTONE_PHASE_COMPLETE[instance.milestone]
                transaction.on_commit(
                    lambda user_id=user.user_id, key=template_key: send_phase_complete_email_task.delay(
                        user_id, key
                    )
                )

            # Trigger Month-3 PERMA report task if 3_MONTHS milestone of PSYCHOMETRIC questionnaire is completed
            if instance.milestone == '3_MONTHS' and instance.questionnaire.assessment_type == 'PSYCHOMETRIC':
                from questionnaires.tasks import send_month_3_report_task
                transaction.on_commit(lambda: send_month_3_report_task.delay(instance.id))

        return instance

class ResponseSetDraftSerializer(serializers.ModelSerializer):
    """
    Serializer to handle incremental saving of a ResponseSet (auto-save),
    without marking it as COMPLETED.
    """
    responses_data = ResponseBulkSerializer(many=True, write_only=True)

    class Meta:
        model = ResponseSet
        fields = ['id', 'responses_data', 'suicide_risk_triggered', 'suicide_risk_opt_in']
        read_only_fields = ['suicide_risk_triggered', 'suicide_risk_opt_in']

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
            # Lock the parent response set row to prevent concurrent conflicts
            ResponseSet.objects.select_for_update().get(id=instance.id)

            # Clear existing draft responses and replace them
            instance.responses.all().delete()
            
            # Bulk create responses to minimize database hits
            responses_to_create = []
            for item in responses_data:
                q = item.get('question')
                opt = item.get('selected_option')
                responses_to_create.append(Response(
                    response_set=instance,
                    question=q,
                    selected_option=opt,
                    text_value=item.get('text_value'),
                    question_text=q.content if q else None,
                    question_order=q.order if q else None,
                    selected_option_value=opt.numeric_value if opt else None,
                    selected_option_label=opt.label if opt else None
                ))
            Response.objects.bulk_create(responses_to_create)
            
            # Note: We do NOT mark status = 'COMPLETED' or set completed_at
            instance.save()

            # Calculate and save scores on draft saving
            calculate_and_save_scores(instance)

            # Check and trigger risk-protocol alert on draft saving (no participant email yet)
            check_and_trigger_risk_protocol(instance, notify_participant=False)

        return instance
