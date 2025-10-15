from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'app_customer'

router = DefaultRouter()
router.register(r'lead-status', views.LeadStatusViewSet, basename='lead-status')
router.register(r'treatment-state', views.TreatmentStateViewSet, basename='treatment-state')
router.register(r'customer-level', views.CustomerLevelViewSet, basename='customer-level')
router.register(r'customer', views.CustomerViewSet, basename='customer')
router.register(r'customer-care', views.CustomerCareViewSet, basename='customer-carecare')
router.register(r'feedback', views.FeedBackViewSet, basename='feedback')
router.register(r'customer-requests', views.CustomerRequestViewSet, basename='customerrequest')
router.register(r'customer-problems', views.CustomerProblemViewSet, basename='customer-problem')
router.register(r'lead-source-actors', views.LeadSourceActorViewSet, basename='lead-source-actors')

urlpatterns = [
    path('v1/', include(router.urls)),
]
