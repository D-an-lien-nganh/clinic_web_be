from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, Q
from decimal import Decimal
from app_customer.models import LeadSourceActor
from rest_framework.validators import UniqueTogetherValidator
import re
from datetime import datetime
from rest_framework.validators import UniqueValidator

from .models import (
    CustomerRequest, LeadStatus, TreatmentState, Customer, CustomerCare, FeedBack,
    customer_introducers, CustomerProblem, CustomerLevel, Referral
)
from app_home.serializers import SimplifiedUserSerializer, TimeFrameSerializer
from app_treatment.models import TreatmentRequest, SessionTechicalSetting, ARItem

User = get_user_model()


class LeadStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadStatus
        fields = "__all__"
        read_only_fields = ['id', 'created', 'user']


class TreatmentStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentState
        fields = "__all__"
        read_only_fields = ['id', 'created', 'user']


class CustomerLevelSerializer(serializers.ModelSerializer):
    treatment_state = serializers.PrimaryKeyRelatedField(
        many=True, queryset=TreatmentState.objects.all(),
        required=False, allow_null=True
    )
    lead_status = serializers.PrimaryKeyRelatedField(
        many=True, queryset=LeadStatus.objects.all(),
        required=False, allow_null=True
    )

    class Meta:
        model = CustomerLevel
        fields = "__all__"
        read_only_fields = ['id', 'created', 'user']

    def validate(self, data):
        # customer_type: '1' = chưa mua → không được set treatment_state
        if data.get('customer_type') == '1':
            if data.get('treatment_state') not in [None, []]:
                raise serializers.ValidationError({
                    "treatment_state": "Treatment state must be empty or null when customer_type is 1."
                })
        else:
            # customer_type 2 hoặc 3 → không được set lead_status
            if data.get('lead_status') not in [None, []]:
                raise serializers.ValidationError({
                    "lead_status": "Lead status must be empty or null when customer_type is 2 or 3."
                })
        return data


class CustomerProblemSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = CustomerProblem
        fields = ['id', 'user', 'customer', 'customer_name',
                  'problem', 'encounter_pain', 'desire']
        read_only_fields = ['id', 'user', 'customer', 'customer_name']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Giữ nguyên cách bạn đang làm (xóa rồi tạo mới)
        old_data = {
            'problem': instance.problem,
            'encounter_pain': instance.encounter_pain,
            'desire': instance.desire,
            'customer': instance.customer,
            'user': instance.user
        }
        new_data = {
            'problem': validated_data.get('problem', old_data['problem']) if validated_data.get('problem') is not None else old_data['problem'],
            'encounter_pain': validated_data.get('encounter_pain', old_data['encounter_pain']) if validated_data.get('encounter_pain') is not None else old_data['encounter_pain'],
            'desire': validated_data.get('desire', old_data['desire']) if validated_data.get('desire') is not None else old_data['desire'],
            'customer': old_data['customer'],
            'user': self.context['request'].user,
        }
        instance.delete()
        return CustomerProblem.objects.create(**new_data)


class CustomerIntroducerSerializer(serializers.ModelSerializer):
    introducer_name = serializers.SerializerMethodField()
    commission_note = serializers.CharField(source='commission.note', read_only=True)

    class Meta:
        model = customer_introducers
        fields = ['id', 'introducer', 'commission', 'commission_note', 'introducer_name']

    def get_introducer_name(self, obj):
        try:
            if not obj.introducer:
                return None
            if obj.introducer.first_name and obj.introducer.last_name:
                return f"{obj.introducer.first_name} {obj.introducer.last_name}"
            return obj.introducer.username
        except Exception:
            return None


class CustomerRequestSerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomerRequest
        fields = ['id', 'created', 'user', 'user_full_name', 'name', 'code', 'color', 'note']
        read_only_fields = ['id', 'created']

    def get_user_full_name(self, obj):
        if obj.user:
            return f"{obj.user.last_name} {obj.user.first_name}".strip()
        return None


class CustomerSerializer(serializers.ModelSerializer):
    # READ-ONLY
    lead_status_name = serializers.ReadOnlyField(source='lead_status.name')
    treatment_status_name = serializers.ReadOnlyField(source='treatment_status.name')
    time_frame_detail = TimeFrameSerializer(source='time_frame', read_only=True)
    service_names = serializers.SerializerMethodField()
    customer_care_list = serializers.SerializerMethodField()
    main_status_name = serializers.SerializerMethodField()
    
    birth_input = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    birth_date = serializers.DateField(read_only=True)
    birth_raw = serializers.CharField(read_only=True)
    birth_accuracy = serializers.CharField(read_only=True)
    
    customer_problems_detail = CustomerProblemSerializer(
        source="customer_problems", many=True, read_only=True
    )
    
    customer_problems = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        allow_null=True,
        default=list,       # ⬅️ MẶC ĐỊNH RỖNG
    )
    
    code = serializers.CharField(read_only=True)

    latest_service_type = serializers.SerializerMethodField()      # Dịch vụ (TLCB/TLDS) theo phác đồ gần nhất
    treatment_progress   = serializers.SerializerMethodField()     # Trạng thái chữa bệnh (% kỹ thuật đã thực hiện)
    payment_status       = serializers.SerializerMethodField()     # Trạng thái thanh toán (đã trả / công nợ)
    next_visit_date      = serializers.SerializerMethodField()     # Ngày tới khám (từ ngày tạo phác đồ gần nhất)
    
    # ---- REFERRAL (write-only) ----
    referral_type = serializers.ChoiceField(
        choices=[('customer','customer'),('hr','hr'),('actor','actor'),('unknown','unknown')],
        required=False, allow_null=True, write_only=True
    )
    # customer→customer
    referral_customer_id   = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    referral_customer_code = serializers.CharField(required=False, allow_blank=True, write_only=True)
    # hr
    referral_hr_id   = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    referral_hr_code = serializers.CharField(required=False, allow_blank=True, write_only=True)
    # actor
    referral_actor = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    referral_source = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    referral_actor_name        = serializers.CharField(required=False, allow_blank=True, write_only=True)
    referral_actor_code        = serializers.CharField(required=False, allow_blank=True, write_only=True)
    referral_actor_external_id = serializers.CharField(required=False, allow_blank=True, write_only=True)
    
    form_referral_type = serializers.SerializerMethodField()
    form_source_id = serializers.SerializerMethodField()
    form_introducer_id = serializers.SerializerMethodField()
    introducer_label = serializers.SerializerMethodField()
    lead_source_name = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'code', 'gender', 'birth', 'carreer',
            'mobile', 'email', 'address', 'district', 'ward', 'city',
            'main_status', 'main_status_name',
            'lead_status', 'lead_status_name',
            'treatment_status', 'treatment_status_name',
            'contact_date', 'time_frame', 'time_frame_detail',
            'service', 'service_names', 'customer_care_list',
            'customer_problems', 'customer_request',
            'customer_problems_detail',

            # birth
            'birth_input', 'birth_date', 'birth_raw', 'birth_accuracy',
            
            'form_referral_type',
            'form_source_id',
            'form_introducer_id',
            'introducer_label',
            'lead_source_name',

            # computed
            'latest_service_type', 'treatment_progress', 'payment_status', 'next_visit_date',

            'referral_type','referral_customer_id','referral_customer_code',
            'referral_hr_id','referral_hr_code',
            'referral_actor','referral_source','referral_actor_name',
            'referral_actor_code','referral_actor_external_id',
        ]
        read_only_fields = [
            'id',
            'service_names', 'time_frame_detail',
            'customer_care_list', 'lead_status_name', 'treatment_status_name',
            'birth_date', 'birth_raw', 'birth_accuracy',
            
            'form_referral_type',
            'form_source_id',
            'form_introducer_id',
            'introducer_label',
            'lead_source_name',
        ]
        
        extra_kwargs = {
            "customer_problems": {"required": False} 
        }
        
    def _ref(self, obj):
        return getattr(obj, 'primary_referral', None)

    def get_form_referral_type(self, obj):
        r = self._ref(obj)
        return r.ref_type if r else None

    def get_form_source_id(self, obj):
        """
        FE cần value cho <Select name="source">.
        - Nếu ref_type == actor: lấy source từ ref_actor.source
        - Nếu customer/hr: nếu bạn có LeadSource “mặc định” cho 2 nhóm này,
          hãy set nó khi tạo/cập nhật và đọc ra ở đây.
          (Nếu hệ thống chưa lưu, trả None để FE tự detect theo tên – như code FE đang làm.)
        """
        r = self._ref(obj)
        # actor → có source thật sự
        if r and r.ref_type == 'actor' and r.ref_actor and r.ref_actor.source:
            return r.ref_actor.source.id

        # customer/hr → nếu bạn có field “fake source” đã lưu đâu đó, trả ở đây.
        # Chưa có? Trả None (FE vẫn chạy vì đã detectReferralType theo tên).
        return None

    def get_lead_source_name(self, obj):
        r = self._ref(obj)
        if r and r.ref_type == 'actor' and r.ref_actor and r.ref_actor.source:
            return r.ref_actor.source.name
        # Với customer/hr nếu bạn có “nguồn mặc định” riêng, có thể trả tên ở đây
        return None

    def get_form_introducer_id(self, obj):
        r = self._ref(obj)
        if not r:
            return None
        if r.ref_type == 'customer' and r.ref_customer:
            return r.ref_customer.id
        if r.ref_type == 'hr' and r.ref_hr:
            return r.ref_hr.id  # FE đang dùng hr_profile_id/id/user → id HrUserProfile là hợp lý
        if r.ref_type == 'actor' and r.ref_actor:
            return r.ref_actor.id
        return None

    def get_introducer_label(self, obj):
        r = self._ref(obj)
        if not r:
            return None
        if r.ref_type == 'customer' and r.ref_customer:
            mobile = r.ref_customer.mobile or r.ref_customer.id
            return f"{r.ref_customer.name} ({mobile})"
        if r.ref_type == 'hr' and r.ref_hr:
            name = getattr(r.ref_hr, 'full_name', None) or f"CTV #{r.ref_hr.id}"
            mobile = getattr(r.ref_hr, 'mobile', None) or r.ref_hr.mobile
            return f"{name} ({mobile})"
        if r.ref_type == 'actor' and r.ref_actor:
            a = r.ref_actor
            tag = a.code or a.external_id
            return f"{a.name}{f' ({tag})' if tag else ''}"
        return None
        
    # ---------- Helpers ----------
    def _normalize_birth(self, s: str):
        if s is None:
            return None, None, None
        s = s.strip()
        if s == "":
            return None, None, None

        # yyyy
        if re.fullmatch(r"\d{4}", s):
            return s, None, "year"

        # mm/yyyy
        if re.fullmatch(r"\d{2}/\d{4}", s):
            mm, yyyy = s.split("/")
            try:
                mm_i = int(mm); yy_i = int(yyyy)
                if 1 <= mm_i <= 12:
                    return s, None, "month"
            except ValueError:
                pass
            raise serializers.ValidationError({"birth_input": "Tháng/năm không hợp lệ (mm/yyyy)."})

        # dd/mm/yyyy
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", s):
            try:
                d = datetime.strptime(s, "%d/%m/%Y").date()
                return s, d, "day"
            except ValueError:
                raise serializers.ValidationError({"birth_input": "Ngày sinh không hợp lệ (dd/mm/yyyy)."})

        raise serializers.ValidationError({"birth_input": "Định dạng phải là yyyy | mm/yyyy | dd/mm/yyyy."})
    
    def _get_latest_tr(self, customer_id: int):
        """
        Lấy phác đồ gần nhất của khách hàng theo created_at desc.
        Ưu tiên liên kết trực tiếp qua TreatmentRequest.customer.
        """
        if not customer_id:
            return None
        return (
            TreatmentRequest.objects
            .filter(
                Q(customer_id=customer_id)
                | Q(treatment_sessions__booking__customer_id=customer_id)  # dự phòng nếu tạo qua session/booking
            )
            .distinct()
            .select_related('service')
            .order_by('-created_at', '-id')
            .first()
        )

    # ---------- Fields ----------
    def get_latest_service_type(self, obj):
        """
        Dịch vụ (TLCB/TLDS) = Service.type của phác đồ gần nhất.
        """
        tr = self._get_latest_tr(obj.id)
        return getattr(getattr(tr, 'service', None), 'type', None) if tr else None

    def get_treatment_progress(self, obj):
        """
        Tính % chữa bệnh theo SỐ BUỔI đã hoàn thành / tổng số buổi theo gói liệu trình.
        
        Logic đúng:
        - total_items = TreatmentPackage.value (số buổi quy định trong gói)
        - done_items = số buổi đã hoàn thành (có ít nhất 1 kỹ thuật has_come=True)
        - percent = (done_items / total_items) * 100
        """
        tr = self._get_latest_tr(obj.id)
        if not tr:
            return {
                "total_items": 0, "done_items": 0, "percent": 0,
                "status_code": "no_plan", "status_label": "Chưa có phác đồ"
            }

        # Lấy tổng số buổi từ gói liệu trình
        treatment_package = getattr(tr, 'treatment_package', None)
        if not treatment_package:
            return {
                "total_items": 0, "done_items": 0, "percent": 0,
                "status_code": "no_package", "status_label": "Chưa có gói liệu trình"
            }

        total_sessions = int(getattr(treatment_package, 'value', 0) or 0)
        if total_sessions <= 0:
            return {
                "total_items": 0, "done_items": 0, "percent": 0,
                "status_code": "invalid_package", "status_label": "Gói liệu trình không hợp lệ"
            }

        # Đếm số BUỔI đã hoàn thành (có ít nhất 1 kỹ thuật has_come=True)
        completed_sessions = (
            SessionTechicalSetting.objects
            .filter(
                session__treatment_request=tr,
                has_come=True
            )
            .values('session_id')  # Group theo buổi
            .distinct()
            .count()
        )

        # Tính phần trăm
        percent = int(round((completed_sessions / total_sessions) * 100)) if total_sessions > 0 else 0

        # Xác định trạng thái
        if completed_sessions == 0:
            status_code, status_label = "not_started", "Chưa bắt đầu"
        elif completed_sessions < total_sessions:
            status_code, status_label = "in_progress", "Đang điều trị"
        else:
            status_code, status_label = "completed", "Hoàn thành"

        return {
            "total_items": total_sessions,           # Từ TreatmentPackage.value
            "done_items": completed_sessions,        # Số buổi đã hoàn thành
            "percent": percent,
            "status_code": status_code,
            "status_label": status_label,
        }

    def get_payment_status(self, obj):
        """
        Tính trạng thái thanh toán dựa trên tổng tiền đã thanh toán / tổng công nợ
        của PHÁC ĐỒ GẦN NHẤT (gắn qua ARItem content_type=TreatmentRequest & object_id=tr.id).
        Trả về: { amount_paid, amount_original, percent, status }
        """
        tr = self._get_latest_tr(obj.id)
        if not tr:
            return {"amount_paid": "0.00", "amount_original": "0.00", "percent": 0, "status": "no_plan"}

        ct = ContentType.objects.get_for_model(TreatmentRequest)
        agg = (ARItem.objects
               .filter(customer_id=obj.id, content_type=ct, object_id=tr.id)
               .aggregate(
                   original=Sum('amount_original'),
                   paid=Sum('amount_paid'),
               ))
        amount_original = agg.get('original') or Decimal('0.00')
        amount_paid     = agg.get('paid') or Decimal('0.00')
        percent = int(round((amount_paid / amount_original) * 100)) if amount_original > 0 else 0

        if amount_original <= 0:
            status = "no_debt"
        elif amount_paid <= 0:
            status = "unpaid"
        elif amount_paid < amount_original:
            status = "partial"
        else:
            status = "paid"

        return {
            "amount_paid": f"{amount_paid:.2f}",
            "amount_original": f"{amount_original:.2f}",
            "percent": percent,
            "status": status,
        }

    def get_next_visit_date(self, obj):
        """
        Ngày tới khám = contact_date lấy từ NGÀY TẠO phác đồ gần nhất.
        Yêu cầu: trả về date (YYYY-MM-DD).
        """
        tr = self._get_latest_tr(obj.id)
        if not tr or not getattr(tr, 'created_at', None):
            return None
        return tr.created_at.date()

    def get_service_names(self, obj):
        return list(obj.service.values_list('name', flat=True))

    def get_customer_care_list(self, obj):
        qs = CustomerCare.objects.filter(customer=obj).order_by('-date')
        return [{"id": x.id, "note": x.note, "date": x.date, "type": x.type, "solidarity": x.solidarity} for x in qs]

    def get_main_status_name(self, obj) -> str:
        mapping = {'1': 'Khách chưa mua', '2': 'Khách đang mua', '3': 'Khách đã mua'}
        return mapping.get(obj.main_status, "Không xác định")
    
    def validate(self, attrs):
        # Không ép gửi referral; nhưng nếu đã gửi thì kiểm tra tối thiểu
        rt = (attrs.get('referral_type') or '').lower()
        if not rt:
            return attrs

        if rt == 'customer':
            if not attrs.get('referral_customer_id') and not attrs.get('referral_customer_code'):
                raise serializers.ValidationError({"referral_customer_code": "Thiếu mã/id khách giới thiệu."})
        elif rt == 'hr':
            if not attrs.get('referral_hr_id') and not attrs.get('referral_hr_code'):
                raise serializers.ValidationError({"referral_hr_code": "Thiếu mã/id CTV/HR giới thiệu."})
        elif rt == 'actor':
            if not (attrs.get('referral_actor') or attrs.get('referral_source') or
                    attrs.get('referral_actor_name') or attrs.get('referral_actor_code') or
                    attrs.get('referral_actor_external_id')):
                raise serializers.ValidationError({"referral_actor": "Thiếu thông tin Actor/Source để ghi nhận."})
        return attrs
    
    def create(self, validated_data):
        # chuẩn hóa code & birth như đang làm
        validated_data.pop('code', None)
        birth_input = self.initial_data.get("birth_input")
        raw, date_val, acc = self._normalize_birth(birth_input)
        validated_data.update({"birth_raw": raw, "birth_date": date_val, "birth_accuracy": acc})
        validated_data.pop("birth", None)
        validated_data.pop("birth_input", None)

        # ==== POP toàn bộ trường referral (chúng KHÔNG phải field của Customer) ====
        referral_payload = {
            "referral_type":           validated_data.pop("referral_type", None),
            "referral_customer_id":    validated_data.pop("referral_customer_id", None),
            "referral_customer_code":  validated_data.pop("referral_customer_code", None),
            "referral_hr_id":          validated_data.pop("referral_hr_id", None),
            "referral_hr_code":        validated_data.pop("referral_hr_code", None),
            "referral_actor":          validated_data.pop("referral_actor", None),
            "referral_source":         validated_data.pop("referral_source", None),
            "referral_actor_name":     validated_data.pop("referral_actor_name", None),
            "referral_actor_code":     validated_data.pop("referral_actor_code", None),
            "referral_actor_external_id": validated_data.pop("referral_actor_external_id", None),
        }

        # Tạo Customer TRƯỚC
        customer = super().create(validated_data)

        # Tạo Referral NẾU có gửi thông tin
        rt = (referral_payload["referral_type"] or "").lower()
        if rt:
            from app_customer.models import LeadSourceActor  # đã dùng ở serializer khác
            ref_kwargs = {"customer": customer, "ref_type": rt}

            if rt == "customer":
                # Ưu tiên id, fallback code
                ref_cus = None
                if referral_payload["referral_customer_id"]:
                    ref_cus = Customer.objects.filter(pk=referral_payload["referral_customer_id"]).first()
                elif referral_payload["referral_customer_code"]:
                    ref_cus = Customer.objects.filter(code=referral_payload["referral_customer_code"].strip().upper()).first()
                ref_kwargs["ref_customer"] = ref_cus

            elif rt == "hr":
                # tùy schema HR, ví dụ app_hr.HrUserProfile
                from app_hr.models import HrUserProfile
                ref_hr = None
                if referral_payload["referral_hr_id"]:
                    ref_hr = HrUserProfile.objects.filter(pk=referral_payload["referral_hr_id"]).first()
                elif referral_payload["referral_hr_code"]:
                    ref_hr = HrUserProfile.objects.filter(code=referral_payload["referral_hr_code"]).first()
                ref_kwargs["ref_hr"] = ref_hr

            elif rt == "actor":
                ref_actor = None
                if referral_payload["referral_actor"]:
                    ref_actor = LeadSourceActor.objects.filter(pk=referral_payload["referral_actor"]).first()
                # (option) có thể tìm/khởi tạo theo source + name/code nếu muốn
                ref_kwargs["ref_actor"] = ref_actor

            # Nếu thông tin không đủ, để 'unknown'
            if rt not in ("customer", "hr", "actor") or all(v is None for k,v in ref_kwargs.items() if k.startswith("ref_")):
                ref_kwargs = {"customer": customer, "ref_type": "unknown"}

            Referral.objects.update_or_create(customer=customer, defaults=ref_kwargs)

        return customer

    def update(self, instance, validated_data):
        validated_data.pop('code', None)
        birth_input = self.initial_data.get("birth_input", None)
        if birth_input is not None:
            raw, date_val, acc = self._normalize_birth(birth_input)
            validated_data.update({
                "birth_raw": raw, "birth_date": date_val, "birth_accuracy": acc
            })
        validated_data.pop("birth", None)
        validated_data.pop("birth_input", None)
        return super().update(instance, validated_data)

class CustomerCareSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.name')
    customer_mobile = serializers.ReadOnlyField(source='customer.mobile')

    class Meta:
        model = CustomerCare
        fields = ['id', 'date', 'note', 'type', 'customer',
                  'customer_name', 'customer_mobile', 'solidarity']
        read_only_fields = ['id']

class LeadSourceActorSerializer(serializers.ModelSerializer):
    source_name = serializers.ReadOnlyField(source='source.name')
    class Meta:
        model = LeadSourceActor
        fields = ['id', 'source', 'source_name', 'name', 'code', 'external_id', 'hr_profile', 'note']
        validators = [
                    UniqueTogetherValidator(
                        queryset=LeadSourceActor.objects.all(),
                        fields=('source', 'name'),
                        message='Actor với name này đã tồn tại trong nguồn.'
                    )
                ]
class FeedBackSerializer(serializers.ModelSerializer):
    service_names = serializers.SerializerMethodField()
    source_name = serializers.ReadOnlyField(source='source.name')

    class Meta:
        model = FeedBack
        fields = [
            'id', 'name', 'source', 'source_name', 'source_link', 'format', 'gender', 'email', 'mobile',
            'service', 'service_names',
            'satification_level', 'service_quality', 'examination_quality', 'serve_quality',
            'customercare_quality', 'unsatify_note', 'suggest_note', 'created'
        ]
        read_only_fields = ['id', 'service_names', 'created']

    @extend_schema_field(list)
    def get_service_names(self, obj):
        return list(obj.service.values_list('name', flat=True))
