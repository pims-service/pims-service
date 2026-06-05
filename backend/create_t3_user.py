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

def create_t3_user():
    username = "tester_t3"
    email = "tester_t3@pims.local"
    password = "password123"
    
    # 1. Clean existing user if any
    User.objects.filter(username=username).delete()
    
    role, _ = Role.objects.get_or_create(name='Participant')
    group = Group.objects.first() # Assign any group
    
    now = timezone.now()
    onboarding_completed = now - timedelta(days=190)
    t1_completed = now - timedelta(days=181)
    t2_completed = now - timedelta(days=91)
    
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        role=role,
        group=group,
        has_completed_sociodemographic=True,
        onboarding_completed_at=onboarding_completed,
        has_completed_posttest=True,
        posttest_completed_at=t1_completed
    )
    
    # Get the questionnaires
    sociodemographic_q = Questionnaire.objects.get(assessment_type='SOCIODEMOGRAPHIC')
    psychometric_q = Questionnaire.objects.get(assessment_type='PSYCHOMETRIC')
    
    # Create completed ResponseSets
    # 1. Sociodemographic
    ResponseSet.objects.create(
        user=user,
        questionnaire=sociodemographic_q,
        status='COMPLETED',
        completed_at=onboarding_completed
    )
    
    # 2. SIGNUP milestone (psychometric)
    ResponseSet.objects.create(
        user=user,
        questionnaire=psychometric_q,
        status='COMPLETED',
        milestone='SIGNUP',
        completed_at=onboarding_completed
    )
    
    # 3. 7_DAYS milestone
    ResponseSet.objects.create(
        user=user,
        questionnaire=psychometric_q,
        status='COMPLETED',
        milestone='7_DAYS',
        completed_at=t1_completed
    )
    
    # 4. 3_MONTHS milestone
    ResponseSet.objects.create(
        user=user,
        questionnaire=psychometric_q,
        status='COMPLETED',
        milestone='3_MONTHS',
        completed_at=t2_completed
    )
    
    # Clear caches
    cache.clear()
    
    # Re-fetch user to print properties
    user = User.objects.get(username=username)
    print(f"Successfully created user: {username}")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"Current Experiment Day: {user.current_experiment_day}")
    print(f"Due Milestone: {user.get_due_milestone}")

if __name__ == '__main__':
    create_t3_user()
