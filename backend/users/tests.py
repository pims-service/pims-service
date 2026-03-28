from django.test import TestCase
from .models import User
from groups.models import Group

class UserModelTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Gratitude")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            group=self.group
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.group.name, "Gratitude")
        self.assertTrue(self.user.check_password("password123"))
