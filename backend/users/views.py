from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import (
    UserSerializer, SignupSerializer, CustomTokenObtainPairSerializer,
    ForgotPasswordRequestSerializer, ResetPasswordSerializer, VerifyResetOTPSerializer
)
from .delete_utils import get_self_delete_confirmation_phrase

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = SignupSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)

class AdminUserUpdateView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)

ADMIN_DELETE_CONFIRMATION = "Confirm Delete"


class AccountSelfDeleteView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        if user.is_superuser:
            return Response(
                {"detail": "Admin accounts cannot be deleted through this action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expected = get_self_delete_confirmation_phrase(user.username)
        confirmation = (request.data.get("confirmation") or "").strip()
        password = request.data.get("password") or ""

        if not password:
            return Response(
                {"detail": "Password is required to delete your account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(password):
            return Response(
                {"detail": "Incorrect password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if confirmation != expected:
            return Response(
                {
                    "detail": (
                        f'You must type "{expected}" exactly to permanently delete your account.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = user.username
        user.delete()
        return Response(
            {"detail": f'Account "{username}" permanently deleted.'},
            status=status.HTTP_200_OK,
        )


class AdminUserDeleteView(APIView):
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request, pk):
        confirmation = (request.data.get("confirmation") or "").strip()
        if confirmation != ADMIN_DELETE_CONFIRMATION:
            return Response(
                {
                    "detail": (
                        f'You must type "{ADMIN_DELETE_CONFIRMATION}" exactly to permanently delete this user.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.pk == request.user.pk:
            return Response(
                {"detail": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_superuser:
            return Response(
                {"detail": "Admin accounts cannot be deleted through this action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = user.username
        user.delete()
        return Response(
            {"detail": f'User "{username}" permanently deleted.'},
            status=status.HTTP_200_OK,
        )

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class SendOTPView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already exists
        from .models import User, EmailVerificationOTP
        if User.objects.filter(email=email).exists():
            return Response({'error': 'User with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)
        
        import random
        # Generate 6 digit OTP
        otp = str(random.randint(100000, 999999))
        
        # Save to DB
        EmailVerificationOTP.objects.create(email=email, otp=otp)
        
        # Send async
        from .tasks import send_otp_email_task
        send_otp_email_task.delay(email, otp)
        
        return Response({'message': 'Verification code sent to your email.'}, status=status.HTTP_200_OK)
        

class HealthCheckView(APIView):
    permission_classes = (permissions.AllowAny,)
    def get(self, request):
        return Response({"status": "ok"})


class ForgotPasswordRequestView(generics.CreateAPIView):
    """
    Triggers password reset flow. Generates and sends OTP if email exists.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = ForgotPasswordRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        user = User.objects.get(email__iexact=email)
        
        # Invalidate any older unused reset codes
        from .models import PasswordResetOTP
        PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
        
        import random
        otp = str(random.randint(100000, 999999))

        # Create OTP record
        PasswordResetOTP.objects.create(user=user, otp=otp)

        # Send OTP email asynchronously
        from .tasks import send_password_reset_email_task
        send_password_reset_email_task.delay(user.email, user.display_name, otp)

        return Response({'message': 'A reset code has been sent to your email.'}, status=status.HTTP_200_OK)


class VerifyResetOTPView(generics.CreateAPIView):
    """
    Verifies reset OTP without updating password.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = VerifyResetOTPSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'message': 'Verification code verified successfully.'}, status=status.HTTP_200_OK)


class ResetPasswordView(generics.CreateAPIView):
    """
    Verifies reset OTP and updates user password.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user_instance
        otp_record = serializer.otp_instance

        # Update password
        user.set_password(serializer.validated_data['password'])
        user.save()

        # Mark OTP as used
        otp_record.is_used = True
        otp_record.save(update_fields=['is_used'])

        return Response({'message': 'Your password has been successfully reset.'}, status=status.HTTP_200_OK)

