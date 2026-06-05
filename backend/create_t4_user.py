import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Role
from groups.models import Group
from django.core.cache import cache
from questionnaires.models import Questionnaire, ResponseSet

User = get_user_model()

def create_t4_user():
    username = "tester_t4"
    email = "tester_t4@pims.local"
    password = "password123"

    User.objects.filter(username=username).delete()

    role, _ = Role.objects.get_or_create(name='Participant')
    group = Group.objects.first()

    now = timezone.now()
    onboarding_completed = now - timedelta(days=380)
    t1_completed = now - timedelta(days=372)
    t2_completed = now - timedelta(days=280)
    t3_completed = now - timedelta(days=190)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role,
        group=group,
        has_completed_sociodemographic=True,
        onboarding_completed_at=onboarding_completed,
        has_completed_posttest=True,
        posttest_completed_at=t1_completed,
    )

    sociodemographic_q = Questionnaire.objects.get(assessment_type='SOCIODEMOGRAPHIC')
    psychometric_q = Questionnaire.objects.get(assessment_type='PSYCHOMETRIC')

    ResponseSet.objects.create(
        user=user,
        questionnaire=sociodemographic_q,
        status='COMPLETED',
        completed_at=onboarding_completed,
    )

    for milestone, completed_at in [
        ('SIGNUP', onboarding_completed),
        ('7_DAYS', t1_completed),
        ('3_MONTHS', t2_completed),
        ('6_MONTHS', t3_completed),
    ]:
        ResponseSet.objects.create(
            user=user,
            questionnaire=psychometric_q,
            status='COMPLETED',
            milestone=milestone,
            completed_at=completed_at,
        )

    cache.clear()

    user = User.objects.get(username=username)
    print(f"Successfully created user: {username}")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"Current Experiment Day: {user.current_experiment_day}")
    print(f"Due Milestone: {user.get_due_milestone}")

if __name__ == '__main__':
    create_t4_user()
