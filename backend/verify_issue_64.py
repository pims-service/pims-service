import os
import django
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from questionnaires.models import Questionnaire, Question, Option, ResponseSet, Response
from django.utils import timezone
from rest_framework.test import APIClient

User = get_user_model()

def verify():
    client = APIClient()
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    username = f'tester_{timestamp}'
    email = f'tester_{timestamp}@example.com'

    # 1. Register a new user (via direct create to simulate registration)
    user = User.objects.create_user(
        username=username,
        email=email,
        password='password123'
    )
    print(f"User '{username}' created. Initial Group: {user.group}")
    assert user.group is None, "User should not have a group yet."

    # 2. Get the Baseline Questionnaire
    q = Questionnaire.objects.get(is_baseline=True)
    print(f"Using Baseline Questionnaire: {q.id}")

    # 3. Create a ResponseSet (DRAFT)
    rs = ResponseSet.objects.create(user=user, questionnaire=q, status='DRAFT')
    print(f"Created ResponseSet: {rs.id}")

    # 4. Prepare bulk submission payload
    responses_data = []
    for question in q.questions.all():
        if question.type != 'TEXT':
            opt = question.options.first()
            if opt:
                responses_data.append({
                    "question_id": question.id,
                    "selected_option_id": opt.id
                })
        else:
            responses_data.append({
                "question_id": question.id,
                "text_value": "Automated verification test."
            })

    # 5. Perform the submission via API (to test view + serializer logic)
    client.force_authenticate(user=user)
    payload = {"responses_data": responses_data}
    url = f'/api/questionnaires/response-sets/{rs.id}/submit/'
    
    print(f"Submitting to {url}...")
    response = client.post(url, payload, format='json')
    
    if response.status_code != 200:
        print(f"ERROR: Submission failed with status {response.status_code}")
        print(response.data)
        return

    # 6. Final verification
    user.refresh_from_db()
    rs.refresh_from_db()
    
    print(f"Final ResponseSet Status: {rs.status}")
    print(f"Final User Group: {user.group}")

    assert rs.status == 'COMPLETED', "ResponseSet should be marked as COMPLETED."
    assert user.group is not None, "User should have been assigned to a group."
    print("\nVERIFICATION SUCCESSFUL: Issue #64 implementation is functionally correct.")

if __name__ == "__main__":
    try:
        verify()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"VERIFICATION FAILED: {e}")
