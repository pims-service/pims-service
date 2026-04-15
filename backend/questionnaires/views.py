from rest_framework import generics, permissions, status
from rest_framework.response import Response as DRFResponse
from .models import Questionnaire, ResponseSet, Response
from .serializers import QuestionnaireSerializer, ResponseSetSerializer

class QuestionnaireListView(generics.ListAPIView):
    queryset = Questionnaire.objects.filter(is_active=True)
    serializer_class = QuestionnaireSerializer
    permission_classes = (permissions.IsAuthenticated,)

class QuestionnaireDetailView(generics.RetrieveAPIView):
    queryset = Questionnaire.objects.all()
    serializer_class = QuestionnaireSerializer
    permission_classes = (permissions.IsAuthenticated,)

class ResponseSetCreateView(generics.CreateAPIView):
    serializer_class = ResponseSetSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
