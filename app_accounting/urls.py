from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter

app_name = 'app_accounting'
router = DefaultRouter()

router.register(r"supplier-product-debts", SupplierProductDebtViewSet, basename="supplier-product-debt")
router.register(r"product-debt-details", ProductDebtDetailViewSet, basename="product-debt-detail")
router.register(r"supplier-facility-debts", SupplierFacilityDebtViewSet, basename="supplier-facility-debt")
router.register(r"facility-debt-details", FacilityDebtDetailViewSet, basename="facility-debt-detail")

router.register(r'unrealized-revenue', BillAccountingViewSet, basename='unrealized-revenue')

urlpatterns = [
    path('v1/', include(router.urls)),
]