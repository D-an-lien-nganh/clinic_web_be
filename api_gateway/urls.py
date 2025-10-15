from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

app_name = 'api_gateway'
urlpatterns = [
    path('', include(router.urls)),  # Include the router URLs    
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api-gateway:schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='api_gateway:schema'), name='redoc'),
]
