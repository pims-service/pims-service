from django.contrib.auth import get_user_model
from questionnaires.models import ResponseSet
User = get_user_model()
users = User.objects.filter(response_sets__milestone='SIGNUP', response_sets__status='COMPLETED')
for u in users:
    rs = ResponseSet.objects.filter(user=u, milestone='SIGNUP', status='COMPLETED').first()
    u.has_completed_baseline = True
    u.baseline_completed_at = rs.completed_at
    u.save(update_fields=['has_completed_baseline', 'baseline_completed_at'])

socio_users = User.objects.filter(response_sets__questionnaire__assessment_type='SOCIODEMOGRAPHIC', response_sets__status='COMPLETED')
socio_users.update(has_completed_sociodemographic=True)
print("Restored data")
