from rest_framework import generics, permissions
from .models import Phase
from .serializers import PhaseSerializer
from django.utils import timezone

class PhaseListView(generics.ListAPIView):
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer
    permission_classes = (permissions.IsAuthenticated,)

class CurrentPhaseView(generics.RetrieveAPIView):
    serializer_class = PhaseSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        today = timezone.now().date()
        return Phase.objects.filter(start_date__lte=today, end_date__gte=today).first()
