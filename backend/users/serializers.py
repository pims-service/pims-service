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
    due_milestone = serializers.CharField(source='get_due_milestone', read_only=True)
    current_experiment_day = serializers.IntegerField(read_only=True, allow_null=True)
    current_activity_wave = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = (
            'user_id', 'username', 'full_name', 'email', 
            'whatsapp_number', 'date_of_birth', 'role', 'role_name', 
            'group', 'group_name', 'traits', 'created_at',
            'has_completed_sociodemographic',
            'has_completed_posttest', 'is_posttest_due', 'due_milestone',
            'current_experiment_day', 'current_activity_wave',
            'has_consecutive_misses', 'consecutive_misses_message',
            'has_two_consecutive_missed_waves', 'is_disqualified',
        )
        read_only_fields = (
            'created_at', 'role', 'group',
            'has_completed_sociodemographic', 'has_completed_posttest',
            'is_posttest_due', 'due_milestone', 'current_experiment_day', 'current_activity_wave',
            'has_consecutive_misses',
            'consecutive_misses_message', 'has_two_consecutive_missed_waves', 'is_disqualified',
        )

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

    def validate_whatsapp_number(self, value):
        if value:
            val = value.strip()
            if User.objects.filter(whatsapp_number=val).exists():
                raise serializers.ValidationError("A user with this WhatsApp number already exists.")
            return val
        return value

    def validate_date_of_birth(self, value):
        if not value:
            raise serializers.ValidationError("Date of birth is mandatory.")
        
        today = timezone.localdate()
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

        # OTP Verification
        if not self.context.get('skip_otp_validation'):
            otp = attrs.get('otp')
            email = attrs.get('email')
            if not otp:
                raise serializers.ValidationError({"otp": "OTP verification code is required."})

            from .models import EmailVerificationOTP
            otp_record = EmailVerificationOTP.objects.filter(
                email=email,
                is_verified=False
            ).order_by('-created_at').first()

            if not otp_record or otp_record.otp != otp:
                raise serializers.ValidationError({"otp": "Invalid verification code."})

            if not otp_record.is_valid():
                raise serializers.ValidationError({"otp": "Verification code has expired."})

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
        otp = validated_data.pop('otp', None)
        
        # Mark OTP as verified
        if otp:
            from .models import EmailVerificationOTP
            EmailVerificationOTP.objects.filter(
                email=validated_data['email'],
                otp=otp
            ).update(is_verified=True)
        
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
        username = attrs.get('username')
        if username:
            from django.db.models import Q
            try:
                user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
                attrs['username'] = user.username
            except User.DoesNotExist:
                pass

        data = super().validate(attrs)
        
        # Safely handle date_of_birth if it's already a string or datetime
        dob = self.user.date_of_birth
        if dob:
            from datetime import date, datetime
            if isinstance(dob, (date, datetime)):
                dob_str = dob.strftime('%Y-%m-%d')
            else:
                dob_str = str(dob)
        else:
            dob_str = None
            
        data['user'] = {
            'id': self.user.pk,
            'username': self.user.username,
            'email': self.user.email,
            'full_name': self.user.full_name,
            'date_of_birth': dob_str,
            'role': self.user.role.name if self.user.role else 'Participant',
            'has_completed_sociodemographic': self.user.has_completed_sociodemographic,
            'has_completed_posttest': self.user.has_completed_posttest,
            'is_posttest_due': self.user.is_posttest_due,
            'due_milestone': self.user.get_due_milestone,
            'is_disqualified': self.user.is_disqualified,
        }
        
        return data


class ForgotPasswordRequestSerializer(serializers.Serializer):
    """
    Validates incoming email for password reset requests.
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class VerifyResetOTPSerializer(serializers.Serializer):
    """
    Validates reset OTP without resetting password.
    """
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email__iexact=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid verification code."})

        from .models import PasswordResetOTP
        otp_record = PasswordResetOTP.objects.filter(
            user=user,
            is_used=False
        ).order_by('-created_at').first()

        if not otp_record or otp_record.otp != attrs['otp']:
            raise serializers.ValidationError({"otp": "Invalid verification code."})

        if not otp_record.is_valid():
            raise serializers.ValidationError({"otp": "Verification code has expired."})

        return attrs


class ResetPasswordSerializer(serializers.Serializer):

    """
    Validates email, OTP, and new password matching during password reset.
    """
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        # Match user
        try:
            user = User.objects.get(email__iexact=attrs['email'])
        except User.DoesNotExist:
            # Mask user existence during reset submission as well for security consistency
            raise serializers.ValidationError({"otp": "Invalid verification code."})

        # Check OTP
        from .models import PasswordResetOTP
        otp_record = PasswordResetOTP.objects.filter(
            user=user,
            is_used=False
        ).order_by('-created_at').first()

        if not otp_record or otp_record.otp != attrs['otp']:
            raise serializers.ValidationError({"otp": "Invalid verification code."})

        if not otp_record.is_valid():
            raise serializers.ValidationError({"otp": "Verification code has expired."})

        # Strength validation
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            validate_password(attrs['password'], user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        # Put user inside validation state for views to retrieve
        self.user_instance = user
        self.otp_instance = otp_record
        return attrs

