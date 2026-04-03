from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Role, UserConsent
from django.utils import timezone

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
            'whatsapp_number', 'role', 'role_name', 
            'group', 'group_name', 'traits', 'created_at'
        )
        read_only_fields = ('created_at',)

class SignupSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for the user registration flow.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    consent_agreed = serializers.BooleanField(write_only=True, required=True)
    consent_version = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'username', 'full_name', 'email', 'password', 
            'confirm_password', 'whatsapp_number', 
            'consent_agreed', 'consent_version'
        )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        if not attrs.get('consent_agreed'):
            raise serializers.ValidationError({"consent_agreed": "You must agree to the terms and conditions."})
            
        return attrs

    def create(self, validated_data):
        # Extract fields not on User model
        validated_data.pop('confirm_password')
        consent_agreed = validated_data.pop('consent_agreed')
        consent_version = validated_data.pop('consent_version')
        
        # Ensure default Role (Participant) exists
        role, _ = Role.objects.get_or_create(
            name='Participant', 
            defaults={'description': 'Default role for experiment participants'}
        )
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', ''),
            whatsapp_number=validated_data.get('whatsapp_number', ''),
            role=role
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
            'role': self.user.role.name if self.user.role else 'Participant'
        }
        
        return data
