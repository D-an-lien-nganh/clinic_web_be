
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.hashers import make_password
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.decorators import api_view, permission_classes
from rest_framework import viewsets, status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from .pagination import CustomPagination
from rest_framework.exceptions import ValidationError

from .models import FunctionCategory, DetailFunction, UserProfile,\
Position, Department, Floor,\
Protocol, Commission, Discount, LeadSource, TimeFrame, Unit
from .serializers import SimplifiedUserSerializer, FunctionCategorySerializer, DetailFunctionSerializer, UserSerializer,\
PositionSerializer, DepartmentSerialzier, FloorSerialzier,\
ProtocolSerialzier, CommissionSerializer, DiscountSerializer, LeadSourceSerializer, TimeFrameSerializer, UnitSerializer

from .docs import *
@extend_schema(tags=["app_home"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_available_functions(request):
    response = {}
    function_default = DetailFunction.objects.filter(function_default=True)
    user_profile = UserProfile.objects.get(user=request.user)
    response["is_admin"] = user_profile.is_admin
    user_functions = user_profile.detail_function.all()
    available_functions = user_functions.union(function_default)
    merged_functions = list({func.pk: func for func in available_functions}.values())
    function_category_id_list = set(func.category_id for func in merged_functions)
    function_category_list = FunctionCategory.objects.filter(id__in=function_category_id_list).order_by('code')
    response["categories"] = []
    for category in function_category_list:
        category_data = FunctionCategorySerializer(category).data
        detail_function_list = sorted(
            [func for func in merged_functions if func.category_id == category.id],
            key=lambda x: x.code
        )
        if detail_function_list:
            detail_function_data = DetailFunctionSerializer(detail_function_list, many=True).data
            category_data["detail_function_list"] = detail_function_data
        response["categories"].append(category_data)
    return Response(response, status=status.HTTP_200_OK)

@extend_schema(tags=["app_home"])
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_all_functions(request):
    try:
        response = {}
        all_functions = DetailFunction.objects.all().order_by('code')
        category_ids = set(func.category_id for func in all_functions if func.category_id is not None)
        categories = FunctionCategory.objects.filter(id__in=category_ids).order_by('code')
        
        response["categories"] = []
        
        # Build response with categories and their functions
        for category in categories:
            category_data = FunctionCategorySerializer(category).data
            
            # Get and sort functions for this category
            category_functions = [func for func in all_functions if func.category_id == category.id]
            
            if category_functions:
                detail_function_data = DetailFunctionSerializer(category_functions, many=True).data
                category_data["detail_function_list"] = detail_function_data
                
            response["categories"].append(category_data)
        
        return Response(response, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {"error": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@extend_schema(tags=["app_home"])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_list(request):
    users = User.objects.filter(is_active=True)
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

class CollaboratorReadOnlyPermission(BasePermission):
    def has_permission(self, request, view):
        print("DEBUG:", request.user, request.method)
        return True  # tạm mở full quyền để test

class AdminPermission(BasePermission):
    def has_permission(self, request, view):
        user_profile = UserProfile.objects.filter(user=request.user).first()
        if user_profile and user_profile.is_admin:
            return True
        return False
    
@extend_schema(tags=["app_home"])
@api_view(["POST"])
@permission_classes([])
def userlogin(request):
    data = request.data
    login_field = data.get("username", None)
    password = data.get("password", None)

    if login_field and password:
        user = User.objects.filter(Q(username=login_field) | Q(email=login_field) | Q(user_profile__user_mobile_number=login_field)).distinct().first()

        if user and not user.is_active:
            return Response({"detail": "Xin lỗi. Tài khoản đã bị khóa."}, status=status.HTTP_403_FORBIDDEN)
        elif user and user.check_password(password):
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            user_json = SimplifiedUserSerializer(user).data
            response = {
                "user": user_json,
                "access_token": access_token,
                "refresh_token": str(refresh)
            }
            return Response(response, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Xin lỗi. Sai thông tin đăng nhập"}, status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response({"detail": "Phải nhập username hoặc email hoặc số điện thoại và mật khẩu của bạn"}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(tags=["app_home"])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    data = request.data
    user = request.user
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")
    if not user.check_password(current_password):
        return Response({"detail": "Mật khẩu hiện tại sai."}, status=status.HTTP_400_BAD_REQUEST)
    if new_password != confirm_password:
        return Response({"detail": "Xác nhận mật khẩu sai."}, status=status.HTTP_400_BAD_REQUEST)
    user.password = make_password(new_password)
    user.save()
    return Response({"detail": "Đổi mật khẩu thành công."}, status=status.HTTP_200_OK)

@extend_schema(tags=["app_home"])
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    data = request.data
    try:
        # Cập nhật thông tin trong bảng User
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.email = data.get("email", user.email)
        user.save()

        # Cập nhật thông tin trong bảng UserProfile
        user_profile = UserProfile.objects.filter(user=user).first()
        if user_profile:
            user_profile.user_mobile_number = data.get("mobile", user_profile.user_mobile_number)
            user_profile.save()
        else:
            return Response({"detail": "UserProfile không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"detail": "Cập nhật thông tin thành công."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"detail": f"Lỗi trong quá trình cập nhật: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(tags=["app_home"])
class UserAccountView(APIView):
    permission_classes = [IsAuthenticated, AdminPermission]
    pagination_class = CustomPagination

    def get(self, request):
        # Lấy tham số user_id nếu có
        user_id = request.query_params.get('user_id') or request.data.get('user_id')

        # Tạo queryset chỉ gồm những user đang active
        active_qs = User.objects.filter(is_active=True)

        if user_id is not None:
            # Nếu có user_id, tìm user trong queryset active_qs
            user = get_object_or_404(active_qs, id=user_id)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Nếu không có user_id, trả về toàn bộ danh sách user active
        serializer = UserSerializer(active_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        confirm = data.get("confirmPassword")
        user_type = data.get("type")

        # 1. Validate bắt buộc
        if User.objects.filter(username=username, is_active=True).exists():
            return Response({"detail": "Username đã tồn tại."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email, is_active=True).exists():
            return Response({"detail": "Email đã tồn tại."}, status=status.HTTP_409_CONFLICT)
        if password != confirm:
            return Response({"detail": "Xin bạn hãy xác nhận lại đúng mật khẩu."}, status=status.HTTP_406_NOT_ACCEPTABLE)

        # 2. Tạo User và set is_staff nếu là admin
        is_admin = (user_type == "admin")
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            email=email,
            is_staff=is_admin,         # cho DRF IsAdminUser hoặc Django admin
            # is_superuser=is_admin,   # nếu muốn superuser luôn
        )

        # 3. Tạo/ cập nhật Profile
        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        user_profile.user_mobile_number = data.get("numberphone", "000")
        user_profile.type = user_type
        user_profile.is_admin = is_admin
        user_profile.save()

        # 4. Phân quyền chi tiết
        if is_admin:
            # cấp toàn bộ detail-function
            funcs = DetailFunction.objects.all()
            user_profile.detail_function.set(funcs)
        elif user_type in ["employee", "collaborator"]:
            # chỉ cấp những function mà frontend chọn
            ids = data.get("detailFunction", [])
            if ids:
                funcs = DetailFunction.objects.filter(id__in=ids)
                user_profile.detail_function.set(funcs)

            # nếu là employee thì xử lý thêm position
            if user_type == "employee":
                pos_id = data.get("position_id")
                if pos_id:
                    try:
                        user_profile.position = Position.objects.get(id=pos_id)
                        user_profile.save()
                    except Position.DoesNotExist:
                        return Response(
                            {"detail": "Vị trí không tồn tại."},
                            status=status.HTTP_400_BAD_REQUEST
                        )

        # 5. Trả về dữ liệu mới tạo
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        
        data = request.data
        user = get_object_or_404(User, id=data["user_id"])
        serializer = UserSerializer(user, data=request.data, partial=True)  # partial=True cho phép cập nhật một phần dữ liệu
        
        if serializer.is_valid():
            serializer.save()
            user_profile = UserProfile.objects.get(user=user)
            user_profile.user_address = data.get("address", user_profile.user_address)
            user_profile.gender = data.get("gender", user_profile.gender)
            user_profile.user_mobile_number = data.get("numberphone", user_profile.user_mobile_number)
            user_profile.is_admin = data.get("is_admin", user_profile.is_admin)
            user_profile.type = data.get("type", user_profile.type)

            position_id = data.get("position_id")
            if position_id:
                try:
                    position = Position.objects.get(id=position_id)
                    user_profile.position = position
                except Position.DoesNotExist:
                    return Response({"detail": "Vị trí không tồn tại."}, status=status.HTTP_400_BAD_REQUEST)

            user_profile.save()

            # Cập nhật lại các chức năng chi tiết
            if user_profile.is_admin:
                all_detail_functions = DetailFunction.objects.all()
                user_profile.detail_function.set(all_detail_functions)
            elif user_profile.type in ["employee", "collaborator"]:
                if len(data.get("detailFunction", [])) > 0:
                    detail_functions = DetailFunction.objects.filter(id__in=data["detailFunction"])
                    user_profile.detail_function.clear()
                    user_profile.detail_function.set(detail_functions)

            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        
        data = request.data
        user = get_object_or_404(User, id=data["user_id"])

        # Thực hiện soft delete
        user.is_active = False
        current_time_str = timezone.now().strftime('%Y%m%d%H%M%S')
        user.username += f"_locked_{current_time_str}"
        user.save()
        
        return Response({"detail": "Tài khoản đã bị khóa."}, status=status.HTTP_200_OK)
    
@extend_schema(tags=["app_home"])
@api_view(["POST"])
@permission_classes([IsAuthenticated, AdminPermission])
def activate_account(request):
   user_profile = UserProfile.objects.filter(user=request.user).first()
   if not user_profile or not user_profile.is_admin:
       return Response({"detail": "Bạn không có quyền thực hiện hành động này."}, status=status.HTTP_403_FORBIDDEN)
   data = request.data
   try:
       user = get_object_or_404(User, id=data["user_id"])
   except User.DoesNotExist:
       return Response({"detail": "Không tìm thấy tài khoản."}, status=status.HTTP_404_NOT_FOUND)
   if user.is_active:
       return Response({"detail": "Tài khoản đã được kích hoạt."}, status=status.HTTP_400_BAD_REQUEST)

   # Kích hoạt tài khoản
   user.is_active = True
   if "_locked_" in user.username:
       user.username = user.username.split("_locked_")[0]
   user.save()
   
   return Response({"detail": "Tài khoản đã được kích hoạt lại."}, status=status.HTTP_200_OK)
    

@extend_schema(tags=["app_home"])
@position_schema_view()
class PositionViewSet(viewsets.ModelViewSet):
    serializer_class = PositionSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, AdminPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)

        filters = Q()
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (
                Q(title__icontains=search_term) |
                Q(user__username__icontains=search_term)|
                Q(code__icontains=search_term) |
                Q(department__name__icontains=search_term)
            )
            filters &= search_filters
        queryset = Position.objects.filter(filters).order_by('-created')

        return queryset

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            # Trích xuất message từ validation error
            if isinstance(e.detail, dict):
                # Lấy message đầu tiên từ các field errors
                first_error = next(iter(e.detail.values()))
                if isinstance(first_error, list) and first_error:
                    message = first_error[0]
                else:
                    message = str(first_error)
            else:
                message = str(e.detail)
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": "Có lỗi xảy ra khi tạo chức vụ."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data)
        except serializers.ValidationError as e:
            # Trích xuất message từ validation error
            if isinstance(e.detail, dict):
                # Lấy message đầu tiên từ các field errors
                first_error = next(iter(e.detail.values()))
                if isinstance(first_error, list) and first_error:
                    message = first_error[0]
                else:
                    message = str(first_error)
            else:
                message = str(e.detail)
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": "Có lỗi xảy ra khi cập nhật chức vụ."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

@extend_schema(tags=["app_home"])
@department_schema_view()
class DepartmentViewSet(viewsets.ModelViewSet):
    serializer_class = DepartmentSerialzier
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, AdminPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)

        filters = Q()
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (
                Q(name__icontains=search_term) |
                Q(user__username__icontains=search_term)|
                Q(code__icontains=search_term)
            )
            filters &= search_filters
        queryset = Department.objects.filter(filters).order_by('-created')

        return queryset

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            # Trích xuất message từ validation error
            if isinstance(e.detail, dict):
                # Lấy message đầu tiên từ các field errors
                first_error = next(iter(e.detail.values()))
                if isinstance(first_error, list) and first_error:
                    message = first_error[0]
                else:
                    message = str(first_error)
            else:
                message = str(e.detail)
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": "Có lỗi xảy ra khi tạo phòng ban."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data)
        except serializers.ValidationError as e:
            # Trích xuất message từ validation error
            if isinstance(e.detail, dict):
                # Lấy message đầu tiên từ các field errors
                first_error = next(iter(e.detail.values()))
                if isinstance(first_error, list) and first_error:
                    message = first_error[0]
                else:
                    message = str(first_error)
            else:
                message = str(e.detail)
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": "Có lỗi xảy ra khi cập nhật phòng ban."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

@extend_schema(tags=["app_home"])
@floor_schema_view()
class FloorViewSet(viewsets.ModelViewSet):
    serializer_class = FloorSerialzier
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, AdminPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)

        filters = Q()
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (
                Q(name__icontains=search_term) |
                Q(user__username__icontains=search_term)|
                Q(code__icontains=search_term)
            )
            filters &= search_filters
        queryset = Floor.objects.filter(filters).order_by('-created')

        return queryset

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            # Trích xuất message từ validation error
            if isinstance(e.detail, dict):
                # Lấy message đầu tiên từ các field errors
                first_error = next(iter(e.detail.values()))
                if isinstance(first_error, list) and first_error:
                    message = first_error[0]
                else:
                    message = str(first_error)
            else:
                message = str(e.detail)
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": "Có lỗi xảy ra khi tạo tầng."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response(serializer.data)
        except serializers.ValidationError as e:
            # Trích xuất message từ validation error
            if isinstance(e.detail, dict):
                # Lấy message đầu tiên từ các field errors
                first_error = next(iter(e.detail.values()))
                if isinstance(first_error, list) and first_error:
                    message = first_error[0]
                else:
                    message = str(first_error)
            else:
                message = str(e.detail)
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": "Có lỗi xảy ra khi cập nhật tầng."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

@extend_schema(tags=["app_home"])
@protocol_schema_view()
class ProtocolViewSet(viewsets.ModelViewSet):
    serializer_class = ProtocolSerialzier
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, AdminPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)

        filters = Q()
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (
                Q(name__icontains=search_term) |
                Q(user__username__icontains=search_term)|
                Q(code__icontains=search_term)
            )
            filters &= search_filters
        queryset = Protocol.objects.filter(filters).order_by('-created')

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema(tags=["app_home"])
@commission_schema_view()
class CommissionViewSet(viewsets.ModelViewSet):
    serializer_class = CommissionSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, AdminPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)

        filters = Q()
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (
                Q(percentage__icontains=search_term) |
                Q(user__username__icontains=search_term)
            )
            filters &= search_filters
        queryset = Commission.objects.filter(filters).order_by('-created')

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema(tags=["app_home"])
@discount_schema_view()
class DiscountViewSet(viewsets.ModelViewSet):
    serializer_class = DiscountSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, AdminPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)

        filters = Q()
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (
                Q(name__icontains=search_term) |
                Q(user__username__icontains=search_term)|
                Q(rate__icontains=search_term) |
                Q(code__icontains=search_term) 
            )
            filters &= search_filters
        queryset = Discount.objects.filter(filters).order_by('-created')

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema(tags=["app_home"])
@lead_source_schema_view()
class LeadSourceViewSet(viewsets.ModelViewSet):
    serializer_class = LeadSourceSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, AdminPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)

        filters = Q()
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (
                Q(name__icontains=search_term) |
                Q(user__username__icontains=search_term)
            )
            filters &= search_filters
        queryset = LeadSource.objects.filter(filters).order_by('-created')

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema(tags=["app_home"])
@time_frame_schema_view()
class TimeFrameViewSet(viewsets.ModelViewSet):
    serializer_class = TimeFrameSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, AdminPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)

        filters = Q()
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (
                Q(user__username__icontains=search_term)
            )
            filters &= search_filters
        queryset = TimeFrame.objects.filter(filters).order_by('-created')

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema(tags=["app_home"])
@unit_schema_view()
class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, AdminPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)

        filters = Q()
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (
                Q(name__icontains=search_term) |
                Q(user__username__icontains=search_term)
            )
            filters &= search_filters
        queryset = Unit.objects.filter(filters).order_by('-created')

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
# @extend_schema(tags=["app_home"])
# @extend_schema(request=PasswordResetRequestSerializer)
# @permission_classes([])
# class PasswordResetRequestView(APIView):
#     def post(self, request, *args, **kwargs):
#         serializer = PasswordResetRequestSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": "Email đặt lại mật khẩu đã được gửi."}, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @extend_schema(tags=["app_home"])
# @extend_schema(request=PasswordResetSerializer)
# @permission_classes([])
# class PasswordResetView(APIView):
#     def post(self, request, *args, **kwargs):
#         serializer = PasswordResetSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": "Mật khẩu đã được đặt lại thành công."}, status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@extend_schema(tags=["app_home"])
@treatment_package_schema_view()
class TreatmentPackageViewSet(viewsets.ModelViewSet):
    queryset = TreatmentPackage.objects.all()
    serializer_class = TreatmentPackageSerializer
    def get_queryset(self):
        queryset = TreatmentPackage.objects.all()
        search = self.request.query_params.get("searchTerm")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset

@extend_schema(tags=["app_home"])
@test_service_schema_view()
class TestServiceViewSet(viewsets.ModelViewSet):
    queryset = TestService.objects.all()
    serializer_class = TestServiceSerializer

    def get_queryset(self):
        queryset = TestService.objects.all()
        search = self.request.query_params.get("searchTerm")
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(note__icontains=search)
            )
        return queryset