from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

from .views import ClinicalExaminationViewSet, DiagnosisMedicineViewSet, ExaminationOrderViewSet, TreatmentRequestAPIView, UserServiceStatsListView, ExpertTechniqueDetailAPIView
from .views_payroll import PayrollAPIView
from .views_accounting import RevenueListAPI, ARDetailByCustomerAPI, ARSummaryAPI, UnrealizedRevenueAPI

app_name = 'app_treatment'
router = DefaultRouter()

router.register(r'booking', views.BookingViewSet, basename='booking')
router.register(r'examination-order', ExaminationOrderViewSet, basename='examination-order')
router.register(r'doctor-health-check', views.DoctorHealthCheckViewSet, basename='doctor-health-check')
router.register(r'clinical-examinations', ClinicalExaminationViewSet, basename='clinical-examinations')
router.register(r'doctor-process', views.DoctorProcessViewSet, basename='doctor-process')
router.register(r"diagnosis-medicines", DiagnosisMedicineViewSet, basename="diagnosis-medicine")

router.register(r'service-assign', views.ServiceAssignViewSet, basename='service-assign')
router.register(r'bills', views.BillViewSet)
router.register(r'payment-history', views.PaymentHistoryViewSet, basename='payment-history')
router.register(r'treatment-request', views.TreatmentRequestViewSet)
router.register(r'treatment-session', views.TreatmentSessionViewSet)
router.register(r're_examination',views.ReExaminationViewSet)
router.register(r'billsNeed', views.BillNeedViewSet)
router.register(r'ar-items', views.ARItemViewSet, basename='aritem')

urlpatterns = [
    path('v1/', include(router.urls)),
    path(
        "treatment-requests/<int:pk>/update-is-done/",
        TreatmentRequestAPIView.as_view(),
        name="treatment-request-update-is-done",
    ),
    path("users/service-stats/", UserServiceStatsListView.as_view(), name="user-service-stats-list"),
    path('v1/payroll/', PayrollAPIView.as_view(), name='payroll'),
    path('v1/treatment/payroll/experts/<int:expert_id>/technique-details/',
         ExpertTechniqueDetailAPIView.as_view(),
         name='expert-technique-details'),
    path('v1/revenue/', RevenueListAPI.as_view(), name='revenue'),
    path('v1/ar-detail/', ARDetailByCustomerAPI.as_view(), name='ar-detail'),
    path('v1/ar-summary/', ARSummaryAPI.as_view(), name='ar-summary'),
    path('v1/revenue-unrealized/', UnrealizedRevenueAPI.as_view(), name="revenue-unrealized"),
]
