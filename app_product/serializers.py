from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes

from app_home.models import TreatmentPackage
from .models import REPAIR_STATUS, FacilityExport, Service, Product, Facility, Maintenance, FixSchedule, ServiceTechnicalSetting, ServiceTreatmentPackage, Supplier, StockIn, StockOut, Warehouse,Unit,TechicalSetting
from drf_spectacular.utils import extend_schema_field
class TreatmentPackagePriceSerializer(serializers.Serializer):
    treatment_package_id = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=20, decimal_places=2)
    duration = serializers.IntegerField()
class ServiceTreatmentPackageReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServiceTreatmentPackage
        fields = '__all__'
class ServiceSerializer(serializers.ModelSerializer):
    treatment_packages = TreatmentPackagePriceSerializer(many=True, write_only=True, required=False)
    technical_settings = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    treatment_packages_info = serializers.SerializerMethodField(read_only=True)
    technical_settings_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Service
        fields = ('id', 'code', 'name',  'status',  
                 'type','treatment_packages', 'technical_settings','treatment_packages_info','technical_settings_info')
        read_only_fields = ['id', 'code']

    def get_treatment_packages_info(self, obj):
        result = []
        for stp in obj.service_treatment_packages.select_related('treatment_package').all():
            result.append({
                "id": stp.treatment_package.id,
                "name": stp.treatment_package.name,
                "note": stp.treatment_package.note,
                "price": stp.price,
                "duration": stp.duration
            })
        return result
    def get_technical_settings_info(self, obj):
        return [
            {
                "id": ts.technical_setting.id,
                "name": ts.technical_setting.name,            }
            for ts in obj.service_technical_settings.select_related('technical_setting').all()
        ]

    def create(self, validated_data):
        treatment_packages_data = validated_data.pop('treatment_packages', [])
        technical_settings_data = validated_data.pop('technical_settings', [])
        
        # Tạo service
        service = Service.objects.create(**validated_data)

        # Tạo ServiceTreatmentPackage
        for tp in treatment_packages_data:
            treatment_package = TreatmentPackage.objects.get(id=tp["treatment_package_id"])
            ServiceTreatmentPackage.objects.create(
                service=service,
                treatment_package=treatment_package,
                price=tp["price"],
                duration=tp["duration"]
            )

        # Tạo ServiceTechnicalSetting
        for tech_id in technical_settings_data:
            tech = TechicalSetting.objects.get(id=tech_id)
            ServiceTechnicalSetting.objects.create(
                service=service,
                technical_setting=tech
            )

        return service
    def update(self, instance, validated_data):
        treatment_packages_data = validated_data.pop('treatment_packages', [])
        technical_settings_data = validated_data.pop('technical_settings', [])

        # Update các trường cơ bản của Service
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Xóa tất cả ServiceTreatmentPackage cũ
        instance.service_treatment_packages.all().delete()

        # Tạo lại ServiceTreatmentPackage
        for tp in treatment_packages_data:
            treatment_package = TreatmentPackage.objects.get(id=tp["treatment_package_id"])
            ServiceTreatmentPackage.objects.create(
                service=instance,
                treatment_package=treatment_package,
                price=tp["price"],
                duration=tp["duration"]
            )

        # Xóa tất cả ServiceTechnicalSetting cũ
        instance.service_technical_settings.all().delete()

        # Tạo lại ServiceTechnicalSetting
        for tech_id in technical_settings_data:
            tech = TechicalSetting.objects.get(id=tech_id)
            ServiceTechnicalSetting.objects.create(
                service=instance,
                technical_setting=tech
            )

        return instance

class ProductSerializer(serializers.ModelSerializer):
    unit_name = serializers.ReadOnlyField(source="unit.name")
    product_type_name = serializers.ReadOnlyField(source="product_type.name")
    class Meta:
        model = Product
        fields = ('id', 'code', 'name', 'description', 'effect', 'origin', 'sell_price', 'unit', 'unit_name','product_type', 'product_type_name')
        read_only_fields = ['id', 'code', 'unit_name']
        
class InventorySummarySerializer(serializers.Serializer):
    product_code = serializers.CharField()
    product_name = serializers.CharField()
    unit = serializers.CharField(allow_null=True)
    open_qty = serializers.DecimalField(max_digits=20, decimal_places=2)
    open_val = serializers.DecimalField(max_digits=20, decimal_places=2)
    in_qty = serializers.DecimalField(max_digits=20, decimal_places=2)
    in_val = serializers.DecimalField(max_digits=20, decimal_places=2)
    out_qty = serializers.DecimalField(max_digits=20, decimal_places=2)
    out_val = serializers.DecimalField(max_digits=20, decimal_places=2)
    close_qty = serializers.DecimalField(max_digits=20, decimal_places=2)
    close_val = serializers.DecimalField(max_digits=20, decimal_places=2)

class MaintenanceSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source="facility.name")
    status_name = serializers.SerializerMethodField()
    class Meta:
        model = Maintenance
        fields = ('id', 'date', 'note', 'status','status_name', 'is_maintenanced', 'facility', 'facility_name', )
        read_only_fields = ['id', 'facility_name', 'status_name']
    @extend_schema_field(str)
    def get_status_name(self, obj):
        return dict(REPAIR_STATUS).get(obj.status, obj.status)
class FixScheduleSerializer(serializers.ModelSerializer):
    facility_name = serializers.ReadOnlyField(source="facility.name")
    status_name = serializers.SerializerMethodField()
    class Meta:
        model = FixSchedule
        fields = ('id', 'date', 'note', 'status','status_name', 'is_fixed', 'facility', 'facility_name')
        read_only_fields = ['id', 'facility_name', 'status_name']
    @extend_schema_field(str)
    def get_status_name(self, obj):
        return dict(REPAIR_STATUS).get(obj.status, obj.status)
class FacilitySerializer(serializers.ModelSerializer):
    maintenance_detail = MaintenanceSerializer(source="facility_maintenance",many=True, read_only=True)
    fix_detail = FixScheduleSerializer(source="facility_fixschedule",many=True, read_only=True)
    unit_name = serializers.ReadOnlyField(source="unit.name")
    class Meta:
        model = Facility
        fields = ('id', 'code','name', 'origin', 'quantity', 'import_price','unit', 'status','effect','unit_name', 'is_malfunction', 'malfunction_status',
                  'maintenance_detail', 'fix_detail')
        read_only_fields = ['id', 'maintenance_detail', 'fix_detail', 'unit_name']

class FacilityExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityExport
        fields = [
            "id", "facility",'supplier', "export_type", "quantity", "unit_price",
            "customer", "internal_department", "note",
            "created_by", "created_at", "updated_at", "total_amount"
        ]
        read_only_fields = ["created_by", "created_at", "updated_at", "total_amount"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["created_by"] = request.user
        return super().create(validated_data)

class SupplierSerializer(serializers.ModelSerializer):
    related_products = ProductSerializer(source='get_related_products', many=True, read_only=True)

    class Meta:
        model = Supplier
        fields = [
            'id', 'user', 'name', 'MST', 'contact_person',
            'mobile', 'email', 'address', 'related_products'
        ]
        read_only_fields = ['id', 'created', 'related_products']


class StockInSerializer(serializers.ModelSerializer):
    supplier_name = serializers.ReadOnlyField(source="supplier.name")
    product_name = serializers.ReadOnlyField(source="product.name")
    creator_name = serializers.ReadOnlyField(source="user.username")
    approver_name = serializers.ReadOnlyField(source="approver.username")
    total_price = serializers.SerializerMethodField()
    unit_name = serializers.ReadOnlyField(source="product.unit.name")

    class Meta:
        model = StockIn
        fields = [
            "id","created","code",
            "user","creator_name",
            "supplier", "supplier_name",
            "product","facility","product_name", "unit_name",
            "quantity","import_price","import_date",
            "approver","approver_name","note",
            "total_price"
        ]
        read_only_fields = ["id", "created", "user", "code", "total_price"]
    @extend_schema_field(float)
    def get_total_price(self, obj):
        return obj.get_total()

class StockOutSerializer(serializers.ModelSerializer):
    supplier_name = serializers.ReadOnlyField(source="supplier.name")
    product_name = serializers.ReadOnlyField(source="product.name")
    creator_name = serializers.ReadOnlyField(source="user.username")
    approver_name = serializers.ReadOnlyField(source="approver.username")
    unit_name = serializers.ReadOnlyField(source="product.unit.name")
    customer_name = serializers.ReadOnlyField(source="customer.name")

    # FE: “Thành tiền” (tổng thực tế)
    original_stockout_price = serializers.SerializerMethodField()
    # (tuỳ chọn) tổng gốc để so sánh nội bộ
    base_total_price = serializers.SerializerMethodField()

    class Meta:
        model = StockOut
        fields = [
            'id','created','code',
            'user','creator_name',
            'product','product_name',"unit_name",
            'supplier','supplier_name',
            'customer','customer_name',
            'approver','approver_name',
            'quantity','export_date','type','actual_stockout_price',
            'note','actual_quantity','missing_reason',
            'original_stockout_price','base_total_price'
        ]
        read_only_fields = ["id","created","user","code","actual_quantity","missing_reason","original_stockout_price","base_total_price"]

    @extend_schema_field(OpenApiTypes.NUMBER)
    def get_original_stockout_price(self, obj):
        return obj.original_stockout_price()

    @extend_schema_field(OpenApiTypes.NUMBER)
    def get_base_total_price(self, obj):
        if not obj.product or obj.quantity is None:
            return 0
        return (obj.product.sell_price or 0) * (obj.quantity or 0)
    
    def create(self, validated_data):
        # KHÔNG gọi service trừ kho ở đây nữa
        return StockOut.objects.create(**validated_data)

    # Ràng buộc: nếu type='customer' thì phải có customer
    def validate(self, attrs):
        t = attrs.get('type') or getattr(self.instance, 'type', None)
        customer = attrs.get('customer') if 'customer' in attrs else getattr(self.instance, 'customer', None)
        if t == 'customer' and not customer:
            raise serializers.ValidationError({"customer": "Bắt buộc chọn khách hàng khi Đối tượng xuất là Khách hàng."})
        return attrs
    
class WarehouseSerializer(serializers.ModelSerializer):
    supplier_name = serializers.ReadOnlyField(source="supplier.name")
    product_name = serializers.ReadOnlyField(source="product.name")
    user_name = serializers.ReadOnlyField(source="user.username")
    supplier_code = serializers.ReadOnlyField(source="supplier.code")
    product_code = serializers.ReadOnlyField(source="product.code")
    class Meta:
        model = Warehouse
        fields = [
            'id', 'created', 'code', 'supplier', 'supplier_name', 'supplier_code',
            'product', 'product_name', 'product_code', 'quantity', 'import_date', 
            'export_date', 'user', 'user_name', 
        ]
        read_only_fields = fields

class TechicalSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechicalSetting
        fields = '__all__'


class ServiceInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name','type']

class TechicalSettingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechicalSetting
        fields = ['id', 'name']

class ServiceTechnicalSettingSerializer(serializers.ModelSerializer):
    service = ServiceInfoSerializer(read_only=True)
    technical_setting = TechicalSettingInfoSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), write_only=True, source='service')
    technical_setting_id = serializers.PrimaryKeyRelatedField(queryset=TechicalSetting.objects.all(), write_only=True, source='technical_setting')

    class Meta:
        model = ServiceTechnicalSetting
        fields = ['id', 'service', 'technical_setting', 'service_id', 'technical_setting_id']
