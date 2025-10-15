from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'app_hr'
router = DefaultRouter()

router.register(r'hr-management', views.HrUserProfileViewSet, basename='hr-management')

urlpatterns = [
    path('v1/', include(router.urls)),
    path("v1/get-collaborators-list/", views.get_collaborator_list),
    
    # ✅ API: danh sách tất cả CTV + tổng doanh thu
    path("v1/collaborators/revenues/", views.CollaboratorRevenueListAPI.as_view(), name="collaborator-revenues"),

    # ✅ API: chi tiết khách hàng theo 1 CTV
    path("v1/collaborators/<int:user_id>/customers/", views.CollaboratorCustomerDetailAPI.as_view(), name="collaborator-customer-detail"),

    path('v1/actor-leadsource-performance/', views.ActorLeadSourcePerformanceAPI.as_view(), name='actor-leadsource-performance'),

    path('v1/actor/<int:user_id>/customers/', views.ActorCustomerDetailAPI.as_view(), name='actor-customer-detail'),
]