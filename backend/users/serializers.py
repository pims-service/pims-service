from rest_framework import serializers
from .models import User
from groups.models import Group

class UserSerializer(serializers.ModelSerializer):
    group_name = serializers.ReadOnlyField(source='group.name')

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'whatsapp_number', 'email_consent', 'whatsapp_consent', 'group', 'group_name', 'traits', 'registration_date')
        read_only_fields = ('registration_date',)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'whatsapp_number', 'email_consent', 'whatsapp_consent', 'traits')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            whatsapp_number=validated_data.get('whatsapp_number', ''),
            email_consent=validated_data.get('email_consent', False),
            whatsapp_consent=validated_data.get('whatsapp_consent', False),
            traits=validated_data.get('traits', {})
        )
        return user
