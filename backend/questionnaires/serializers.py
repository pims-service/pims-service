from rest_framework import serializers
from .models import Questionnaire, QuestionnaireResponse

class QuestionnaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questionnaire
        fields = '__all__'

class QuestionnaireResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionnaireResponse
        fields = '__all__'
        read_only_fields = ('user', 'submitted_at')
