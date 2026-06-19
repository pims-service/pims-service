import pytest
import logging
from django.core import mail
from django.core.management import call_command
from django.core.cache import cache
from django.contrib.auth import get_user_model
from questionnaires.models import Questionnaire, Question, Option, ResponseSet, Response
from questionnaires.serializers import ResponseSetSubmitSerializer, ResponseSetDraftSerializer
from notifications.models import Notification

User = get_user_model()

@pytest.fixture(autouse=True)
def clear_caches():
    cache.clear()

@pytest.fixture
def seeded_db(db):
    call_command('seed_longitudinal_scales')
    return True

@pytest.fixture
def participant_user(db):
    from users.models import Role
    role, _ = Role.objects.get_or_create(name='Participant')
    return User.objects.create_user(
        username='participant',
        email='p@test.com',
        password='password123',
        role=role,
        has_completed_sociodemographic=True
    )

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username='admin_staff',
        email='admin@test.com',
        password='password123',
        is_staff=True
    )

@pytest.mark.django_db
def test_phq9_seeding(seeded_db):
    battery = Questionnaire.objects.get(title="Longitudinal Psychometric Scales")
    # Filter only SCALE questions (skip TEXT header)
    phq_questions = Question.objects.filter(
        questionnaire=battery, content__icontains="[PHQ-9]", type="SCALE"
    ).order_by('order')
    
    assert phq_questions.count() == 9
    
    # Check order is 25 to 33  (header TEXT is at 24)
    orders = [q.order for q in phq_questions]
    assert orders == list(range(25, 34))
    
    # Check the 9th item contains thoughts of suicide/death text and has bilingual option labels
    item_9 = phq_questions[8]
    assert "Thoughts that you would be better off dead" in item_9.content
    assert "ذہن میں اس خیال کا بار بار آنا کہ زندہ رہنے سے مر جانا بہتر ہے" in item_9.content
    
    options = item_9.options.all().order_by('numeric_value')
    assert options.count() == 4
    assert options[0].label == "0 - Not at all | بالکل نہیں"
    assert options[3].label == "3 - Nearly every day | تقریباً روزانہ"

@pytest.mark.django_db
def test_phq9_item9_zero_no_alert(seeded_db, participant_user, admin_user):
    battery = Questionnaire.objects.get(title="Longitudinal Psychometric Scales")
    item_9 = Question.objects.filter(questionnaire=battery, content__icontains="dead").first()
    zero_option = Option.objects.get(question=item_9, numeric_value=0)
    
    response_set = ResponseSet.objects.create(
        user=participant_user,
        questionnaire=battery,
        status='DRAFT'
    )
    
    # Construct submission payload
    responses_payload = []
    for question in battery.questions.all():
        if question == item_9:
            responses_payload.append({
                "question_id": str(question.id),
                "selected_option_id": str(zero_option.id)
            })
        elif question.type == 'SCALE':
            opt = question.options.first()
            responses_payload.append({
                "question_id": str(question.id),
                "selected_option_id": str(opt.id)
            })
            
    serializer = ResponseSetSubmitSerializer(instance=response_set, data={"responses_data": responses_payload})
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    
    # Verify no Notification is created for admin_user
    assert Notification.objects.filter(user=admin_user).count() == 0

@pytest.mark.django_db
def test_phq9_item9_risk_triggers_alert(seeded_db, participant_user, admin_user, caplog):
    battery = Questionnaire.objects.get(title="Longitudinal Psychometric Scales")
    item_9 = Question.objects.filter(questionnaire=battery, content__icontains="dead").first()
    risk_option = Option.objects.get(question=item_9, numeric_value=2) # Score 2 >= 1
    
    response_set = ResponseSet.objects.create(
        user=participant_user,
        questionnaire=battery,
        status='DRAFT'
    )
    
    responses_payload = []
    for question in battery.questions.all():
        if question == item_9:
            responses_payload.append({
                "question_id": str(question.id),
                "selected_option_id": str(risk_option.id)
            })
        elif question.type == 'SCALE':
            opt = question.options.first()
            responses_payload.append({
                "question_id": str(question.id),
                "selected_option_id": str(opt.id)
            })
            
    with caplog.at_level(logging.CRITICAL):
        serializer = ResponseSetSubmitSerializer(instance=response_set, data={"responses_data": responses_payload})
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        
    # Check logger critical output
    critical_logs = [record for record in caplog.records if record.levelname == 'CRITICAL']
    assert len(critical_logs) == 1
    assert "RISK PROTOCOL ALERT" in critical_logs[0].message
    assert "participant" in critical_logs[0].message
    assert "score 2" in critical_logs[0].message

    # Verify a notification is created for the staff user
    notifications = Notification.objects.filter(user=admin_user)
    assert notifications.count() == 1
    assert "CRITICAL SAFETY ALERT" in notifications[0].message
    assert "participant" in notifications[0].message

@pytest.mark.django_db
def test_phq9_item9_spam_prevention(seeded_db, participant_user, admin_user):
    battery = Questionnaire.objects.get(title="Longitudinal Psychometric Scales")
    item_9 = Question.objects.filter(questionnaire=battery, content__icontains="dead").first()
    risk_option = Option.objects.get(question=item_9, numeric_value=2)
    
    response_set = ResponseSet.objects.create(
        user=participant_user,
        questionnaire=battery,
        status='DRAFT'
    )
    
    responses_payload = []
    for question in battery.questions.all():
        if question == item_9:
            responses_payload.append({
                "question_id": str(question.id),
                "selected_option_id": str(risk_option.id)
            })
        elif question.type == 'SCALE':
            opt = question.options.first()
            responses_payload.append({
                "question_id": str(question.id),
                "selected_option_id": str(opt.id)
            })
            
    # First draft save
    draft_serializer = ResponseSetDraftSerializer(instance=response_set, data={"responses_data": responses_payload})
    assert draft_serializer.is_valid(), draft_serializer.errors
    draft_serializer.save()
    
    assert Notification.objects.filter(user=admin_user).count() == 1
    
    # Second draft save (should NOT trigger a duplicate notification)
    draft_serializer2 = ResponseSetDraftSerializer(instance=response_set, data={"responses_data": responses_payload})
    assert draft_serializer2.is_valid(), draft_serializer2.errors
    draft_serializer2.save()
    
    assert Notification.objects.filter(user=admin_user).count() == 1


@pytest.mark.django_db
def test_battery_scoring_and_sidas_risk_triggers(seeded_db, participant_user, admin_user, caplog):
    battery = Questionnaire.objects.get(title="Longitudinal Psychometric Scales")
    questions = battery.questions.all().order_by('order')
    
    # Construct base response set
    response_set = ResponseSet.objects.create(
        user=participant_user,
        questionnaire=battery,
        status='DRAFT'
    )
    
    # Scenario A: Answers that do not trigger risk protocol, with SIDAS item 1 = 0
    responses_payload = []
    for q in questions:
        # Skip TEXT-type header questions (no options)
        if q.type == 'TEXT':
            continue
        # Determine numeric value based on question order
        val = 0
        if 1 <= q.order <= 23:
            if q.order == 11:
                val = 2
            else:
                val = 5
        elif 25 <= q.order <= 33:
            if q.order == 33:
                val = 0 # PHQ-9 Item 9 must be 0 to not trigger safety protocol
            else:
                val = 1 # PHQ-9
        elif 35 <= q.order <= 41:
            val = 2 # GAD-7
        elif q.order in [45, 46, 49, 51]:
            val = 3 # PANAS PA
        elif q.order in [43, 44, 47, 48, 50]:
            val = 1 # PANAS NA
        elif 52 <= q.order <= 65:
            val = 2 # Gratitude GtO
        elif 66 <= q.order <= 77:
            val = 3 # Gratitude GtA
        elif q.order == 78:
            val = 0 # SIDAS Item 1
        elif 79 <= q.order <= 82:
            val = 0 # rest of SIDAS
            
        opt = Option.objects.filter(question=q, numeric_value=val).first()
        assert opt is not None, f"Option for question {q.order} with value {val} not found."
        responses_payload.append({
            "question_id": str(q.id),
            "selected_option_id": str(opt.id)
        })
        
    serializer = ResponseSetSubmitSerializer(instance=response_set, data={"responses_data": responses_payload})
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    
    # Reload and assert scores
    response_set.refresh_from_db()
    scores = response_set.scores
    
    assert scores['PERMA_P'] == 5.0
    assert scores['PERMA_E'] == 5.0
    assert scores['PERMA_R'] == 5.0
    assert scores['PERMA_M'] == 5.0
    assert scores['PERMA_A'] == 5.0
    assert scores['PERMA_N'] == 5.0
    assert scores['PERMA_H'] == 5.0
    assert scores['PERMA_LON'] == 2.0
    assert scores['PERMA_OVERALL'] == 5.0
    
    assert scores['PHQ9_TOTAL'] == 8
    assert scores['GAD7_TOTAL'] == 14
    assert scores['PANAS_PA'] == 12
    assert scores['PANAS_NA'] == 5
    assert scores['GRAT_GTO'] == 28
    assert scores['GRAT_GTA'] == 36
    assert scores['GRAT_TOTAL'] == 64
    
    # Since SIDAS Item 1 was 0, total must be 0
    assert scores['SIDAS_TOTAL'] == 0
    
    # No risk notification should be triggered
    assert Notification.objects.filter(user=admin_user).count() == 0

    # Scenario B: SIDAS Item 1 > 0 with custom answers (test reverse scoring)
    cache.clear()
    response_set_2 = ResponseSet.objects.create(
        user=participant_user,
        questionnaire=battery,
        status='DRAFT'
    )
    
    responses_payload_2 = []
    for q in questions:
        # Skip TEXT-type header questions (no options)
        if q.type == 'TEXT':
            continue
        val = 0
        if 1 <= q.order <= 77:
            val = 0
        elif q.order == 78:
            val = 2 # SIDAS Item 1
        elif q.order == 79:
            val = 3 # SIDAS Item 2 (control) -> reverse scored to 7
        elif q.order == 80:
            val = 0 # SIDAS Item 3 (closeness to attempt) -> 0 means no trigger
        elif q.order == 81:
            val = 1 # SIDAS Item 4
        elif q.order == 82:
            val = 2 # SIDAS Item 5
            
        opt = Option.objects.filter(question=q, numeric_value=val).first()
        responses_payload_2.append({
            "question_id": str(q.id),
            "selected_option_id": str(opt.id)
        })
        
    serializer_2 = ResponseSetSubmitSerializer(instance=response_set_2, data={"responses_data": responses_payload_2})
    assert serializer_2.is_valid(), serializer_2.errors
    serializer_2.save()
    
    response_set_2.refresh_from_db()
    # SIDAS_TOTAL = 2 + (10 - 3) + 0 + 1 + 2 = 12
    assert response_set_2.scores['SIDAS_TOTAL'] == 12
    assert Notification.objects.filter(user=admin_user).count() == 0

    # Scenario C: SIDAS Item 3 > 0 (Risk trigger)
    cache.clear()
    response_set_3 = ResponseSet.objects.create(
        user=participant_user,
        questionnaire=battery,
        status='DRAFT'
    )
    responses_payload_3 = []
    for q in questions:
        # Skip TEXT-type header questions (no options)
        if q.type == 'TEXT':
            continue
        val = 0
        if q.order == 78:
            val = 2
        elif q.order == 80:
            val = 1 # Closeness to suicide attempt > 0
            
        opt = Option.objects.filter(question=q, numeric_value=val).first()
        responses_payload_3.append({
            "question_id": str(q.id),
            "selected_option_id": str(opt.id)
        })
        
    import logging
    with caplog.at_level(logging.CRITICAL):
        serializer_3 = ResponseSetSubmitSerializer(instance=response_set_3, data={"responses_data": responses_payload_3})
        assert serializer_3.is_valid(), serializer_3.errors
        serializer_3.save()
        
    assert any("RISK PROTOCOL ALERT" in r.message for r in caplog.records if r.levelname == 'CRITICAL')
    assert Notification.objects.filter(user=admin_user).count() == 1
    assert "closeness to suicide attempt" in Notification.objects.filter(user=admin_user).first().message.lower()

    # Scenario D: SIDAS Total >= 21 (Risk trigger)
    cache.clear()
    Notification.objects.all().delete()
    
    response_set_4 = ResponseSet.objects.create(
        user=participant_user,
        questionnaire=battery,
        status='DRAFT'
    )
    responses_payload_4 = []
    for q in questions:
        # Skip TEXT-type header questions (no options)
        if q.type == 'TEXT':
            continue
        val = 0
        if q.order == 78:
            val = 5 # Item 1
        elif q.order == 79:
            val = 2 # Item 2 -> reverse scored to 8
        elif q.order == 80:
            val = 0 # Item 3
        elif q.order == 81:
            val = 5 # Item 4
        elif q.order == 82:
            val = 5 # Item 5
            
        # Total = 5 + 8 + 0 + 5 + 5 = 23 >= 21
        opt = Option.objects.filter(question=q, numeric_value=val).first()
        responses_payload_4.append({
            "question_id": str(q.id),
            "selected_option_id": str(opt.id)
        })
        
    serializer_4 = ResponseSetSubmitSerializer(instance=response_set_4, data={"responses_data": responses_payload_4})
    assert serializer_4.is_valid(), serializer_4.errors
    serializer_4.save()
    
    response_set_4.refresh_from_db()
    assert response_set_4.scores['SIDAS_TOTAL'] == 23
    assert Notification.objects.filter(user=admin_user).count() == 1
    assert "high suicide risk" in Notification.objects.filter(user=admin_user).first().message.lower()


@pytest.mark.django_db(transaction=True)
def test_suicide_risk_protocol_opt_in_flow(seeded_db, participant_user, admin_user):
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=participant_user)
    
    battery = Questionnaire.objects.get(title="Longitudinal Psychometric Scales")
    item_9 = Question.objects.filter(questionnaire=battery, content__icontains="dead").first()
    risk_option = Option.objects.get(question=item_9, numeric_value=2) # Score 2 >= 1
    
    response_set = ResponseSet.objects.create(
        user=participant_user,
        questionnaire=battery,
        status='DRAFT'
    )
    
    responses_payload = []
    for question in battery.questions.all():
        if question == item_9:
            responses_payload.append({
                "question_id": str(question.id),
                "selected_option_id": str(risk_option.id)
            })
        elif question.type == 'SCALE':
            opt = question.options.first()
            responses_payload.append({
                "question_id": str(question.id),
                "selected_option_id": str(opt.id)
            })
            
    # Submit via API
    url = f"/api/questionnaires/response-sets/{response_set.id}/submit/"
    response = client.post(url, {"responses_data": responses_payload}, format='json')
    assert response.status_code == 200
    
    # Check that response data flags suicide risk
    assert response.data['suicide_risk_triggered'] is True
    
    # Reload and assert ResponseSet model fields
    response_set.refresh_from_db()
    assert response_set.suicide_risk_triggered is True
    assert response_set.suicide_risk_opt_in is None
    
    # Verify participant support email and whatsapp notification
    participant_emails = [m for m in mail.outbox if participant_user.email in m.to]
    assert len(participant_emails) == 1
    assert 'Support resources are available' in participant_emails[0].subject

    participant_notifications = Notification.objects.filter(user=participant_user)
    assert not participant_notifications.filter(n_type='email').exists()
    assert participant_notifications.filter(n_type='whatsapp').exists()
    
    # Post to opt-in endpoint
    opt_in_url = f"/api/questionnaires/response-sets/{response_set.id}/opt-in/"
    opt_in_res = client.post(opt_in_url, {"opt_in": True}, format='json')
    assert opt_in_res.status_code == 200
    assert opt_in_res.data['suicide_risk_opt_in'] is True
    
    # Reload and check database
    response_set.refresh_from_db()
    assert response_set.suicide_risk_opt_in is True


@pytest.mark.django_db
def test_duplicate_response_set_prevention(seeded_db, participant_user):
    from rest_framework.test import APIClient
    client = APIClient()
    client.force_authenticate(user=participant_user)
    
    battery = Questionnaire.objects.get(title="Longitudinal Psychometric Scales")
    
    # Create the first response set (COMPLETED)
    ResponseSet.objects.create(
        user=participant_user,
        questionnaire=battery,
        milestone='SIGNUP',
        status='COMPLETED'
    )
    
    # Try to create another one via POST
    url = "/api/questionnaires/response-sets/"
    response = client.post(url, {
        "questionnaire": str(battery.id),
        "milestone": "SIGNUP"
    }, format='json')
    
    assert response.status_code == 400
    assert "already completed" in response.data['detail'].lower()

