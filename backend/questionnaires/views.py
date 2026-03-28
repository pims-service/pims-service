from rest_framework import generics, permissions
from .models import Questionnaire, QuestionnaireResponse
from .serializers import QuestionnaireSerializer, QuestionnaireResponseSerializer

class QuestionnaireDetailView(generics.RetrieveAPIView):
    queryset = Questionnaire.objects.all()
    serializer_class = QuestionnaireSerializer
    permission_classes = (permissions.IsAuthenticated,)

class ResponseCreateView(generics.CreateAPIView):
    serializer_class = QuestionnaireResponseSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
