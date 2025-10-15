from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'app_product'

router = DefaultRouter()
router.register(r'service', views.ServiceViewSet, basename='service')
router.register(r'product', views.ProductViewSet, basename='product')
router.register(r'maintenance', views.MaintenanceViewSet, basename='maintenance')
router.register(r'fix-schedule', views.FixScheduleViewSet, basename='fix-schedule')
router.register(r'facility', views.FacilityViewSet, basename='facility')
router.register(r"facility-exports", views.FacilityExportViewSet, basename="facility-export")

router.register(r'supplier', views.SupplierViewSet, basename='supplier')
router.register(r'stock-in', views.StockInViewSet, basename='stock-in')
router.register(r'stock-out', views.StockOutViewSet, basename='stock-out')
router.register(r'warehouse', views.WarehouseViewSet, basename='warehouse')
router.register(r'technical-settings', views.TechicalSettingViewSet, basename='technical-settings')

router.register(r'service-treatment-packages', views.ServiceTreatmentPackageViewSet, basename='service-treatment-package')
router.register(r'service-technical-settings', views.ServiceTechnicalSettingViewSet, basename='service-technical-setting')
router.register(r'inventory', views.InventoryViewSet, basename='inventory')

urlpatterns = [
    path('v1/', include(router.urls)),

]
