from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import serializers
from app_treatment.models import Bill, Booking, ClinicalExamination, DoctorProcess, DoctorHealthCheck, ExaminationOrder, ExaminationOrderItem, ExpertSessionRecord, ReExamination, ServiceAssign, SessionTechicalSetting, \
    TreatmentRequest, TreatmentSession, diagnosis_medicine, diagnosis_service, PaymentHistory
from app_product.models import ServiceTreatmentPackage
from app_customer.models import Customer
from django.db import models
from django.apps import apps
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType
from app_treatment.models import ARItem, PaymentHistory
from django.db import OperationalError
from django.core.exceptions import FieldDoesNotExist
from typing import Optional
from rest_framework import status
from rest_framework.response import Response

# app_home/serializers.py
from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_date
from rest_framework import serializers
from django.db.models import Count, F, Sum, DecimalField, ExpressionWrapper, Q, Prefetch
from app_treatment.models import SessionTechicalSetting  

User = get_user_model()

from app_home.models import TestService, TreatmentPackage, generate_random_code
from app_product.models import Service, TechicalSetting
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_time, parse_date

from app_customer.serializers import CustomerIntroducerSerializer

class CustomerGetSerializer(serializers.ModelSerializer):
    source_details = serializers.SerializerMethodField()
    introducers = CustomerIntroducerSerializer(source="customer_introducers_set", many=True)
    examination_histories = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'name', 'code', 'birth', 'mobile', 'email', 'gender', 'address',
                  'main_status', 'city', 'ward', 'district',
                  'source_details', 'introducers', 'examination_histories']
        read_only_fields = fields
        
    def get_source_details(self, obj):
        try:
            # use *_id to avoid implicit queries
            referral_id = getattr(obj, "primary_referral_id", None)
            if not referral_id:
                return None

            # if view already did select_related('primary_referral', ...), this will be populated
            referral = getattr(obj, "primary_referral", None)
            if referral is None:
                Referral = apps.get_model("app_treatment", "Referral")
                referral = (Referral.objects
                            .only("id", "ref_type", "ref_customer_id", "ref_hr_id", "ref_actor_id")
                            .filter(pk=referral_id)
                            .first())
                if referral is None:
                    return None

            rtype = getattr(referral, "ref_type", "unknown")
            if rtype == "unknown":
                return None

            # ---- customer
            if rtype == "customer" and getattr(referral, "ref_customer_id", None):
                # prefer already-selected object, otherwise fetch minimal fields
                rc = getattr(referral, "ref_customer", None)
                if rc is None:
                    Customer = apps.get_model("app_customer", "Customer")
                    rc = (Customer.objects
                        .only("id", "code", "name")
                        .filter(pk=referral.ref_customer_id)
                        .first())
                code = getattr(rc, "code", None) if rc else None
                name = getattr(rc, "name", None) if rc else None
                return {
                    "ref_type": "customer",
                    "ref_customer_id": referral.ref_customer_id,
                    "ref_customer_code": code,
                    "ref_customer_name": name,
                    "label": f"KH:{code or name}",
                }

            # ---- hr (HrUserProfile)
            if rtype == "hr" and getattr(referral, "ref_hr_id", None):
                hr = getattr(referral, "ref_hr", None)
                if hr is None:
                    Hr = apps.get_model("app_hr", "HrUserProfile")
                    hr = (Hr.objects
                        .only("id", "code", "full_name")
                        .filter(pk=referral.ref_hr_id)
                        .first())
                code = getattr(hr, "code", None) if hr else None
                full_name = getattr(hr, "full_name", None) if hr else None
                return {
                    "ref_type": "hr",
                    "ref_hr_id": referral.ref_hr_id,
                    "ref_hr_code": code,
                    "ref_hr_name": full_name,
                    "label": f"HR:{code or full_name}",
                }

            # ---- actor (+ optional source)
            if rtype == "actor" and getattr(referral, "ref_actor_id", None):
                actor = getattr(referral, "ref_actor", None)
                if actor is None:
                    Actor = apps.get_model("app_treatment", "Actor")
                    actor = (Actor.objects
                            .only("id", "name", "source_id")
                            .filter(pk=referral.ref_actor_id)
                            .first())
                actor_id = getattr(actor, "id", referral.ref_actor_id)
                actor_name = getattr(actor, "name", None) if actor else None

                # source (optional)
                source_id = getattr(actor, "source_id", None) if actor else None
                source_name = None
                if source_id:
                    src = getattr(actor, "source", None)
                    if src is None:
                        Source = apps.get_model("app_treatment", "Source")
                        src = Source.objects.only("id", "name").filter(pk=source_id).first()
                    source_name = getattr(src, "name", None) if src else None

                return {
                    "ref_type": "actor",
                    "actor_id": actor_id,
                    "actor_name": actor_name,
                    "source_id": source_id,
                    "source_name": source_name,
                    "label": f"{source_name}:{actor_name}" if source_name else actor_name,
                }

            return None
        except OperationalError:
            # If DB connection drops mid-serialize, don't 500 the whole list
            return None

    def get_examination_histories(self, obj):
        bookings = Booking.objects.filter(customer_id=obj.id).values("id", "receiving_day")
        return [{"id": booking["id"], "day": booking["receiving_day"]} for booking in bookings]

class DoctorMiniSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User  # import User phù hợp dự án của bạn
        fields = ("id", "username", "first_name", "last_name", "full_name", "email")

    def get_full_name(self, obj):
        # tuỳ bạn chuẩn hoá
        return f"{obj.last_name} {obj.first_name}".strip()


class DoctorHealthCheckMiniSerializer(serializers.ModelSerializer):
    doctor = DoctorMiniSerializer(read_only=True)
    class Meta:
        model = DoctorHealthCheck
        fields = ("id", "doctor")


class TestServiceMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestService
        fields = ("id", "code", "name")


class ExaminationOrderItemSerializer(serializers.ModelSerializer):
    test_service_detail = TestServiceMiniSerializer(source="test_service", read_only=True)

    class Meta:
        model = ExaminationOrderItem
        fields = (
            "id",
            "test_service",
            "test_service_detail",
            "quantity",
            "note",
            'test_result',
        )


class ExaminationOrderSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(write_only=True, required=True)
    items = ExaminationOrderItemSerializer(many=True)

    class Meta:
        model = ExaminationOrder
        fields = (
            "id",
            "customer",
            "doctor_id",
            "diagnosis",
            "note",
            'start_time',
            'end_time',
            "created",
            "updated",
            "items",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['doctor_id'] = getattr(instance, 'doctor_profile_id', None)
        return data

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        
        # Xử lý doctor_id giống như DoctorProcessSerializer
        hr_id = validated_data.pop("doctor_id")
        HrUserProfile = apps.get_model('app_hr', 'HrUserProfile')
        doctor_profile = HrUserProfile.objects.filter(pk=hr_id).first()
        if not doctor_profile:
            raise serializers.ValidationError({"doctor_id": "HrUserProfile không tồn tại."})
        
        # Tạo ExaminationOrder với doctor_profile
        order = ExaminationOrder.objects.create(
            doctor_profile=doctor_profile,
            **validated_data
        )
        
        # Tạo các items
        for it in items_data:
            ExaminationOrderItem.objects.create(order=order, **it)
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        
        # Xử lý đổi bác sĩ giống như DoctorProcessSerializer
        hr_id = validated_data.pop("doctor_id", None)
        if hr_id is not None:
            HrUserProfile = apps.get_model('app_hr', 'HrUserProfile')
            doctor_profile = HrUserProfile.objects.filter(pk=hr_id).first()
            if not doctor_profile:
                raise serializers.ValidationError({"doctor_id": "HrUserProfile không tồn tại."})
            instance.doctor_profile = doctor_profile

        # Cập nhật các field khác
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        # Cập nhật items nếu có
        if items_data is not None:
            # Chiến lược đơn giản: xoá cũ, tạo lại
            instance.items.all().delete()
            for it in items_data:
                ExaminationOrderItem.objects.create(order=instance, **it)

        return instance
    
def _tr_created_field():
    # helper nhỏ để an toàn với schema
    try:
        TreatmentRequest._meta.get_field('created')
        return 'created'
    except FieldDoesNotExist:
        return 'created_at'
        
def _hr_display_name(hr) -> Optional[str]:
    if not hr:
        return None
    name = getattr(hr, "full_name", None)
    if name:
        return name
    u = getattr(hr, "user", None)
    if u:
        try:
            full = u.get_full_name() if hasattr(u, "get_full_name") else None
        except Exception:
            full = None
        return full or getattr(u, "username", None) or getattr(u, "email", None)
    return None

class BookingSerializer(serializers.ModelSerializer):
    customer_info = CustomerGetSerializer(source="customer", read_only=True)
    lead_status_code = serializers.CharField(source='customer.lead_status.code', read_only=True)
    contact_date = serializers.DateField(source='customer.contact_date', read_only=True)

    treating_doctor = serializers.SerializerMethodField(read_only=True)
    latest_plan_type = serializers.SerializerMethodField(read_only=True)
    latest_plan_status = serializers.SerializerMethodField(read_only=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ✅ Cache để tránh query lặp lại
        self._tr_cache = {}
        self._plan_status_cache = {}
    
    def _get_latest_tr(self, booking):
        """
        Lấy TreatmentRequest mới nhất của customer.
        Ưu tiên dùng prefetch data từ ViewSet.
        """
        customer_id = getattr(booking, 'customer_id', None)
        if not customer_id:
            return None
        
        # ✅ Check cache
        if customer_id in self._tr_cache:
            return self._tr_cache[customer_id]
        
        tr = None
        
        # ✅ Ưu tiên: Dùng prefetch data
        try:
            customer = booking.customer
            if hasattr(customer, 'latest_tr_list') and customer.latest_tr_list:
                tr = customer.latest_tr_list[0]
        except Exception:
            pass
        
        # ✅ Fallback: Query trực tiếp (chỉ khi prefetch thất bại)
        if tr is None:
            tr = (
                TreatmentRequest.objects
                .filter(customer_id=customer_id)
                .select_related('user', 'doctor_profile', 'service')
                .prefetch_related(
                    Prefetch(
                        'treatment_sessions',
                        queryset=TreatmentSession.objects.prefetch_related(
                            'sessiontechicalsetting_set'
                        )
                    )
                )
                .order_by('-created_at', '-id')
                .first()
            )
        
        # ✅ Cache kết quả
        self._tr_cache[customer_id] = tr
        return tr
    
    def get_treating_doctor(self, obj):
        """Lấy tên bác sĩ điều trị"""
        tr = self._get_latest_tr(obj)
        if not tr:
            return None
        
        # ✅ Ưu tiên doctor_profile
        if tr.doctor_profile_id:
            dp = tr.doctor_profile
            # HrUserProfile có thể có full_name hoặc name
            return getattr(dp, 'full_name', None) or getattr(dp, 'name', None)
        
        # ✅ Fallback: user tạo TR
        if tr.user_id:
            user = tr.user
            full_name = getattr(user, 'get_full_name', lambda: None)()
            return full_name or getattr(user, 'username', None)
        
        return None
    
    def get_latest_plan_type(self, obj):
        """Loại phác đồ = loại dịch vụ"""
        tr = self._get_latest_tr(obj)
        if not tr or not tr.service_id:
            return None
        
        return getattr(tr.service, 'type', None)
    
    def get_latest_plan_status(self, obj):
        """
        Trạng thái phác đồ dựa trên SessionTechicalSetting:
        - no_plan: chưa có TR
        - no_session: có TR nhưng chưa có buổi/kỹ thuật
        - not_started: có kỹ thuật nhưng chưa has_come nào
        - in_progress: có has_come nhưng chưa hết
        - done: tất cả has_come=True
        """
        tr = self._get_latest_tr(obj)
        
        if not tr:
            return {
                "code": "no_plan",
                "label": "Chưa có phác đồ",
                "total": 0,
                "done": 0
            }
        
        # ✅ Check cache
        tr_id = tr.id
        if tr_id in self._plan_status_cache:
            return self._plan_status_cache[tr_id]
        
        total = 0
        done = 0
        
        # ✅ Ưu tiên: Dùng prefetch data
        if hasattr(tr, 'treatment_sessions'):
            sessions = tr.treatment_sessions.all()
            
            for session in sessions:
                if hasattr(session, 'sessiontechicalsetting_set'):
                    techs = session.sessiontechicalsetting_set.all()
                    total += len(techs)
                    done += sum(1 for tech in techs if getattr(tech, 'has_come', False))
        else:
            # ✅ Fallback: Query aggregate (nhanh hơn count riêng)
            from django.db.models import Count, Q
            stats = SessionTechicalSetting.objects.filter(
                session__treatment_request=tr
            ).aggregate(
                total=Count('id'),
                done=Count('id', filter=Q(has_come=True))
            )
            total = stats['total'] or 0
            done = stats['done'] or 0
        
        # ✅ Xác định trạng thái
        if total == 0:
            result = {
                "code": "no_session",
                "label": "Chưa tạo buổi",
                "total": 0,
                "done": 0
            }
        elif done == 0:
            result = {
                "code": "not_started",
                "label": "Chưa bắt đầu",
                "total": total,
                "done": 0
            }
        elif done < total:
            result = {
                "code": "in_progress",
                "label": "Đang điều trị",
                "total": total,
                "done": done
            }
        else:  # done == total
            result = {
                "code": "done",
                "label": "Hoàn thành",
                "total": total,
                "done": done
            }
        
        # ✅ Cache kết quả
        self._plan_status_cache[tr_id] = result
        return result
    
    def validate(self, data):
        is_update = self.instance is not None
        customer = data.get('customer', self.instance.customer if is_update else None)

        if not customer:
            raise serializers.ValidationError("Khách hàng là bắt buộc.")

        return data

    class Meta:
        model = Booking
        fields = '__all__'

class DoctorHealthCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorHealthCheck
        fields = '__all__'

class ClinicalExaminationSerializer(serializers.ModelSerializer):
    doctor = DoctorMiniSerializer(source="doctor_health_check_process.doctor", read_only=True)
    doctor_id = serializers.IntegerField(source="doctor_health_check_process.doctor_id", read_only=True)
    floor_name = serializers.StringRelatedField(source="floor", read_only=True)
    department_name = serializers.StringRelatedField(source="department", read_only=True)

    class Meta:
        model = ClinicalExamination
        fields = [
            'id',
            'doctor_health_check_process',
            'doctor',          # ⬅️ thay cho assigned_doctor_name
            'doctor_id',       # ⬅️ tiện cho client lấy id
            'floor',
            'floor_name',
            'department',
            'department_name',
            'medical_history',
            'diagnosis',
            'present_symptom',
            'treatment_method',
        ]

class DiagnosisMedicineSerializer(serializers.ModelSerializer):
    product_name = serializers.StringRelatedField(source='product', read_only=True)
    unit_str = serializers.StringRelatedField(source='unit', read_only=True)
    class Meta:
        model = diagnosis_medicine
        fields = ['id', 'product', 'product_name', 'quantity', 'unit', 'unit_str', 'dose', 'note', 'price']
class DiagnosisMedicineV2Serializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(source="doctor_process.customer.id", read_only=True)
    doctor_id = serializers.SerializerMethodField()
    class Meta:
        model = diagnosis_medicine
        fields = [
            "id", "doctor_process", "product", "quantity", "unit", 
            "dose", "note", "price", 
             "customer_id", "doctor_id"
        ]
    def get_doctor_id(self, obj):
        dp = getattr(obj, "doctor_process", None)
        # nếu sau này bạn thêm cột assigned_doctor vào DoctorProcess thì dòng dưới sẽ tự trả id
        return getattr(getattr(dp, "assigned_doctor", None), "id", None)
class NestedDiagnosisMedicineWriteSerializer(serializers.ModelSerializer):
    # id chỉ dùng cho update; khi tạo mới bỏ qua
    id = serializers.IntegerField(required=False)

    class Meta:
        model = diagnosis_medicine
        fields = ["id", "product", "quantity", "unit", "dose", "note", "price"]
        extra_kwargs = {
            "product": {"required": False},  # tạo mới thì nên gửi; nếu không gửi, model vẫn có thể tự set unit/price theo product (nếu có)
            "quantity": {"required": False},
            "unit": {"required": False, "allow_null": True},
            "dose": {"required": False, "allow_null": True, "allow_blank": True},
            "note": {"required": False, "allow_null": True, "allow_blank": True},
            "price": {"required": False, "allow_null": True},
        }

# app_treatment/serializers.py
from django.apps import apps
from rest_framework import serializers
from django.db import transaction
from decimal import Decimal

class DoctorProcessSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(write_only=True, required=True)
    customer_details = serializers.SerializerMethodField(read_only=True)
    
    total_amount = serializers.SerializerMethodField(read_only=True)
    total_after_discount = serializers.SerializerMethodField(read_only=True)

    # Versioning
    parent_id = serializers.IntegerField(source="parent.id", read_only=True)
    version = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    replace_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    # Thuốc
    diagnosis_medicines = NestedDiagnosisMedicineWriteSerializer(many=True, required=False)

    # 👇 Bác sĩ: FE gửi hr.id qua field doctor_id (giữ tên cũ để không phải sửa FE)
    doctor_id = serializers.IntegerField(write_only=True, required=True)

    # Hiển thị
    assigned_doctor_name = serializers.SerializerMethodField(read_only=True)

    # Fork
    fork_from_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = DoctorProcess
        fields = [
            "id",
            "customer_id", "customer_details",
            "parent_id", "version", "is_active", "replace_reason",
            "doctor_id", "assigned_doctor_name", 
            "medicine_discount", "diagnosis_medicines",
            "start_time", "end_time",
            "fork_from_id", "total_amount",
            "total_after_discount",
        ]
        read_only_fields = [
            "customer_details", "parent_id", "version", "is_active",
            "assigned_doctor_name", "total_amount", "total_after_discount",
        ]

    # ----- Helpers -----
    def get_customer_details(self, obj):
        c = obj.customer
        return {"id": c.id, "name": c.name, "code": c.code} if c else None

    def get_assigned_doctor_name(self, obj):
        p = getattr(obj, "doctor_profile", None)
        if not p:
            return None
        # ưu tiên họ tên, sau đó email, sau đó code
        return p.full_name or p.email or getattr(p, "code", None) or f"HR#{p.pk}"
    
    # === NEW: totals & discount info ===
    def get_total_amount(self, obj):
        # tổng trước khuyến mãi
        if hasattr(obj, "total_amount"):
            return obj.total_amount()
        # fallback nếu bạn dùng tên khác
        return obj.total_product_amount_after_discount() + Decimal("0")  # tệ nhất vẫn trả số

    def get_total_after_discount(self, obj):
        # tổng sau khuyến mãi
        if hasattr(obj, "total_after_discount"):
            return obj.total_after_discount()
        # fallback theo method có sẵn của bạn
        if hasattr(obj, "total_product_amount_after_discount"):
            return obj.total_product_amount_after_discount()
        return self.get_total_amount(obj)
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # trả về doctor_id = id của HrUserProfile đang gắn
        data["doctor_id"] = getattr(instance, "doctor_profile_id", None)
        return data

    def _upsert_medicines(self, doctor_process, items, delete_missing=False):
        if items is None:
            return
        if not isinstance(items, list):
            raise serializers.ValidationError({"diagnosis_medicines": "Phải là danh sách."})

        existing_qs = doctor_process.diagnosis_medicines.select_related("product", "unit").all()
        existing_map = {str(obj.id): obj for obj in existing_qs}
        sent_ids = set()

        for payload in items:
            dm_id = payload.get("id")
            if dm_id:
                inst = existing_map.get(str(dm_id))
                if not inst:
                    raise serializers.ValidationError({"diagnosis_medicines": [f"id {dm_id} không thuộc DoctorProcess hiện tại"]})
                for k, v in payload.items():
                    if k != "id":
                        setattr(inst, k, v)
                inst.save()
                sent_ids.add(str(dm_id))
            else:
                diagnosis_medicine.objects.create(doctor_process=doctor_process, **payload)

        if delete_missing:
            for obj in existing_qs:
                if str(obj.id) not in sent_ids:
                    obj.delete()

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # >>> VÁ NHANH: gọi hàm sync ARItem ngay sau khi đã lưu KM <<<
        self._sync_ar_for_doctor_process(instance)  # nếu có sẵn hàm trong serializer/service
        # hoặc gọi service tách riêng (xem Cách 3)

        return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)

    def _sync_ar_for_doctor_process(self, dp):
        ARItem = apps.get_model('app_treatment', 'ARItem')   # <-- chú ý đúng AppLabel & ClassName
        if ARItem is None:
            raise LookupError("Không tìm thấy model app_treatment.ARItem — kiểm tra class name & app label.")

        ct = ContentType.objects.get_for_model(type(dp))
        amount = Decimal(str(dp.total_after_discount() or 0))
        qs = ARItem.objects.filter(content_type=ct, object_id=dp.id)

        if amount > 0:
            if qs.exists():
                ar = qs.first()
                paid = ar.amount_paid or Decimal('0')
                ar.customer = dp.customer
                ar.description = 'Đơn thuốc'
                ar.amount_original = amount
                ar.status = 'closed' if paid >= amount else ('partial' if paid > 0 else 'open')
                ar.save(update_fields=['customer','description','amount_original','status'])
            else:
                ARItem.objects.create(
                    customer=dp.customer,
                    content_type=ct,
                    object_id=dp.id,
                    description='Đơn thuốc',
                    amount_original=amount,
                    status='open',
                )
        else:
            qs.delete()

    # ----- Create / Update -----
    @transaction.atomic
    def create(self, validated_data):
        medicines_data = validated_data.pop("diagnosis_medicines", None)
        fork_from_id   = validated_data.pop("fork_from_id", None)
        customer_id    = validated_data.pop("customer_id")

        # 👇 Lấy HR profile theo id; KHÔNG kiểm tra User nữa
        hr_id = validated_data.pop("doctor_id")
        HrUserProfile = apps.get_model('app_hr', 'HrUserProfile')
        doctor_profile = HrUserProfile.objects.filter(pk=hr_id).first()
        if not doctor_profile:
            raise serializers.ValidationError({"doctor_id": "HrUserProfile không tồn tại."})

        customer = Customer.objects.get(pk=customer_id)

        if fork_from_id:
            parent = (DoctorProcess.objects
                      .select_for_update()
                      .get(pk=fork_from_id))
            if parent.customer_id != customer_id:
                raise serializers.ValidationError("fork_from_id không thuộc cùng khách hàng.")

            new_dp = parent.fork(replace_reason=validated_data.get("replace_reason"))
            for f in ("medicine_discount", "start_time", "end_time"):
                if f in validated_data:
                    setattr(new_dp, f, validated_data[f])
            new_dp.doctor_profile = doctor_profile
            new_dp.save()

            if medicines_data is not None:
                self._upsert_medicines(new_dp, medicines_data, delete_missing=False)
            self._sync_ar_for_doctor_process(new_dp)
            return new_dp

        dp = DoctorProcess.objects.create(
            customer=customer,
            doctor_profile=doctor_profile,   # 👈 dùng HR profile
            **validated_data
        )
        self._upsert_medicines(dp, medicines_data, delete_missing=False)

        customer.main_status = '2'
        customer.save(update_fields=['main_status'])

        self._sync_ar_for_doctor_process(dp)
        return dp

    @transaction.atomic
    def update(self, instance, validated_data):
        if instance.medicines_has_paid and "diagnosis_medicines" in self.initial_data:
            raise serializers.ValidationError("Không thể cập nhật danh sách thuốc vì đã thanh toán.")

        validated_data.pop("customer_id", None)
        validated_data.pop("fork_from_id", None)

        # 👇 Cho phép đổi bác sĩ bằng hr.id; KHÔNG liên quan User
        hr_id = validated_data.pop("doctor_id", None)
        if hr_id is not None:
            HrUserProfile = apps.get_model('app_hr', 'HrUserProfile')
            doctor_profile = HrUserProfile.objects.filter(pk=hr_id).first()
            if not doctor_profile:
                raise serializers.ValidationError({"doctor_id": "HrUserProfile không tồn tại."})
            instance.doctor_profile = doctor_profile

        # chặn đổi các field versioning
        for f in ["parent", "version", "is_active"]:
            validated_data.pop(f, None)

        medicines_data = validated_data.pop("diagnosis_medicines", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        request = self.context.get("request")
        delete_missing = str(request.query_params.get("delete_missing", "false")).lower() in ("1", "true", "yes") if request else False
        if medicines_data is not None:
            self._upsert_medicines(instance, medicines_data, delete_missing=delete_missing)

        self._sync_ar_for_doctor_process(instance)
        return instance
    
class DiagnosisServiceSerializer(serializers.ModelSerializer):
    service_name = serializers.StringRelatedField(source='service', read_only=True)
    treatment_package_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = diagnosis_service
        fields = ['id', 'service', 'service_name', 'quantity', 'treatment_package_id']


class ServiceAssignSerializer(serializers.ModelSerializer):
    doctor_process_id = serializers.IntegerField(write_only=True, required=False)
    straight_booking_id = serializers.IntegerField(write_only=True, required=False)
    diagnosis_services = DiagnosisServiceSerializer(many=True, required=False)

    class Meta:
        model = ServiceAssign
        fields = [
            'id',
            'doctor_process_id',
            'straight_booking_id',
            'assigned_expert',
            'treatment_method',
            'service_discount',
            'diagnosis_services',
        ]

    def validate(self, attrs):

        doctor_process_id = attrs.get('doctor_process_id')
        straight_booking_id = attrs.get('straight_booking_id')

        if doctor_process_id and straight_booking_id:
            raise serializers.ValidationError("Không thể truyền cả doctor_process_id và straight_booking_id. Chỉ chọn một.")

        if not doctor_process_id and not straight_booking_id:
            raise serializers.ValidationError("Cần phải truyền hoặc doctor_process_id hoặc straight_booking_id.")

        return attrs

    def create(self, validated_data):
        diagnosis_services_data = validated_data.pop('diagnosis_services', [])

        doctor_process_id = validated_data.pop('doctor_process_id', None)
        straight_booking_id = validated_data.pop('straight_booking_id', None)
        treatment_request_for_booking_exp = validated_data.pop('treatment_request', [])

        # (phần xử lý treatment_request giữ nguyên)

        if doctor_process_id:
            doctor_process = get_object_or_404(DoctorProcess, pk=doctor_process_id)
            booking = doctor_process.customer.doctor_health_check_process.booking
            validated_data['doctor_process'] = doctor_process
        else:
            booking = get_object_or_404(Booking, pk=straight_booking_id)
            validated_data['straight_booking'] = booking

        service_assign = ServiceAssign.objects.create(**validated_data)

        for diag_data in diagnosis_services_data:
            treatment_package_id = diag_data.pop("treatment_package_id", None)
            treatment_package = None

            if treatment_package_id:
                try:
                    treatment_package = TreatmentPackage.objects.get(id=treatment_package_id)
                except TreatmentPackage.DoesNotExist:
                    raise serializers.ValidationError(f"Gói liệu trình ID {treatment_package_id} không tồn tại.")

            diagnosis_service.objects.create(
                service_assign=service_assign,
                treatment_package=treatment_package,
                **diag_data
            )

        return service_assign

    def update(self, instance, validated_data):
        # Không cho cập nhật type
        validated_data.pop('type', None)

        diagnosis_services_data = validated_data.pop('diagnosis_services', None)
        doctor_process_id = validated_data.pop('doctor_process_id', None)
        straight_booking_id = validated_data.pop('straight_booking_id', None)

        if doctor_process_id:
            try:
                doctor_process = DoctorProcess.objects.get(pk=doctor_process_id)
            except DoctorProcess.DoesNotExist:
                raise serializers.ValidationError({"doctor_process_id": "DoctorProcess không tồn tại."})
            instance.doctor_process = doctor_process
            instance.straight_booking = None  

        elif straight_booking_id:
            try:
                booking = Booking.objects.get(pk=straight_booking_id)
            except Booking.DoesNotExist:
                raise serializers.ValidationError({"straight_booking_id": "Booking không tồn tại."})
            instance.straight_booking = booking
            instance.doctor_process = None  

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if diagnosis_services_data is not None:
            instance.diagnosis_services.all().delete()
            for diag_data in diagnosis_services_data:
                diagnosis_service.objects.create(service_assign=instance, **diag_data)

        return instance
class ServiceGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name']

class ExpertSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    class Meta:
        model = User
        fields = ['id', 'full_name']


class SessionTechicalSettingSerializer(serializers.ModelSerializer):
    techical_setting_id = serializers.IntegerField(source='techical_setting.id', read_only=True)
    techical_setting_name = serializers.CharField(source='techical_setting.name', read_only=True)
    price = serializers.DecimalField(source='techical_setting.price', read_only=True, max_digits=10, decimal_places=2)
    # duration = serializers.IntegerField(source='techical_setting.duration', read_only=True)
    expert = serializers.SerializerMethodField()
    
    techical_setting_duration = serializers.IntegerField(source='techical_setting.duration', read_only=True)
    
    duration_minutes = serializers.IntegerField(read_only=True)
    room = serializers.CharField(read_only=True)
    has_come = serializers.BooleanField(read_only=True)

    class Meta:
        model = SessionTechicalSetting
        fields = [
            'id',
            'techical_setting_id', 'techical_setting_name', 'price', 'techical_setting_duration',
            'duration_minutes', 'room', 'has_come',
            'expert'
        ]

    def get_expert(self, obj):
        u = getattr(obj, 'expert', None)
        if not u:
            return None
        # tuỳ bạn có serializer UserLite riêng thì dùng, ở đây trả gọn:
        full_name = getattr(u, 'full_name', None) or getattr(u, 'username', None) or f'#{u.id}'
        return {"id": u.id, "full_name": full_name}
        
class TreatmentSessionSerializer(serializers.ModelSerializer):
    techniques = serializers.SerializerMethodField()

    floor_name = serializers.CharField(source='floor.name', read_only=True)
    index_no = serializers.IntegerField(read_only=True)

    # thông tin Booking
    booking_id = serializers.IntegerField(source='booking.id', read_only=True)
    receiving_day = serializers.DateField(source='booking.receiving_day', read_only=True)
    set_date = serializers.DateTimeField(source='booking.set_date', read_only=True)

    # tổng hợp tiện UI (tùy chọn)
    total_duration_minutes = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = TreatmentSession
        fields = [
            'id',
            'index_no',
            'floor_name',
            'is_done',
            'note',

            # Booking
            'booking_id', 'receiving_day', 'set_date',

            # Tổng hợp (tùy chọn)
            'total_duration_minutes', 'total_price',

            # Danh sách dòng kỹ thuật
            'techniques',
        ]

    def get_techniques(self, obj):
        settings = obj.sessiontechicalsetting_set.all()
        return SessionTechicalSettingSerializer(settings, many=True).data
    
    def get_total_duration_minutes(self, obj):
        return obj.sessiontechicalsetting_set.aggregate(
            s=models.Sum('duration_minutes')
        )['s'] or 0

    def get_total_price(self, obj):
        return obj.sessiontechicalsetting_set.aggregate(
            s=models.Sum('techical_setting__price')
        )['s'] or 0
        
def _normalize_booking_dt(receiving_day, set_date):
    d_obj = parse_date(receiving_day) if isinstance(receiving_day, str) else receiving_day
    t_obj = None
    if set_date:
        if isinstance(set_date, str):
            dt = parse_datetime(set_date)
            if dt:
                if not d_obj:
                    d_obj = dt.date()
                t_obj = dt.time()
            else:
                t_obj = parse_time(set_date)
        else:
            if hasattr(set_date, "date") and hasattr(set_date, "time"):
                if not d_obj:
                    d_obj = set_date.date()
                t_obj = set_date.time()
            else:
                t_obj = set_date
    return d_obj, t_obj

class TreatmentRequestSerializer(serializers.ModelSerializer):
    # Read
    service = ServiceGetSerializer(read_only=True)
    treatment_sessions = serializers.SerializerMethodField(read_only=True)
    spent_amount = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()
    
    customer_details = serializers.SerializerMethodField(read_only=True)

    # Write
    service_id = serializers.IntegerField(write_only=True, required=True)
    treatment_package_id = serializers.IntegerField(write_only=True, required=True)
    customer_id = serializers.IntegerField(write_only=True, required=True) 
    sessions = serializers.ListField(write_only=True, required=False)

    doctor_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    doctor_name = serializers.SerializerMethodField(read_only=True)
    diagnosis = serializers.CharField(required=False, allow_blank=True)
    
    discount_id = serializers.IntegerField(required=False, allow_null=True)
    package_price_original = serializers.SerializerMethodField()
    package_price_final = serializers.SerializerMethodField()

    class Meta:
        model = TreatmentRequest
        fields = [
            'id', 'code', 'discount_id', 'customer_details', 'doctor_name',
            # read
            'service', 'treatment_sessions', 'spent_amount', 'service_name',
            'created_at', 'user', 'is_done', 'note', 'selected_package_id',
            # write
            'service_id', 'treatment_package_id', 'customer_id',
            'sessions', 'doctor_id', 'diagnosis', 'package_price_original',  # ✅ Giá gốc
            'package_price_final', 
        ]
        
        read_only_fields = [
            "customer_details", 'doctor_name',
        ]
        
    def get_doctor_name(self, obj):
        p = getattr(obj, "doctor_profile", None)
        if not p:
            return None

        # 1) Ưu tiên full_name trên HR profile
        if getattr(p, "full_name", None):
            return p.full_name
        
    def get_customer_details(self, obj):
        c = obj.customer
        return {"id": c.id, "name": c.name, "code": c.code} if c else None
        
    def get_package_price_original(self, obj):
        """
        Giá gốc của phác đồ (chưa giảm giá)
        = Giá trong ServiceTreatmentPackage hoặc Service.price
        """
        return obj.package_price_original()
    
    def get_package_price_final(self, obj):
    # Dùng TR.discount trực tiếp
        return obj.package_price()
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['doctor_id'] = getattr(instance, 'doctor_profile_id', None)
        return data
        
    def get_service(self, obj):
        s = obj.service
        return {'id': s.id, 'name': s.name, 'type': getattr(s, 'type', None)} if s else None

    def get_treatment_sessions(self, obj):
        qs = (
            obj.treatment_sessions
            .select_related('booking')
            .prefetch_related(
                'sessiontechicalsetting_set__techical_setting',
                'sessiontechicalsetting_set__expert',         # HR
                'sessiontechicalsetting_set__expert__user',    # fallback tên từ User nếu còn
            )
        )
        out = []
        for sess in qs:
            items = []
            for it in sess.sessiontechicalsetting_set.all():
                exp = getattr(it, 'expert', None)  # HrUserProfile hoặc None
                experts_payload = []
                if exp:
                    experts_payload.append({
                        'id': exp.id,
                        'full_name': _hr_display_name(exp),
                    })

                items.append({
                    'id': it.id,
                    'techical_setting_id': it.techical_setting_id,
                    'duration_minutes': it.duration_minutes,
                    'room': it.room,
                    'has_come': it.has_come,
                    'experts': experts_payload,
                })

            out.append({
                'id': sess.id,
                'index_no': sess.index_no,
                'note': sess.note,
                'receiving_day': getattr(sess.booking, 'receiving_day', None),
                'set_date': getattr(sess.booking, 'set_date', None),
                'techniques': items,
            })
        return out

    def get_spent_amount(self, obj):
        return obj.get_total_price_is_done_treatment_sessions()

    def get_service_name(self, obj):
        return obj.service.name if obj.service else None
    
    def _get_customer_or_raise(self, customer_id: int) -> Customer:
        try:
            return Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Khách hàng không tồn tại.")

    def _validate_service_and_package(self, service_id: int, package_id: int):
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            raise serializers.ValidationError("Service không tồn tại.")
        try:
            package = TreatmentPackage.objects.get(id=package_id)
        except TreatmentPackage.DoesNotExist:
            raise serializers.ValidationError("Gói liệu trình không tồn tại.")
        if not ServiceTreatmentPackage.objects.filter(
            service_id=service.id, treatment_package_id=package.id
        ).exists():
            raise serializers.ValidationError("Gói liệu trình không thuộc dịch vụ đã chọn.")
        return service, package
    
    def _ensure_aware(self, dt):
        if not dt:
            return dt
        if timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.get_current_timezone())
        return dt
    
    def _get_booking_type_for_service(self, service: Service) -> str:
        # service.type có thể là 'TLCB' hoặc 'TLDS'
        if service.type == 'TLCB':
            return "treatment_cure"
        if service.type == 'TLDS':
            return "treatment_relax"
        return "treatment_cure"

    # ------------------- CREATE -------------------
    @transaction.atomic
    def create(self, validated_data):
        service_id   = validated_data.pop("service_id")
        package_id   = validated_data.pop("treatment_package_id")
        customer_id  = validated_data.pop("customer_id")
        session_data = validated_data.pop("sessions", [])
        user         = self.context["request"].user
        discount_id = validated_data.pop('discount_id', None)

        # doctor_id = HrUserProfile.id (không kiểm tra liên kết User)
        hr_id = validated_data.pop("doctor_id", None)
        HrUserProfile = apps.get_model("app_hr", "HrUserProfile")
        doctor_profile = None
        if hr_id is not None:
            doctor_profile = HrUserProfile.objects.filter(pk=hr_id).first()
            if not doctor_profile:
                raise serializers.ValidationError({"doctor_id": "HrUserProfile không tồn tại."})

        diagnosis = validated_data.pop("diagnosis", "")

        # Validate & create TR
        customer = self._get_customer_or_raise(customer_id)
        service, package = self._validate_service_and_package(service_id, package_id)

        tr = TreatmentRequest.objects.create(
            service=service,
            treatment_package=package,
            doctor_profile=doctor_profile,
            diagnosis=diagnosis,
            customer=customer,
            user=user,
            discount_id=discount_id,
            **validated_data,
        )

        # cập nhật trạng thái KH
        customer.main_status = "2"
        customer.save(update_fields=["main_status"])

        # ---- fallback booking cho buổi #1 ----
        now_dt = timezone.now()
        today  = now_dt.date()

        booking_today = (
            Booking.objects
            .filter(customer=customer, receiving_day=today)
            .order_by("set_date", "created")
            .first()
        )

        # Check-in tất cả booking trong ngày
        Booking.objects.filter(
            customer=customer,
            receiving_day=today,
            has_come=False
        ).update(has_come=True)

        # type booking theo service
        booking_type = self._get_booking_type_for_service(service)

        # Tạo các buổi
        for i, session in enumerate(session_data, start=1):
            session_note  = session.get("note", f"Buổi {i}")
            techniques    = session.get("techniques", [])
            receiving_day = session.get("receiving_day")
            set_date      = session.get("set_date")

            booking = None
            if receiving_day or set_date:
                # tạo booking đúng theo payload
                d_obj, t_obj = _normalize_booking_dt(receiving_day, set_date)

                booking = Booking.objects.create(
                    customer=customer,
                    type=booking_type,
                    note=f"Buổi trị liệu {i} - {service.name}",
                    is_treatment=True,
                    has_come=False,
                    receiving_day=d_obj,
                    set_date=t_obj,
                )

                # Nếu có kỹ thuật đã đến → đồng bộ booking
                if any(bool(t.get("has_come")) for t in techniques):
                    if not booking.has_come:
                        booking.has_come = True
                        booking.save(update_fields=["has_come"])

                # nếu buổi này cũng là hôm nay → coi như check-in
                if d_obj == today and not booking.has_come:
                    booking.has_come = True
                    booking.save(update_fields=["has_come"])

            else:
                # không có thời gian → buổi 1 dùng booking trong ngày hoặc tạo mới
                if i == 1:
                    booking = booking_today or Booking.objects.create(
                        customer=customer,
                        type=booking_type,
                        note=f"Buổi trị liệu {i} - {service.name}",
                        is_treatment=True,
                        has_come=True,         # coi như đã đến
                        receiving_day=today,
                        set_date=now_dt.time(),  # TimeField -> time
                    )

            # tạo session & items
            sess = TreatmentSession.objects.create(
                treatment_request=tr,
                note=session_note,
                index_no=i,
                booking=booking,
            )

            for tech in techniques:
                ts_id            = tech.get("techical_setting_id")
                expert_ids       = tech.get("expert_ids", [])
                duration_minutes = tech.get("duration_minutes", 10)
                room             = tech.get("room")
                has_come         = bool(tech.get("has_come", False))

                ts = TechicalSetting.objects.filter(id=ts_id).first()
                if not ts:
                    raise serializers.ValidationError(f"Kỹ thuật ID {ts_id} không tồn tại.")

                SessionTechicalSetting.objects.create(
                    session=sess,
                    techical_setting=ts,
                    duration_minutes=duration_minutes,
                    room=room,
                    has_come=has_come,
                    expert_id=(expert_ids[0] if expert_ids else None),  # <-- lưu expert_id tại đây
                )

                # nếu có item đã đến → chắc chắn booking.has_come=True
                if booking and has_come and not booking.has_come:
                    booking.has_come = True
                    booking.save(update_fields=["has_come"])

        return tr

    # ------------------- UPDATE -------------------
    @transaction.atomic
    def update(self, instance, validated_data):
        incoming_sessions = validated_data.pop("sessions", [])
        service_id        = validated_data.pop("service_id", None)
        package_id        = validated_data.pop("treatment_package_id", None)
        customer_id       = validated_data.pop("customer_id", None)  # hỗ trợ update
        hr_id             = validated_data.pop("doctor_id", None)
        diagnosis         = validated_data.pop("diagnosis", serializers.empty)
        discount_id       = validated_data.pop('discount_id', None)

        if discount_id is not None:
            if discount_id:
                # Validate discount tồn tại
                Discount = apps.get_model('app_home', 'Discount')
                discount = Discount.objects.filter(pk=discount_id).first()
                if not discount:
                    raise serializers.ValidationError({"discount_id": "Mã giảm giá không tồn tại."})
                instance.discount = discount
            else:
                # discount_id = None -> bỏ mã giảm giá
                instance.discount = None
            
        # Cập nhật service / package
        if service_id is not None:
            service = Service.objects.filter(id=service_id).first()
            if not service:
                raise serializers.ValidationError("Service không tồn tại.")
            instance.service = service

        if package_id is not None:
            package = TreatmentPackage.objects.filter(id=package_id).first()
            if not package:
                raise serializers.ValidationError("Gói liệu trình không tồn tại.")
            if not ServiceTreatmentPackage.objects.filter(
                service_id=instance.service_id, treatment_package_id=package.id
            ).exists():
                raise serializers.ValidationError("Gói liệu trình không thuộc dịch vụ đã chọn.")
            instance.treatment_package = package

        # đổi bác sĩ bằng hr.id
        if hr_id is not None:
            HrUserProfile = apps.get_model("app_hr", "HrUserProfile")
            doctor_profile = HrUserProfile.objects.filter(pk=hr_id).first()
            if not doctor_profile:
                raise serializers.ValidationError({"doctor_id": "HrUserProfile không tồn tại."})
            instance.doctor_profile = doctor_profile

        if diagnosis is not serializers.empty:
            instance.diagnosis = diagnosis

        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        
        instance.recalc_ar()

        # Xác định customer để tạo/điều chỉnh Booking
        if customer_id:
            customer = self._get_customer_or_raise(customer_id)
        else:
            any_sess = instance.treatment_sessions.select_related("booking__customer").first()
            customer = getattr(getattr(any_sess, "booking", None), "customer", None)
            if not customer:
                raise serializers.ValidationError(
                    "Không xác định được khách hàng. Vui lòng gửi kèm 'customer_id'."
                )

        # Nếu service đã đổi, có thể muốn đồng bộ type của các booking cũ
        booking_type = self._get_booking_type_for_service(instance.service)
        # Optional: đồng bộ toàn bộ booking hiện có của phác đồ
        # instance.treatment_sessions.filter(booking__isnull=False).update(booking__type=booking_type)

        # Upsert session + items
        from django.db.models import Max
        next_index = (instance.treatment_sessions.aggregate(mx=Max("index_no"))["mx"] or 0) + 1

        for s in incoming_sessions:
            session_id    = s.get("id")
            session_note  = s.get("note", None)
            receiving_day = s.get("receiving_day")
            set_date      = s.get("set_date")

            # lấy hoặc tạo session
            if session_id:
                sess = (
                    TreatmentSession.objects
                    .select_for_update()
                    .filter(id=session_id, treatment_request=instance)
                    .first()
                )
                if not sess:
                    raise serializers.ValidationError(f"Buổi id={session_id} không thuộc phác đồ.")
                if session_note is not None:
                    sess.note = session_note
            else:
                sess = TreatmentSession.objects.create(
                    treatment_request=instance,
                    note=session_note or f"Buổi {next_index}",
                    index_no=next_index,
                )
                next_index += 1

            # upsert booking
            if receiving_day is not None or set_date is not None:
                d_obj, t_obj = _normalize_booking_dt(receiving_day, set_date)
                if sess.booking_id:
                    bk = sess.booking
                    if receiving_day is not None:
                        bk.receiving_day = d_obj
                    if set_date is not None:
                        bk.set_date = t_obj
                    # đồng bộ type theo service hiện tại
                    if bk.type != booking_type:
                        bk.type = booking_type
                    bk.save(update_fields=["receiving_day", "set_date", "type"])
                else:
                    bk = Booking.objects.create(
                        customer=customer,
                        type=booking_type,
                        note=f"Buổi trị liệu {sess.index_no} - {instance.service.name if instance.service else ''}",
                        is_treatment=True,
                        has_come=False,
                        receiving_day=d_obj,
                        set_date=t_obj,
                    )
                    sess.booking = bk
                    sess.save(update_fields=["booking"])

            # upsert techniques
            for t in s.get("techniques", []):
                item_id          = t.get("id")
                ts_id            = t.get("techical_setting_id")
                expert_ids       = t.get("expert_ids", [])
                duration_minutes = t.get("duration_minutes", 10)
                room             = t.get("room")
                has_come         = t.get("has_come", False)

                if item_id:
                    item = (
                        SessionTechicalSetting.objects
                        .select_for_update()
                        .filter(id=item_id, session=sess)
                        .first()
                    )
                    if not item:
                        raise serializers.ValidationError(f"Item id={item_id} không thuộc buổi {sess.id}.")
                    if ts_id:
                        ts = TechicalSetting.objects.filter(id=ts_id).first()
                        if not ts:
                            raise serializers.ValidationError("Kỹ thuật không tồn tại.")
                        if (hasattr(ts, "service_id")
                            and ts.service_id
                            and instance.service_id
                            and ts.service_id != instance.service_id):
                            raise serializers.ValidationError("Kỹ thuật không thuộc dịch vụ đã chọn.")
                        item.techical_setting = ts
                    item.duration_minutes = duration_minutes
                    item.room = room
                    item.has_come = has_come
                    if expert_ids is not None:
                        item.expert_id = (expert_ids[0] if expert_ids else None)  # cập nhật expert
                    item.save()
                else:
                    ts = TechicalSetting.objects.filter(id=ts_id).first()
                    if not ts:
                        raise serializers.ValidationError("Kỹ thuật không tồn tại.")
                    if (hasattr(ts, "service_id")
                        and ts.service_id
                        and instance.service_id
                        and ts.service_id != instance.service_id):
                        raise serializers.ValidationError("Kỹ thuật không thuộc dịch vụ đã chọn.")
                    expert_id = (expert_ids[0] if expert_ids else None)
                    SessionTechicalSetting.objects.create(
                        session=sess,
                        techical_setting=ts,
                        duration_minutes=duration_minutes,
                        room=room,
                        has_come=has_come,
                        expert_id=expert_id,
                    )

        return instance

class BillListSerializer(serializers.ModelSerializer):
    # annotate từ ViewSet
    source_type = serializers.CharField(read_only=True)
    source_id   = serializers.CharField(read_only=True)  # object_id có thể là str/UUID

    # QUAN HỆ
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    customer_details = CustomerGetSerializer(source="customer", read_only=True)
    doctor_process_details = serializers.SerializerMethodField(read_only=True)

    # TÍNH TOÁN
    total_amount = serializers.SerializerMethodField()
    total_amount_real = serializers.SerializerMethodField()
    amount_remaining = serializers.SerializerMethodField()
    total_product_amount = serializers.SerializerMethodField()
    total_service_amount = serializers.SerializerMethodField()
    customer_total_billed = serializers.SerializerMethodField()
    customer_total_paid = serializers.SerializerMethodField()
    package_services_total = serializers.SerializerMethodField()
    technical_used_total = serializers.SerializerMethodField()

    # USER / SESSIONS
    doctor = serializers.SerializerMethodField()
    treatment_request = TreatmentRequestSerializer(many=True, read_only=True)
    treatment_sessions = serializers.ListField(write_only=True, required=False)

    treatment_sessions_remaining = serializers.SerializerMethodField()
    treatment_sessions_done = serializers.SerializerMethodField()
    uncompleted_sessions_tlcbs = serializers.SerializerMethodField()
    completed_sessions_tlcbs = serializers.SerializerMethodField()
    uncompleted_sessions_tldss = serializers.SerializerMethodField()
    completed_sessions_tldss = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = [
            # ids & meta
            'id', 'created', 'user', 'code', 'doctor',
            # loại hóa đơn (annotate)
            'source_type', 'source_id',

            # quan hệ
            'customer', 'customer_details', 'doctor_process_details',

            # thanh toán (đúng tên field trên model Bill của bạn)
            'method', 'paid_ammount', 'fully_paid', 'note',

            # tính toán
            'total_amount', 'total_amount_real', 'amount_remaining',
            'total_product_amount', 'total_service_amount',
            'customer_total_billed', 'customer_total_paid',
            'package_services_total', 'technical_used_total',

            # sessions
            'treatment_request', 'treatment_sessions',
            'treatment_sessions_remaining', 'treatment_sessions_done',
            'uncompleted_sessions_tlcbs', 'completed_sessions_tlcbs',
            'uncompleted_sessions_tldss', 'completed_sessions_tldss',
        ]
        read_only_fields = ['id', 'created', 'code', 'fully_paid']

    # -------------- methods --------------
    def get_package_services_total(self, obj):
        return obj.get_total_service_amount()

    def get_technical_used_total(self, obj):
        total = 0
        for tr in obj.treatment_requests.all():
            total += tr.get_total_price_is_done_treatment_sessions()
        return total

    def get_total_amount(self, obj): return obj.get_total_amount()
    def get_total_amount_real(self, obj): return obj.get_total_amount_real()
    def get_amount_remaining(self, obj): return obj.amount_remaining()
    def get_total_product_amount(self, obj): return obj.get_total_product_amount()
    def get_total_service_amount(self, obj): return obj.get_total_service_amount()
    def get_customer_total_billed(self, obj): return obj.get_customer_total_billed()
    def get_customer_total_paid(self, obj): return obj.get_customer_total_paid()

    def get_doctor_process_details(self, obj):
        dp = obj.customer.doctor_process.order_by('-id').first() if obj.customer else None
        return DoctorProcessSerializer(dp, context=self.context).data if dp else None

    def get_doctor(self, obj):
        doctor = obj.get_doctor()
        return getattr(doctor, "username", None) if doctor else None

    # ==== SESSIONS ====
    def get_treatment_sessions_remaining(self, obj):
        return obj.get_treatment_sessions_remaining()

    def get_treatment_sessions_done(self, obj):
        return obj.get_treatment_sessions_done()

    def get_uncompleted_sessions_tlcbs(self, obj):
        return obj.get_uncompleted_sessions_for_tlcb_service()

    def get_completed_sessions_tlcbs(self, obj):
        return obj.get_completed_sessions_for_tlcb_service()

    def get_uncompleted_sessions_tldss(self, obj):
        return obj.get_uncompleted_sessions_for_tlds_service()

    def get_completed_sessions_tldss(self, obj):
        return obj.get_completed_sessions_for_tlds_service()

class PaymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentHistory
        fields = '__all__'
        read_only_fields = ('customer', 'user', 'code', 'created')

    def validate(self, attrs):
        ar = attrs['ar_item']
        amt = attrs['paid_amount']
        if amt <= 0:
            raise serializers.ValidationError("Số tiền phải > 0.")
        # TÍNH remaining TRỰC TIẾP (tránh phụ thuộc property)
        remaining = (ar.amount_original or Decimal('0')) - (ar.amount_paid or Decimal('0'))
        if amt > remaining:
            raise serializers.ValidationError("Số tiền vượt quá dư nợ của phiếu công nợ.")
        return attrs

    def create(self, validated):
        request = self.context['request']
        ar = validated['ar_item']
        validated['customer'] = ar.customer
        validated['user'] = request.user
        if not validated.get('code'):
            validated['code'] = f"PMT{timezone.now():%Y%m%d%H%M%S}"
        with transaction.atomic():
            pmt = super().create(validated)
            # cập nhật ARItem
            ar.amount_paid = (ar.amount_paid or Decimal('0')) + pmt.paid_amount
            ar.status = 'closed' if ar.amount_paid >= ar.amount_original else 'partial'
            ar.save(update_fields=['amount_paid', 'status'])
        return pmt

class ReExaminationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReExamination
        fields = '__all__'

class ReExaminationDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReExamination
        fields = ['status' , 'appointment_date']

class GetCustomerSerializer(serializers.ModelSerializer):
    source_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = ['id', 'name', 'mobile', 'email', "source_details",]
        read_only_fields = fields

class DiagnoseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProcess
        fields = ['id', 'start_time', 'end_time']
        read_only_fields = fields
class BillNeedSerializer(serializers.ModelSerializer):
    customer_info = GetCustomerSerializer(source="customer", read_only=True)
    treatment_sessions = serializers.ListField(write_only=True, required=False)
    doctor = serializers.SerializerMethodField(read_only=True)

    diagnose = serializers.SerializerMethodField(read_only=True)   # ✅ đổi sang method
    treatment_sessions_done = serializers.SerializerMethodField(read_only=True)
    uncompleted_sessions_tlcbs = serializers.SerializerMethodField()
    completed_sessions_tlcbs = serializers.SerializerMethodField(read_only=True)
    uncompleted_sessions_tldss = serializers.SerializerMethodField()
    completed_sessions_tldss = serializers.SerializerMethodField(read_only=True)
    re_examination_date = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Bill
        fields = [
            'id','code', 'created', 'user', 'customer_info', 'doctor',
            're_examination_date', 'diagnose', 'method', 'treatment_sessions', 'note',
            'treatment_sessions_done', 'uncompleted_sessions_tlcbs', 'completed_sessions_tlcbs',
            'uncompleted_sessions_tldss','completed_sessions_tldss'
        ]

    def get_diagnose(self, obj):
        """
        Lấy 1 DoctorProcess đại diện gần nhất (tuỳ bạn: theo start_time hoặc id mới nhất)
        """
        try:
            dhc = obj.customer.doctor_health_check
            ce = getattr(dhc, "clinical_examination", None)
            if not ce:
                return None
            dp = ce.doctor_process.order_by('-id').first()  # hoặc '-start_time'
            if not dp:
                return None
            return DiagnoseSerializer(dp).data
        except Exception:
            return None

    def get_treatment_sessions_done(self, obj) -> int:
        return obj.get_treatment_sessions_done()

    def get_doctor(self, obj):
        doctor = obj.get_doctor()
        return doctor.username if doctor else None

    def get_completed_sessions_tlcbs(self, obj):
        return obj.get_completed_sessions_for_tlcb_service()

    def get_completed_sessions_tldss(self, obj):
        return obj.get_completed_sessions_for_tlds_service()


    def get_re_examination_date(self, obj):
        latest_reexam = obj.reexamination_set.order_by('-created_at').first()
        if latest_reexam:
            return ReExaminationDateSerializer(latest_reexam).data
        return None

    def get_uncompleted_sessions_tldss(self, obj):
        return obj.get_uncompleted_sessions_for_tlds_service()

    def get_uncompleted_sessions_tlcbs(self, obj):
        return obj.get_uncompleted_sessions_for_tlcb_service()

class UserServiceStatsSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    total_tlcb = serializers.SerializerMethodField()
    total_tlds = serializers.SerializerMethodField()
    amount_tlcb = serializers.SerializerMethodField()
    amount_tlds = serializers.SerializerMethodField()
    amount_total = serializers.SerializerMethodField()
    contract_type = serializers.CharField(
        source="user_profile.hr_profile.contract_type", read_only=True
    )
    contract_type_display = serializers.CharField(
        source="user_profile.hr_profile.get_contract_type_display", read_only=True
    )

    class Meta:
        model = User
        fields = (
            "id", "full_name",
            "total_tlcb", "total_tlds",
            "amount_tlcb", "amount_tlds", "amount_total",
            "contract_type",
            "contract_type_display",
        )

    def get_full_name(self, obj):
        fn = getattr(obj, "get_full_name", None)
        name = fn() if callable(fn) else None
        if name:
            return name
        parts = [getattr(obj, "first_name", "") or "", getattr(obj, "last_name", "") or ""]
        name2 = " ".join(p for p in parts if p).strip()
        return name2 or getattr(obj, "username", str(obj.pk))

    # ----- Lọc theo thời gian & base queryset -----
    def _base_qs(self, obj):
        """
        Lấy queryset SessionTechicalSetting mà user là expert,
        có áp dụng lọc thời gian theo TreatmentRequest.created_at.
        """
        request = self.context.get("request")
        qs = SessionTechicalSetting.objects.filter(expert=obj)

        if request:
            start = request.query_params.get("start")
            end = request.query_params.get("end")
            if start:
                d = parse_date(start)
                if d:
                    qs = qs.filter(session__treatment_request__created_at__date__gte=d)
            if end:
                d = parse_date(end)
                if d:
                    qs = qs.filter(session__treatment_request__created_at__date__lte=d)
        return qs

    # ----- Đếm số phác đồ (distinct TreatmentRequest) theo loại -----
    def _count_plans_by_service_type(self, obj, service_type):
        """Đếm số phác đồ (distinct TreatmentRequest) theo loại dịch vụ"""
        qs = self._base_qs(obj).filter(
            session__treatment_request__service__type=service_type
        )
        return qs.values("session__treatment_request_id").distinct().count()

    def get_total_tlcb(self, obj):
        return self._count_plans_by_service_type(obj, "TLCB")

    def get_total_tlds(self, obj):
        return self._count_plans_by_service_type(obj, "TLDS")

    # ----- Tính tiền công theo loại -----
    def _amount_by_service_type(self, obj, service_type):
        """Tính tổng tiền cho expert này theo loại dịch vụ"""
        qs = self._base_qs(obj).filter(
            session__treatment_request__service__type=service_type,
            has_come=True,  # chỉ tính kỹ thuật đã thực hiện
            expert=obj      # chỉ tính kỹ thuật mà user này là expert
        )
        
        # Tổng giá trị kỹ thuật đã thực hiện
        agg = qs.aggregate(total=Sum("techical_setting__price"))
        return agg["total"] or Decimal('0')

    def get_total_tlcb(self, obj):
        """Đếm số lượt thực hiện kỹ thuật TLCB"""
        return self._base_qs(obj).filter(
            session__treatment_request__service__type="TLCB",
            has_come=True,
            expert=obj
        ).count()

    def get_total_tlds(self, obj):
        """Đếm số lượt thực hiện kỹ thuật TLDS"""
        return self._base_qs(obj).filter(
            session__treatment_request__service__type="TLDS", 
            has_come=True,
            expert=obj
        ).count()

    def get_amount_total(self, obj):
        # Tổng tiền công từ cả 2 loại
        return (self.get_amount_tlcb(obj) or 0) + (self.get_amount_tlds(obj) or 0)
    
class ARPaymentBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentHistory
        fields = ('id','code','created','paid_amount','paid_method')
    
class ARItemSerializer(serializers.ModelSerializer):
    payment_histories = ARPaymentBriefSerializer(many=True, read_only=True)
    amount_remaining = serializers.DecimalField(max_digits=25, decimal_places=2, read_only=True)

    source_type = serializers.SerializerMethodField(read_only=True)
    source_id   = serializers.IntegerField(source="object_id", read_only=True)
    
    def get_source_type(self, obj):
        # trả về tên model ở dạng lowercase: "treatmentrequest" / "doctorprocess"
        return getattr(obj.content_type, "model", None)
    
    class Meta:
        model = ARItem
        fields = ('id','customer','amount_original','amount_paid','amount_remaining','status',
                  'payment_histories', 'source_type','source_id', 'created')
