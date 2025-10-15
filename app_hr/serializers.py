from collections import defaultdict
from rest_framework import serializers

from app_home.models import Position
from .models import HrUserProfile
from app_home.serializers import UserNameSerializer, PositionSerializer
import base64
import boto3
from thabicare_admin.base import *
from app_treatment.models import TreatmentRequest, SessionTechicalSetting, TreatmentSession
from django.contrib.auth import get_user_model
User = get_user_model()

class HrUserProfileSerializer(serializers.ModelSerializer):
    contract_base64 = serializers.SerializerMethodField()
    full_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_null=True)
    mobile = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    code = serializers.CharField(read_only=True)
    
    position = PositionSerializer(read_only=True)
    
    department = serializers.SerializerMethodField()  # New field
    expert_done_session_exp = serializers.SerializerMethodField()
    expert_done_session_ser = serializers.SerializerMethodField()
    expert_salary = serializers.SerializerMethodField()
    expert_services = serializers.SerializerMethodField()
    
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        queryset=User.objects.all(),
        write_only=True,
        required=False,  # <-- quan trọng
        allow_null=True
    )
    user = serializers.IntegerField(source='user.id', read_only=True)
    
    position_id = serializers.PrimaryKeyRelatedField(
        source='position',
        queryset=Position.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = HrUserProfile
        fields = [
            'id','user','user_id','user_profile', 'code',
            'contract','contract_start','contract_end','contract_status',
            'contract_type', 'type', 'position_id',
            'start_date','level','calculate_seniority','full_name','mobile','email','position','department',
            'contract_base64','expert_done_session_exp','expert_done_session_ser','expert_salary','expert_services'
        ]
        read_only_fields = ['id','created','user','position']

    def get_expert_done_session_exp(self, obj):
        return obj.calculate_expert_done_session_exp()

    def get_expert_done_session_ser(self, obj) -> str:
        return obj.calculate_expert_done_session_ser()

    def get_expert_salary(self, obj) -> float:
        return obj.calculate_expert_salary()

    def get_contract_base64(self, obj) -> str:
        if obj.contract:
            try:
                key = obj.contract.name   # Sử dụng tên file từ trường 'file'
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=env("AWS_S3_ACCESS_KEY_ID"),
                    aws_secret_access_key=env("AWS_S3_SECRET_ACCESS_KEY"),
                    # region_name=env("AWS_S3_REGION_NAME")
                )
                response = s3.get_object(
                    Bucket=env("AWS_STORAGE_BUCKET_NAME"),
                    Key=key
                )
                file_content = response['Body'].read()
                return base64.b64encode(file_content).decode()
            except Exception as e:
                print(f"Error: {str(e)}")
    
    def get_department(self, obj):
        if obj.position and obj.position.department:
            return obj.position.department.name
        return None
    
    def get_expert_services(self, obj):
        # ✅ Không truy cập obj.user (có thể bắn DoesNotExist); dùng obj.user_id
        if not obj.user_id:
            return {}

        qs = (
            SessionTechicalSetting.objects
            .filter(expert_id=obj.user_id)  # ✅ dùng *_id
            .select_related(
                "expert",
                "techical_setting",
                "session__booking__customer",
                "session__treatment_request__service",
                "session__treatment_request__bill__customer",
                "session__treatment_request__bill",
            )
        )

        data_by_type = defaultdict(dict)

        for sts in qs:
            sess = sts.session
            tr = getattr(sess, "treatment_request", None)
            service = getattr(tr, "service", None)
            service_type = getattr(service, "type", None) or "UNKNOWN"

            booking = getattr(sess, "booking", None)
            bill = getattr(tr, "bill", None)
            customer = getattr(booking, "customer", None) or (getattr(bill, "customer", None) if bill else None)

            customer_name = getattr(customer, "name", None)
            service_name = getattr(service, "name", None)
            created_at = getattr(bill, "created", None)

            sid = sess.id
            bucket = data_by_type[service_type].setdefault(
                sid,
                {
                    "session_id": sid,
                    "customer_name": customer_name,
                    "service_name": service_name,
                    "created_at": created_at,
                    "participation_count": 0,
                    "total_price": 0,
                    "techniques": {},
                },
            )

            # Với FK expert: 100% thời lượng/tiền cho 1 người
            try:
                bucket["participation_count"] += sts.calculate_expert_time() or 1
            except Exception:
                bucket["participation_count"] += 1

            try:
                bucket["total_price"] += sts.calculate_expert_payment() or 0
            except Exception:
                bucket["total_price"] += getattr(sts.techical_setting, "price", 0) or 0

            ts = sts.techical_setting
            if ts:
                tkey = ts.id
                t_bucket = bucket["techniques"].setdefault(
                    tkey,
                    {
                        "technique_id": ts.id,
                        "technique_name": ts.name,
                        "technique_price": getattr(ts, "price", 0),
                        "usage_count": 0,
                    },
                )
                t_bucket["usage_count"] += 1

        out = {}
        for s_type, sessions_map in data_by_type.items():
            out[s_type] = []
            for _sid, v in sessions_map.items():
                v = dict(v)
                v["techniques"] = list(v["techniques"].values())
                out[s_type].append(v)
        return out