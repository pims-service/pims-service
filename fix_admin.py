from users.models import User, Role
role, _ = Role.objects.get_or_create(name='Admin')
u = User.objects.get(username='admin')
u.role = role
u.save()
print('Fixed admin role')
