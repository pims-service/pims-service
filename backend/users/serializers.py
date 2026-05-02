from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db.models import Count
from django.utils import timezone

from groups.models import Group
from .models import User, Role, UserConsent

class UserSerializer(serializers.ModelSerializer):
    """
    Standard user profile serializer.
    """
    group_name = serializers.ReadOnlyField(source='group.name')
    role_name = serializers.ReadOnlyField(source='role.name')

    class Meta:
        model = User
        fields = (
            'user_id', 'username', 'full_name', 'email', 
            'whatsapp_number', 'date_of_birth', 'role', 'role_name', 
            'group', 'group_name', 'traits', 'created_at',
            'has_completed_baseline',
            'has_completed_posttest', 'is_posttest_due',
            'completion_rate',
        )
        read_only_fields = ('created_at', 'has_completed_baseline', 'has_completed_posttest', 'is_posttest_due', 'completion_rate',)

class SignupSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for the user registration flow.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    consent_agreed = serializers.BooleanField(write_only=True, required=True)
    consent_version = serializers.CharField(write_only=True, required=True)
    otp = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=6)

    group = serializers.PrimaryKeyRelatedField(read_only=True)
    group_name = serializers.ReadOnlyField(source='group.name')

    class Meta:
        model = User
        fields = (
            'username', 'full_name', 'email', 'password', 
            'confirm_password', 'whatsapp_number', 'date_of_birth',
            'consent_agreed', 'consent_version', 'otp',
            'group', 'group_name',
        )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_date_of_birth(self, value):
        if not value:
            raise serializers.ValidationError("Date of birth is mandatory.")
        
        today = timezone.now().date()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        
        if age < 15 or age > 80:
            raise serializers.ValidationError("Age must be between 15 and 80 years old.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        if not attrs.get('consent_agreed'):
            raise serializers.ValidationError({"consent_agreed": "You must agree to the terms and conditions."})
        
        if not attrs.get('date_of_birth'):
            raise serializers.ValidationError({"date_of_birth": "Date of birth is mandatory."})

        # Django built-in password validation
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            # We don't have the user instance yet, but we can pass the data
            validate_password(attrs['password'], user=User(username=attrs.get('username')))
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def create(self, validated_data):
        # Extract fields not on User model
        validated_data.pop('confirm_password')
        consent_agreed = validated_data.pop('consent_agreed')
        consent_version = validated_data.pop('consent_version')
        validated_data.pop('otp', None)
        
        # Ensure default Role (Participant) exists
        role, _ = Role.objects.get_or_create(
            name='Participant', 
            defaults={'description': 'Default role for experiment participants'}
        )
        
        # Create user (Group assignment is now deferred to baseline completion)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', ''),
            whatsapp_number=validated_data.get('whatsapp_number', ''),
            date_of_birth=validated_data.get('date_of_birth'),
            role=role,
        )
        
        # Create consent record
        UserConsent.objects.create(
            user=user,
            agreed=consent_agreed,
            agreed_at=timezone.now(),
            consent_version=consent_version
        )
        
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add extra user information to the response
        data['user'] = {
            'id': self.user.pk,
            'username': self.user.username,
            'email': self.user.email,
            'full_name': self.user.full_name,
            'date_of_birth': self.user.date_of_birth.strftime('%Y-%m-%d') if self.user.date_of_birth else None,
            'role': self.user.role.name if self.user.role else 'Participant',
            'has_completed_baseline': self.user.has_completed_baseline,
            'has_completed_posttest': self.user.has_completed_posttest,
            'is_posttest_due': self.user.is_posttest_due,
        }
        
        return data
