from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'app_home'
router = DefaultRouter()

router.register(r'position', views.PositionViewSet, basename='position')
router.register(r'department', views.DepartmentViewSet, basename='department')
router.register(r'floor', views.FloorViewSet, basename='floor')

router.register(r'protocol', views.ProtocolViewSet, basename='protocol')
router.register(r'commission', views.CommissionViewSet, basename='commission')
router.register(r'discount', views.DiscountViewSet, basename='discount')
router.register(r'lead-source', views.LeadSourceViewSet, basename='lead-source')
router.register(r'time-frame', views.TimeFrameViewSet, basename='time-frame')
router.register(r'unit', views.UnitViewSet, basename='unit')

router.register(r'treatment-packages', views.TreatmentPackageViewSet, basename='treatmentpackage')
router.register(r'test-services', views.TestServiceViewSet, basename='test-service')

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/user-login/', views.userlogin, name='user-login'),
    path('v1/change-password/', views.change_password),
    path('v1/update-profile/', views.update_profile),
    # path('v1/password-reset-request/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    # path('v1/password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path("v1/get-available-functions/", views.get_available_functions),
    path("v1/get-all-functions/", views.get_all_functions),
    path("v1/get-all-users/", views.get_user_list),
    path('v1/user-account/', views.UserAccountView.as_view(), name='user_account'),
    path('v1/user-account/unlock-account/', views.activate_account, name='unlock-account'),

]