from rest_framework import serializers
from .models import Questionnaire, Question, Option, ResponseSet, Response

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'label', 'numeric_value', 'order']

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'content', 'type', 'order', 'required', 'options']

class QuestionnaireSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Questionnaire
        fields = ['id', 'title', 'description', 'is_active', 'max_completion_time', 'questions']

class ResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Response
        fields = ['id', 'question', 'selected_option', 'text_value']

class ResponseSetSerializer(serializers.ModelSerializer):
    responses = ResponseSerializer(many=True, read_only=True)

    class Meta:
        model = ResponseSet
        fields = ['id', 'user', 'questionnaire', 'status', 'started_at', 'completed_at', 'responses']
        read_only_fields = ['user', 'started_at']
