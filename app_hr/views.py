from .serializers import HrUserProfileSerializer
from app_home.pagination import CustomPagination
from django.db import transaction
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from app_home.views import CollaboratorReadOnlyPermission
from app_home.serializers import  UserSerializer
from drf_spectacular.utils import extend_schema
from django.db.models import Q, Value, Sum, Count, F
from django.db.models.functions import Concat
from rest_framework import viewsets, status
from .models import HrUserProfile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .docs import hr_management_schema
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from collections import defaultdict
from app_customer.models import Customer, Referral, LeadSourceActor

# Lấy model bảng trung gian (customer_id, introducer_id, commission_id)

User = get_user_model()
from app_treatment.models import ARItem, PaymentHistory
from rest_framework.views import APIView

@extend_schema(tags=["app_hr"])
@hr_management_schema()
class HrUserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = HrUserProfileSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, CollaboratorReadOnlyPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)
        format = self.request.query_params.get('format', None)
        #Phòng ban đang không có trong serializer nên hỏi FE có nên trả về phòng ban trong phòng nhân sự không ?
        department = self.request.query_params.get('department', None) 
        contract_type = self.request.query_params.get('contractType', None) 
        contract_status = self.request.query_params.get('contractStatus', None) 
        user_type = self.request.query_params.get('type', None)
        #Vì ko có full_name trong hr model nên phải trích từ user_profile: full_name để filtering
        queryset = HrUserProfile.objects.all()

        filters = Q()

        if start_date and end_date:
            filters &= Q(date__range=[start_date, end_date])
            
        if user_type:
            filters &= Q(type=user_type)

        # Lọc theo từ khóa tìm kiếm
        if search_term:
            search_filters = (
                Q(full_name__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(mobile__icontains=search_term) |
                Q(code__icontains=search_term)
            )
            filters &= search_filters

        if format:
            queryset = queryset.filter(format=format)

        #  Lọc theo phòng ban
        if department:
            filters &= Q(position__department__name__icontains=department)

        #  Lọc theo loại hợp đồng
        if contract_type:
            filters &= Q(contract_type=contract_type)

        #  Lọc theo trạng thái hợp đồng
        if contract_status:
            filters &= Q(contract_status=contract_status)
        return queryset.filter(filters).order_by('-created')

    def perform_create(self, serializer):
        serializer.save()
        
    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        from app_customer.models import Referral  # đổi import đúng app
        with transaction.atomic():
            # CÁCH A: chuyển về unknown
            # Referral.objects.filter(ref_hr=instance).update(ref_hr=None, unknown=True)
            # hoặc CÁCH B: xoá hẳn các referral liên quan (nếu business ok)
            Referral.objects.filter(ref_hr=instance).delete()

            instance.delete()

@extend_schema(tags=["app_hr"])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_collaborator_list(request):
    collaborators = User.objects.filter(user_profile__type='collaborator', is_active=True)
    serializer = UserSerializer(collaborators, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

class CollaboratorRevenueListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get("startDate")
        end_date = request.query_params.get("endDate")
        search = (request.query_params.get("searchTerm") or "").strip()

        # 0) LẤY TẤT CẢ CTV từ HrUserProfile - nguồn duy nhất
        ctv_qs = HrUserProfile.objects.filter(type='collaborator')
        
        if search:
            ctv_qs = ctv_qs.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(mobile__icontains=search) |
                Q(code__icontains=search)
            )
        
        # Lấy ID của HrUserProfile
        ctv_ids = list(ctv_qs.values_list("id", flat=True))

        # 1) Lấy danh sách khách hàng được CTV giới thiệu thông qua Referral
        # ref_hr_id giờ trỏ đến HrUserProfile.id
        ci_qs = Referral.objects.filter(ref_hr_id__in=ctv_ids).values("ref_hr_id", "customer_id")
        customers_by_ctv = defaultdict(set)
        for rel in ci_qs:
            customers_by_ctv[rel["ref_hr_id"]].add(rel["customer_id"])

        # 2) ARItem của toàn bộ khách hàng đã được CTV giới thiệu
        all_customer_ids = {cid for s in customers_by_ctv.values() for cid in s}
        ar_qs = ARItem.objects.filter(customer_id__in=all_customer_ids) if all_customer_ids else ARItem.objects.none()

        # 3) Doanh thu theo khách hàng = SUM PaymentHistory.paid_amount
        revenue_by_customer = {}
        if ar_qs.exists():
            pmt_filters = Q(ar_item__customer_id__in=all_customer_ids)
            if start_date and end_date:
                pmt_filters &= Q(created__date__range=[start_date, end_date])
            elif start_date:
                pmt_filters &= Q(created__date__gte=start_date)
            elif end_date:
                pmt_filters &= Q(created__date__lte=end_date)

            pmt_qs = (
                PaymentHistory.objects
                .filter(pmt_filters)
                .values("ar_item__customer_id")
                .annotate(revenue=Sum("paid_amount"))
            )
            revenue_by_customer = {
                r["ar_item__customer_id"]: r["revenue"] or 0
                for r in pmt_qs
            }

        # 4) Đếm số hóa đơn (ARItem) theo khách hàng
        ar_count_by_customer = {}
        if ar_qs.exists():
            invoice_count = (
                ar_qs.values("customer_id")
                     .annotate(cnt=Count("id", distinct=True))
            )
            ar_count_by_customer = {r["customer_id"]: r["cnt"] for r in invoice_count}

        # 5) Khởi tạo dữ liệu cho TẤT CẢ CTV
        data = {}
        for ctv_id in ctv_ids:
            data[ctv_id] = {
                "total_revenue": 0,
                "invoices": 0,
                "referrals": 0
            }

        # 6) Tổng hợp thông tin cho từng CTV
        for ctv_id, cust_set in customers_by_ctv.items():
            if ctv_id not in data:
                continue
            
            total_rev = sum(revenue_by_customer.get(c, 0) or 0 for c in cust_set)
            total_inv = sum(ar_count_by_customer.get(c, 0) for c in cust_set)
            
            data[ctv_id]["total_revenue"] = total_rev
            data[ctv_id]["invoices"] = total_inv
            data[ctv_id]["referrals"] = len(cust_set)

        # 7) Tạo kết quả - TRẢ VỀ TẤT CẢ CTV
        result = []
        for ctv in ctv_qs.order_by("-created"):
            row = data.get(ctv.id, {"invoices": 0, "total_revenue": 0, "referrals": 0})
            result.append({
                "id": ctv.id,
                "code": ctv.code,
                "full_name": ctv.full_name,
                "email": ctv.email,
                "mobile": ctv.mobile,
                "invoices": row["invoices"],
                "total_revenue": row["total_revenue"],
                "referrals": row["referrals"],
            })
        
        return Response(result)
    
class CollaboratorCustomerDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        start_date = request.query_params.get("startDate")
        end_date = request.query_params.get("endDate")
        search = (request.query_params.get("searchTerm") or "").strip()

        # KH do CTV này giới thiệu thông qua Referral
        cust_ids = (Referral.objects
                    .filter(ref_hr_id=user_id)
                    .values_list("customer_id", flat=True))

        cust_qs = Customer.objects.filter(id__in=cust_ids)
        if search:
            cust_qs = cust_qs.filter(Q(name__icontains=search) | Q(mobile__icontains=search))

        # ARItem của các khách hàng này
        ar_qs = ARItem.objects.filter(customer_id__in=cust_qs.values("id"))

        # Doanh thu theo ARItem = SUM PaymentHistory.paid_amount (lọc theo kỳ nếu có)
        pmt_filters = Q(ar_item_id__in=ar_qs.values("id"))
        if start_date and end_date:
            pmt_filters &= Q(created__date__range=[start_date, end_date])
        elif start_date:
            pmt_filters &= Q(created__date__gte=start_date)
        elif end_date:
            pmt_filters &= Q(created__date__lte=end_date)

        ar_revenue = (
            PaymentHistory.objects.filter(pmt_filters)
            .values("ar_item_id")
            .annotate(revenue=Sum("paid_amount"))
        )
        ar_rev_map = {r["ar_item_id"]: r["revenue"] or 0 for r in ar_revenue}

        # Build details per customer
        result = []
        for c in cust_qs:
            cust_ar = list(
                ar_qs.filter(customer_id=c.id)
                     .values("id", "created", "content_type_id", "description")
            )
            details = []
            total_rev = 0

            for ar in cust_ar:
                ct = ContentType.objects.get_for_id(ar["content_type_id"])
                invoice_type = {
                    "treatmentrequest": "Hóa đơn phác đồ",
                    "diagnosis_medicine": "Thành phần thuốc",
                    "doctorprocess": "Hóa đơn thuốc",
                }.get(ct.model.lower(), ct.model.title())

                rev = ar_rev_map.get(ar["id"], 0) or 0
                total_rev += rev
                details.append({
                    "created": ar["created"],
                    "invoice_type": invoice_type,
                    "revenue": rev,
                })

            result.append({
                "customer_id": c.id,
                "name": c.name,
                "mobile": c.mobile,
                "total_invoices": len(cust_ar),
                "total_revenue": total_rev,
                "details": details,
            })
        return Response(result)
    
class ActorLeadSourcePerformanceAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get("startDate")
        end_date = request.query_params.get("endDate")
        search = (request.query_params.get("searchTerm") or "").strip()

        # 1) Lọc tất cả các Actor từ LeadSourceActor
        actors_qs = LeadSourceActor.objects.all()  # Lấy tất cả actor từ LeadSourceActor

        if search:
            actors_qs = actors_qs.filter(
                Q(name__icontains=search)
            )

        actor_ids = list(actors_qs.values_list("id", flat=True))  # Sử dụng ID của LeadSourceActor

        # 2) Lấy danh sách khách hàng (customer) mà các actor đã giới thiệu thông qua Referral
        ci_qs = (
            Referral.objects.filter(ref_actor_id__in=actor_ids)
            .values("ref_actor_id", "customer_id")
        )
        customers_by_actor = defaultdict(set)
        for rel in ci_qs:
            customers_by_actor[rel["ref_actor_id"]].add(rel["customer_id"])

        # 3) Lấy ARItem từ tất cả các khách hàng đã giới thiệu
        all_customer_ids = {cid for s in customers_by_actor.values() for cid in s}
        ar_qs = ARItem.objects.filter(customer_id__in=all_customer_ids) if all_customer_ids else ARItem.objects.none()

        # 4) Doanh thu: sum PaymentHistory
        revenue_by_customer = {}
        if ar_qs.exists():
            pmt_filters = Q(ar_item__customer_id__in=all_customer_ids)
            if start_date and end_date:
                pmt_filters &= Q(created__date__range=[start_date, end_date])
            elif start_date:
                pmt_filters &= Q(created__date__gte=start_date)
            elif end_date:
                pmt_filters &= Q(created__date__lte=end_date)

            pmt_qs = (
                PaymentHistory.objects
                .filter(pmt_filters)
                .values("ar_item__customer_id")
                .annotate(revenue=Sum("paid_amount"))
            )
            revenue_by_customer = {
                r["ar_item__customer_id"]: r["revenue"] or 0
                for r in pmt_qs
            }

        # 5) Đếm số lượng khách hàng (customer) được giới thiệu bởi từng actor
        data = {
            actor_id: {
                "actor_id": actor_id,
                "total_revenue": 0,
                "total_customers": 0,
                "lead_source": None,  # Thêm thông tin LeadSource vào
            }
            for actor_id in actor_ids
        }

        # 6) Tính doanh thu và số lượng khách cho từng actor
        for actor_id, customer_set in customers_by_actor.items():
            total_revenue = sum(revenue_by_customer.get(c, 0) for c in customer_set)
            total_customers = len(customer_set)
            # Lấy thông tin LeadSource từ Actor
            actor = LeadSourceActor.objects.get(id=actor_id)
            lead_source = actor.source.name if actor.source else "N/A"  # Thêm LeadSource

            data[actor_id]["total_revenue"] = total_revenue
            data[actor_id]["total_customers"] = total_customers
            data[actor_id]["lead_source"] = lead_source

        # 7) Join thông tin Actor (LeadSourceActor)
        result = []
        for actor in actors_qs.order_by("id"):
            actor_data = data.get(actor.id, {"total_revenue": 0, "total_customers": 0, "lead_source": "N/A"})
            result.append({
                "actor_id": actor.id,
                "full_name": actor.name,  # Sử dụng tên actor từ trường 'name'
                "total_revenue": actor_data["total_revenue"],
                "total_customers": actor_data["total_customers"],
                "lead_source": actor_data["lead_source"],
            })
        return Response(result)
    
class ActorCustomerDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        start_date = request.query_params.get("startDate")
        end_date = request.query_params.get("endDate")
        search = (request.query_params.get("searchTerm") or "").strip()

        # KH do Actor này giới thiệu thông qua Referral
        cust_ids = (Referral.objects
                    .filter(ref_actor_id=user_id)
                    .values_list("customer_id", flat=True))

        cust_qs = Customer.objects.filter(id__in=cust_ids)
        if search:
            cust_qs = cust_qs.filter(Q(name__icontains=search) | Q(mobile__icontains=search))

        # ARItem của các khách hàng này
        ar_qs = ARItem.objects.filter(customer_id__in=cust_qs.values("id"))

        # Doanh thu theo ARItem = SUM PaymentHistory.paid_amount (lọc theo kỳ nếu có)
        pmt_filters = Q(ar_item_id__in=ar_qs.values("id"))
        if start_date and end_date:
            pmt_filters &= Q(created__date__range=[start_date, end_date])
        elif start_date:
            pmt_filters &= Q(created__date__gte=start_date)
        elif end_date:
            pmt_filters &= Q(created__date__lte=end_date)

        ar_revenue = (
            PaymentHistory.objects.filter(pmt_filters)
            .values("ar_item_id")
            .annotate(revenue=Sum("paid_amount"))
        )
        ar_rev_map = {r["ar_item_id"]: r["revenue"] or 0 for r in ar_revenue}

        # Build details per customer
        result = []
        for c in cust_qs:
            cust_ar = list(
                ar_qs.filter(customer_id=c.id)
                     .values("id", "created", "content_type_id", "description")
            )
            details = []
            total_rev = 0

            for ar in cust_ar:
                ct = ContentType.objects.get_for_id(ar["content_type_id"])
                invoice_type = {
                    "treatmentrequest": "Hóa đơn phác đồ",
                    "diagnosis_medicine": "Thành phần thuốc",
                    "doctorprocess": "Hóa đơn thuốc",
                }.get(ct.model.lower(), ct.model.title())

                rev = ar_rev_map.get(ar["id"], 0) or 0
                total_rev += rev
                details.append({
                    "created": ar["created"],
                    "invoice_type": invoice_type,
                    "revenue": rev,
                })

            result.append({
                "customer_id": c.id,
                "name": c.name,
                "mobile": c.mobile,
                "total_invoices": len(cust_ar),
                "total_revenue": total_rev,
                "details": details,
            })
        return Response(result)