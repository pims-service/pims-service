from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # App APIs
    path('api/admin/tools/', include('admin_tools.urls')),
    path('api/users/', include('users.urls')),
    path('api/groups/', include('groups.urls')),
    path('api/phases/', include('phases.urls')),
    path('api/activities/', include('activities.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/questionnaires/', include('questionnaires.urls')),

    # Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
