from rest_framework import serializers
from django.contrib.auth.models import User
from app_customer.models import Customer
from app_home.models import  TestService, TreatmentPackage, UserProfile, DetailFunction, FunctionCategory,Position, Department, Floor,\
Protocol, Commission, Discount, LeadSource, TimeFrame, Unit
from drf_spectacular.utils import extend_schema_field
from datetime import datetime
from app_customer.models import Referral
from app_hr.models import HrUserProfile
from django.db.models import Q

# set up profile
class UserNameSerializer(serializers.ModelSerializer):
    # Serializer to return the full name of a user
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id','full_name']

    def get_full_name(self, obj) -> str:
        # Return the full name of the user
        return f"{obj.first_name} {obj.last_name}"
    
class UserProfileSerializer(serializers.ModelSerializer):
    position = serializers.SerializerMethodField()  # Thêm trường tùy chỉnh
    detail_function = serializers.SerializerMethodField()  # Thêm trường tùy chỉnh
    introduced_customer_count = serializers.SerializerMethodField()  # Thêm trường này!

    class Meta:
        model = UserProfile
        fields = "__all__"

    def get_position(self, obj):
        if obj.position:
            position_data = PositionSerializer(obj.position).data
            return position_data
        else:
            return None
    def get_introduced_customer_count(self, obj):
        """
        Đếm số khách do user (nhân sự) này giới thiệu:
        - qua Referral.ref_type='hr' (ref_hr)
        - hoặc qua Referral.ref_type='actor' mà LeadSourceActor.hr_profile = nhân sự này
        """
        user = getattr(obj, "user", None)  # obj là UserProfile
        if not user:
            return 0

        hr = HrUserProfile.objects.filter(user_id=user.id).only("id").first()
        if not hr:
            return 0

        return Referral.objects.filter(
            Q(ref_type="hr", ref_hr_id=hr.id) |
            Q(ref_type="actor", ref_actor__hr_profile_id=hr.id)
        ).count()
    # Định nghĩa phương thức để trả về thông tin Detail Function của User
    def get_detail_function(self, obj):
        try:
            detail_function_list = DetailFunction.objects.filter(
                user_profile_detail_function__user_profile=obj
            )
            detail_function_data = DetailFunctionSerializer(detail_function_list, many=True).data
            return detail_function_data
        except UserProfile.DoesNotExist:
            return None

class UserSerializer(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField()  # Thêm trường tùy chỉnh
    date_joined = serializers.SerializerMethodField() # Thêm trường tùy chỉnh
    full_name = serializers.SerializerMethodField() # Thêm trường tùy chỉnh

    class Meta:
        model = User
        fields = "__all__"

    def get_date_joined(self, obj):
        return obj.date_joined.strftime('%Y-%m-%d %H:%M:%S')

    def get_full_name(self, obj) -> str:
        return obj.get_full_name()

    # Định nghĩa phương thức để trả về thông tin UserProfile của User
    def get_user_profile(self, obj):
        try:
            user_profile = UserProfile.objects.get(user=obj)  # Lấy UserProfile tương ứng với User
            return UserProfileSerializer(user_profile).data
        except UserProfile.DoesNotExist:
            return None

class SimplifiedUserProfileSerializer(serializers.ModelSerializer):
    position = serializers.SerializerMethodField()  # Thêm trường tùy chỉnh
    
    class Meta:
        model = UserProfile
        fields = ['gender', 'user_mobile_number', 'user_address', 'image', 
                  'desc', 'position',]
        read_only_fields = fields

    def get_position(self, obj):
        if obj.position:
            position_data = PositionSerializer(obj.position).data
            return position_data
        else:
            return None

class SimplifiedUserSerializer(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField()  # Thêm trường tùy chỉnh
    date_joined = serializers.SerializerMethodField() # Thêm trường tùy chỉnh

    class Meta:
        model = User
        fields = ['date_joined', 'last_login', 'username', 'first_name', 'last_name', 'email', 'user_profile']
        read_only_fields = fields
    @extend_schema_field(datetime)
    def get_date_joined(self, obj):
        return obj.date_joined.strftime('%Y-%m-%d %H:%M:%S')

    # Định nghĩa phương thức để trả về thông tin UserProfile của User
    @extend_schema_field(dict)
    def get_user_profile(self, obj):
        try:
            user_profile = UserProfile.objects.get(user=obj)  # Lấy UserProfile tương ứng với User
            return SimplifiedUserProfileSerializer(user_profile).data
        except UserProfile.DoesNotExist:
            return None

class FunctionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FunctionCategory
        fields = ['id', 'title',]
        read_only_fields = fields

class DetailFunctionSerializer(serializers.ModelSerializer):
    category_str = serializers.StringRelatedField(source='category', read_only=True)

    class Meta:
        model = DetailFunction
        fields = ['id', 'category_str', 'title', 'link', ]
        read_only_fields = fields

class PositionSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source="department.name")
    class Meta:
        model = Position
        fields = ['id', 'created', 'user', 'department', 'department_name', 'code', 'title', 'performance_coefficient']
        read_only_fields = ['id', 'created', 'user']
        
    def validate_code(self, value):
        # Check for existing code during creation
        if self.instance is None:  # Create case
            if Position.objects.filter(code=value).exists():
                raise serializers.ValidationError("Mã chức vụ đã tồn tại.")
        # Check for existing code during update
        else:  # Update case
            if Position.objects.filter(code=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Mã chức vụ đã tồn tại.")
        return value

class DepartmentSerialzier(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"
        read_only_fields = ['id', 'created', 'user']
        
    def validate_code(self, value):
        # Check for existing code during creation
        if self.instance is None:  # Create case
            if Department.objects.filter(code=value).exists():
                raise serializers.ValidationError("Mã phòng ban đã tồn tại.")
        # Check for existing code during update
        else:  # Update case
            if Department.objects.filter(code=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Mã phòng ban đã tồn tại.")
        return value

class FloorSerialzier(serializers.ModelSerializer):
    class Meta:
        model = Floor
        fields = "__all__"
        read_only_fields = ['id', 'created', 'user']
        
    def validate_code(self, value):
        # Check for existing code during creation
        if self.instance is None:  # Create case
            if Floor.objects.filter(code=value).exists():
                raise serializers.ValidationError("Mã tầng đã tồn tại.")
        # Check for existing code during update
        else:  # Update case
            if Floor.objects.filter(code=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Mã tầng đã tồn tại.")
        return value

#for other fields

class ProtocolSerialzier(serializers.ModelSerializer):
    class Meta:
        model = Protocol
        fields = "__all__"
        read_only_fields = ['id', 'created', 'user']

class CommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commission
        fields = "__all__"
        read_only_fields = ['id', 'created', 'user']

class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = "__all__"
        read_only_fields = ['id', 'created', 'user']

class LeadSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadSource
        fields = "__all__"
        read_only_fields = ['id', 'created', 'user']

class TimeFrameSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeFrame
        fields = "__all__"
        read_only_fields = ['id', 'created', 'user']

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = "__all__"
        read_only_fields = ['id', 'created', 'user']
# password reset
# class PasswordResetRequestSerializer(serializers.Serializer):
#     email = serializers.EmailField()

#     def validate_email(self, value):
#         try:
#             user = User.objects.get(email=value)
#         except User.DoesNotExist:
#             raise serializers.ValidationError("Email không tồn tại.")
#         return value

#     def save(self):
#         email = self.validated_data['email']
#         user = User.objects.get(email=email)
#         self.send_reset_email(user)

# class PasswordResetSerializer(serializers.Serializer):
#     uidb64 = serializers.CharField()
#     token = serializers.CharField()
#     new_password = serializers.CharField(write_only=True)

#     def validate(self, data):
#         try:
#             uid = urlsafe_base64_decode(data['uidb64']).decode()
#             self.user = User.objects.get(pk=uid)
#         except (TypeError, ValueError, OverflowError, User.DoesNotExist):
#             raise serializers.ValidationError("Liên kết đặt lại mật khẩu không hợp lệ.")

#         if not default_token_generator.check_token(self.user, data['token']):
#             raise serializers.ValidationError("Token không hợp lệ hoặc đã hết hạn.")

#         return data

#     def save(self):
#         new_password = self.validated_data['new_password']
#         self.user.set_password(new_password)
#         self.user.save()

class TreatmentPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentPackage
        fields = ['id', 'value', 'name', 'note']

class TestServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestService
        fields = '__all__'