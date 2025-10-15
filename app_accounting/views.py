from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from app_home.pagination import CustomPagination
# app_product/views_debt.py
from rest_framework import viewsets, permissions

from app_treatment.models import Bill
from .models import (
    SupplierProductDebt, ProductDebtDetail,
    SupplierFacilityDebt, FacilityDebtDetail
)
from .serializers import (
    BillAccountingSerializer, SupplierProductDebtSerializer, ProductDebtDetailSerializer,
    SupplierFacilityDebtSerializer, FacilityDebtDetailSerializer
)
from .docs import *
@extend_schema(tags=["app_accounting"])
@supplier_product_debt_schema_view()
class SupplierProductDebtViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierProductDebtSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = SupplierProductDebt.objects.select_related("supplier", "user")
        supplier_id = self.request.query_params.get("supplier")
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        return qs.order_by("-id")

@extend_schema(tags=["app_accounting"])
@product_debt_detail_schema_view()
class ProductDebtDetailViewSet(viewsets.ModelViewSet):
    serializer_class = ProductDebtDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # chỉ lấy detail của StockIn product (product != null, facility == null)
        qs = (ProductDebtDetail.objects
              .select_related("stock_in", "stock_in__supplier", "stock_in__product", "user")
              .filter(stock_in__product__isnull=False, stock_in__facility__isnull=True))

        qp = self.request.query_params
        if qp.get("supplier"): qs = qs.filter(stock_in__supplier_id=qp["supplier"])
        if qp.get("product"):  qs = qs.filter(stock_in__product_id=qp["product"])
        if qp.get("stock_in"): qs = qs.filter(stock_in_id=qp["stock_in"])
        if qp.get("method"):   qs = qs.filter(method=qp["method"])
        return qs.order_by("-id")

@extend_schema(tags=["app_accounting"])
@supplier_facility_debt_schema_view()
class SupplierFacilityDebtViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierFacilityDebtSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = SupplierFacilityDebt.objects.select_related("supplier", "user")
        supplier_id = self.request.query_params.get("supplier")
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        return qs.order_by("-id")

@extend_schema(tags=["app_accounting"])
@facility_debt_detail_schema_view()
class FacilityDebtDetailViewSet(viewsets.ModelViewSet):
    serializer_class = FacilityDebtDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # chỉ lấy detail của StockIn facility (facility != null, product == null)
        qs = (FacilityDebtDetail.objects
              .select_related("stock_in", "stock_in__supplier", "stock_in__facility", "user")
              .filter(stock_in__facility__isnull=False, stock_in__product__isnull=True))

        qp = self.request.query_params
        if qp.get("supplier"): qs = qs.filter(stock_in__supplier_id=qp["supplier"])
        if qp.get("facility"): qs = qs.filter(stock_in__facility_id=qp["facility"])
        if qp.get("stock_in"): qs = qs.filter(stock_in_id=qp["stock_in"])
        if qp.get("method"):   qs = qs.filter(method=qp["method"])
        return qs.order_by("-id")

@extend_schema(tags=["app_accounting"])
class BillAccountingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bill.objects.all()
    pagination_class = CustomPagination
    serializer_class = BillAccountingSerializer
    permission_classes = [IsAuthenticated]