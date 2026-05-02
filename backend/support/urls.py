from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SupportTicketViewSet

router = DefaultRouter()
router.register(r'tickets', SupportTicketViewSet, basename='supportticket')

urlpatterns = [
    path('', include(router.urls)),
]
