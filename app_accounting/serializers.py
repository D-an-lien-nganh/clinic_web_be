from rest_framework import serializers
from app_treatment.models import Bill, TreatmentRequest, TreatmentSession

# app_product/serializers_debt.py
from rest_framework import serializers
from .models import (
    SupplierProductDebt, ProductDebtDetail,
    SupplierFacilityDebt, FacilityDebtDetail
)

# ---------- PRODUCT DEBT ----------
class SupplierProductDebtSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    total_paid = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()

    class Meta:
        model = SupplierProductDebt
        fields = ["id", "created", "user", "supplier", "supplier_name",
                  "total_amount", "total_paid", "remaining"]
        read_only_fields = ["id", "created", "user", "supplier_name", "total_paid", "remaining"]

    def get_total_paid(self, obj):
        return obj.get_total_paid()

    def get_remaining(self, obj):
        return obj.get_remaining()

    def create(self, validated_data):
        req = self.context.get("request")
        if req and req.user and req.user.is_authenticated:
            validated_data["user"] = req.user
        return super().create(validated_data)


class ProductDebtDetailSerializer(serializers.ModelSerializer):
    supplier = serializers.IntegerField(source="stock_in.supplier_id", read_only=True)
    supplier_name = serializers.CharField(source="stock_in.supplier.name", read_only=True)
    product_name = serializers.CharField(source="stock_in.product.name", read_only=True)

    class Meta:
        model = ProductDebtDetail
        fields = ["id", "created", "user", "code", "method",
                  "stock_in", "supplier", "supplier_name", "product_name",
                  "paid_amount", "note"]
        read_only_fields = ["id", "created", "user", "code",
                            "supplier", "supplier_name", "product_name"]

    def create(self, validated_data):
        req = self.context.get("request")
        if req and req.user and req.user.is_authenticated:
            validated_data["user"] = req.user
        return super().create(validated_data)

# ---------- FACILITY DEBT ----------
class SupplierFacilityDebtSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    total_paid = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()

    class Meta:
        model = SupplierFacilityDebt
        fields = ["id", "created", "user", "supplier", "supplier_name",
                  "total_amount", "total_paid", "remaining"]
        read_only_fields = ["id", "created", "user", "supplier_name", "total_paid", "remaining"]

    def get_total_paid(self, obj):
        return obj.get_total_paid()

    def get_remaining(self, obj):
        return obj.get_remaining()

    def create(self, validated_data):
        req = self.context.get("request")
        if req and req.user and req.user.is_authenticated:
            validated_data["user"] = req.user
        return super().create(validated_data)


class FacilityDebtDetailSerializer(serializers.ModelSerializer):
    supplier = serializers.IntegerField(source="stock_in.supplier_id", read_only=True)
    supplier_name = serializers.CharField(source="stock_in.supplier.name", read_only=True)
    facility_name = serializers.CharField(source="stock_in.facility.name", read_only=True)

    class Meta:
        model = FacilityDebtDetail
        fields = ["id", "created", "user", "code", "method",
                  "stock_in", "supplier", "supplier_name", "facility_name",
                  "paid_amount", "note"]
        read_only_fields = ["id", "created", "user", "code",
                            "supplier", "supplier_name", "facility_name"]

    def create(self, validated_data):
        req = self.context.get("request")
        if req and req.user and req.user.is_authenticated:
            validated_data["user"] = req.user
        return super().create(validated_data)

class TreatmentSessionAccountingSerializer(serializers.ModelSerializer):
    service_name = serializers.ReadOnlyField(source='service.name', read_only=True)
    floor_name = serializers.ReadOnlyField(source='floor.name', read_only=True)
    class Meta:
        model = TreatmentSession
        fields = ['id', 'service_name', 'floor_name', 'is_done']

class TreatmentRequestAccountingSerializer(serializers.ModelSerializer):
    service_name = serializers.ReadOnlyField(source='service.name', read_only=True)
    treatment_sessions_details = TreatmentSessionAccountingSerializer(many=True, source="treatment_sessions" , read_only=True)
    class Meta:
        model = TreatmentRequest
        fields = ['id', 'code', 'service_name', 'is_done', 'treatment_sessions_details']




class BillAccountingSerializer(serializers.ModelSerializer):
    treatment_requests = TreatmentRequestAccountingSerializer(many=True,source='treatment_request', read_only=True)
    customer_info = serializers.SerializerMethodField()
    class Meta:
        model = Bill
        fields = ['id', 'code', 'customer_info', 'treatment_requests']
    def get_customer_info(self, obj):
        if obj.booking and obj.booking.customer:
            customer = obj.booking.customer
            customer_info = {
                'name': customer.name,
                'email': customer.email,
                'mobile': customer.mobile
            }
            return customer_info
        return None