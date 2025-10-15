import code
from django.shortcuts import get_object_or_404
from app_home.models import LeadSource
from app_hr.models import HrUserProfile
from django.db.models import Q, Prefetch
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework import viewsets, status, permissions
from app_customer.models import LeadSourceActor
from app_treatment.models import (
    TreatmentRequest, TreatmentSession, SessionTechicalSetting, TreatmentPackage
)
from app_treatment.models import ARItem, PaymentHistory
from django.db.models import OuterRef, Subquery
from django.utils.dateparse import parse_date
from rest_framework.exceptions import APIException

from drf_spectacular.utils import extend_schema
from app_home.pagination import CustomPagination
from django.db import transaction, IntegrityError
from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from .docs import customer_level_schema, customer_care_schema, feedback_schema, lead_status_schema, treatment_state_schema

from .models import CustomerRequest, LeadStatus, Referral, TreatmentState, Customer, CustomerCare, FeedBack, CustomerProblem, Referral, LeadSourceActor
from .serializers import CustomerRequestSerializer, LeadStatusSerializer, TreatmentStateSerializer, CustomerSerializer, CustomerCareSerializer, FeedBackSerializer, CustomerProblemSerializer, LeadSourceActorSerializer
from .models import LeadStatus, TreatmentState, Customer, CustomerCare, FeedBack, CustomerLevel, CustomerProblem
from .serializers import LeadStatusSerializer, TreatmentStateSerializer, CustomerSerializer, CustomerCareSerializer,FeedBackSerializer, CustomerLevelSerializer
from django.db.models import F

@lead_status_schema()
@extend_schema(tags=["app_customer"])
class LeadStatusViewSet(viewsets.ModelViewSet):
    serializer_class = LeadStatusSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

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
                Q(note__icontains=search_term)
            )
            filters &= search_filters
        queryset = LeadStatus.objects.filter(filters).order_by('-created')

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@treatment_state_schema()
@extend_schema(tags=["app_customer"])
class TreatmentStateViewSet(viewsets.ModelViewSet):
    serializer_class = TreatmentStateSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

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
                Q(note__icontains=search_term)
            )
            filters &= search_filters
        queryset = TreatmentState.objects.filter(filters).order_by('-created')

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@customer_level_schema()
@extend_schema(tags=["app_customer"])
class CustomerLevelViewSet(viewsets.ModelViewSet):
    queryset = CustomerLevel.objects.prefetch_related(
        Prefetch('lead_status'),
        Prefetch('treatment_state')
    )
    serializer_class = CustomerLevelSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        search_term = self.request.query_params.get('searchTerm', None)

        filters = Q()
        if search_term:
            search_filters = (
                Q(name__icontains=search_term) |
                Q(user__username__icontains=search_term)
            )
            filters &= search_filters
        queryset = CustomerLevel.objects.filter(filters).order_by('-created')

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
@extend_schema(tags=["app_customer"])
class CustomerRequestViewSet(viewsets.ModelViewSet):
    queryset = CustomerRequest.objects.all().order_by('-created')
    serializer_class = CustomerRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CustomerProblemViewSet(viewsets.ModelViewSet):
    queryset = CustomerProblem.objects.select_related('customer', 'user').all().order_by('-id')
    serializer_class = CustomerProblemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        customer_id = self.request.query_params.get('customer')

        if customer_id:
            qs = qs.filter(customer_id=customer_id)

        return qs

    def perform_create(self, serializer):
        """
        - Gán user = request.user
        - Lấy customer từ request.data['customer'] (bắt buộc) rồi truyền qua serializer.save(...)
        """
        customer_id = self.request.data.get('customer')
        if not customer_id:
            # Trả lỗi rõ ràng nếu thiếu customer
            raise ValueError("Missing 'customer' in request data.")
        customer = get_object_or_404(Customer, pk=customer_id)
        serializer.save(user=self.request.user, customer=customer)

    def create(self, request, *args, **kwargs):
        """
        Ghi đè để trả thông báo lỗi đẹp hơn nếu thiếu/invalid 'customer'
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
        """
        Không cho đổi customer qua request; nếu cần đổi phải xoá và tạo mới (theo logic serializer hiện tại).
        Ở đây chỉ đảm bảo user là người cập nhật hiện tại.
        """
        serializer.save(user=self.request.user)

    # destroy/retrieve/list/update/partial_update dùng mặc định của ModelViewSet
# @customer_schema()
@extend_schema(tags=["app_customer"])
class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        params = self.request.query_params
        start_date = params.get("startDate")
        end_date = params.get("endDate")
        search_term = params.get("searchTerm")
        main_status = params.get("main-status")
        lead_status = params.get("lead-status")
        treatment_status = params.get("treatment-status")

        filters = Q(is_active=True)
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            filters &= (
                Q(name__icontains=search_term) |
                Q(code__icontains=search_term) |
                Q(mobile__icontains=search_term) |
                Q(carreer__icontains=search_term)
            )
        if main_status:
            filters &= Q(main_status=str(main_status))
        if lead_status:
            filters &= Q(lead_status_id=lead_status)
        if treatment_status:
            filters &= Q(treatment_status_id=treatment_status)

        return (
            Customer.objects.filter(filters)
            .select_related(
                "user", "lead_status", "treatment_status", "time_frame",
                "primary_referral",
                "primary_referral__ref_customer",
                "primary_referral__ref_hr",
                "primary_referral__ref_actor",
                "primary_referral__ref_actor__source",
            )
            .prefetch_related("service")
            .order_by("-created")
        )
        
    def perform_destroy(self, instance):
        try:
            with transaction.atomic():
                # Xóa PaymentHistory liên quan
                PaymentHistory.objects.filter(ar_item__customer=instance).delete()
                # Xóa ARItem liên quan
                ARItem.objects.filter(customer=instance).delete()
                # Xóa Referral liên quan
                Referral.objects.filter(customer=instance).delete()
                # Xóa Customer
                instance.delete()
        except Exception as e:
            raise APIException(f"Không thể xóa khách hàng: {str(e)}")

    # ---------- Referral helper ----------
    def _apply_referral(self, customer):
        """
        Cập nhật nguồn 1–1 từ payload write-only của CustomerSerializer.
        Hợp lệ: ref_type in {customer|hr|actor}. Không hợp lệ hoặc trống → xoá Referral.
        """
        data = self.request.data
        rt = (data.get("referral_type") or "").strip().lower()

        # Xoá nếu trống hoặc không hợp lệ
        if rt not in {"customer", "hr", "actor"}:
            Referral.objects.filter(customer=customer).delete()
            return

        # KH giới thiệu KH
        if rt == "customer":
            ref_customer = None
            rid = data.get("referral_customer_id")
            rcode = (data.get("referral_customer_code") or "").strip()
            if rid:
                ref_customer = Customer.objects.filter(pk=int(rid)).first()
            elif rcode:
                ref_customer = Customer.objects.filter(code__iexact=rcode).first()

            if not ref_customer or ref_customer.id == customer.id:
                Referral.objects.filter(customer=customer).delete()
                return

            Referral.objects.update_or_create(
                customer=customer,
                defaults={
                    "ref_type": "customer",
                    "ref_customer": ref_customer,
                    "ref_hr": None,
                    "ref_actor": None,
                    "lookup_code": rcode or str(rid or ""),
                }
            )
            return

        # CTV/HR giới thiệu
        if rt == "hr":
            hr = None
            hrid = data.get("referral_hr_id")
            hrcode = (data.get("referral_hr_code") or "").strip()
            if hrid:
                hr = HrUserProfile.objects.filter(pk=int(hrid)).first()
            elif hrcode:
                hr = HrUserProfile.objects.filter(code__iexact=hrcode).first()

            if not hr:
                Referral.objects.filter(customer=customer).delete()
                return

            Referral.objects.update_or_create(
                customer=customer,
                defaults={
                    "ref_type": "hr",
                    "ref_customer": None,
                    "ref_hr": hr,
                    "ref_actor": None,
                    "lookup_code": hrcode or str(hrid or ""),
                }
            )
            return

        # Actor thuộc LeadSource
        if rt == "actor":
            actor = None
            actor_id = data.get("referral_actor")
            if actor_id:
                actor = LeadSourceActor.objects.filter(pk=int(actor_id)).select_related("source").first()
            else:
                src_id = data.get("referral_source")
                if not src_id:
                    Referral.objects.filter(customer=customer).delete()
                    return
                source = LeadSource.objects.filter(pk=int(src_id)).first()
                if not source:
                    Referral.objects.filter(customer=customer).delete()
                    return

                actor_name = (data.get("referral_actor_name") or "").strip()
                actor_code = (data.get("referral_actor_code") or "").strip()
                actor_ext  = (data.get("referral_actor_external_id") or "").strip()

                # Ưu tiên code → external_id → name
                if actor_code:
                    actor, _ = LeadSourceActor.objects.get_or_create(
                        source=source, name=(actor_name or actor_code),
                        defaults={"code": actor_code, "external_id": actor_ext or None}
                    )
                elif actor_ext:
                    actor, _ = LeadSourceActor.objects.get_or_create(
                        source=source, name=(actor_name or actor_ext),
                        defaults={"external_id": actor_ext}
                    )
                elif actor_name:
                    actor, _ = LeadSourceActor.objects.get_or_create(source=source, name=actor_name)
                else:
                    Referral.objects.filter(customer=customer).delete()
                    return

            Referral.objects.update_or_create(
                customer=customer,
                defaults={
                    "ref_type": "actor",
                    "ref_customer": None,
                    "ref_hr": None,
                    "ref_actor": actor,
                    "lookup_code": data.get("referral_actor_code")
                                   or data.get("referral_actor_external_id")
                                   or data.get("referral_actor_name")
                                   or "",
                }
            )
            return
        
    def perform_create(self, serializer):
        validated = dict(serializer.validated_data)
        problems_data = validated.pop("customer_problems", [])
        service_data = validated.pop("service", [])

        # Bỏ logic kiểm tra code cũ vì giờ tự động sinh
        
        try:
            with transaction.atomic():
                # Code sẽ tự động sinh trong model.save()
                customer = serializer.save(
                    user=self.request.user,
                    main_status=serializer.validated_data.get("main_status", "1")
                )

                if service_data:
                    customer.service.set(service_data)

                # Xử lý problems inline
                for p in problems_data:
                    CustomerProblem.objects.create(
                        customer=customer, user=self.request.user,
                        problem=p.get("problem"), encounter_pain=p.get("encounter_pain"),
                        desire=p.get("desire"),
                    )

                # Xử lý nguồn 1-1
                self._apply_referral(customer)

        except IntegrityError as e:
            # Nếu có lỗi tự động sinh code, thử lại
            if "code" in str(e).lower():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"code": "Lỗi sinh mã khách hàng tự động. Vui lòng thử lại."})
            raise
    
    @action(detail=False, methods=["get"], url_path="treatment-report")
    def treatment_report(self, request):
        params = request.query_params
        search      = params.get("search") or params.get("q")
        date_str    = params.get("date")
        start_date  = params.get("startDate")
        end_date    = params.get("endDate")
        service_type= params.get("serviceType")  # ví dụ: TLCB | TLDS

        # 1) Tập KH có phác đồ
        qs_cus = Customer.objects.filter(treatment_requests__isnull=False).distinct()

        # search theo mã/tên/SĐT
        if search:
            qs_cus = qs_cus.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(mobile__icontains=search)
            )

        # 2) Subquery lấy ID phác đồ gần nhất theo từng KH (lọc theo ngày / loại DV nếu có)
        tr_sq = TreatmentRequest.objects.filter(customer_id=OuterRef("pk"))
        if date_str:
            d = parse_date(date_str)
            if d:
                tr_sq = tr_sq.filter(created_at__date=d)
        if start_date:
            tr_sq = tr_sq.filter(created_at__date__gte=start_date)
        if end_date:
            tr_sq = tr_sq.filter(created_at__date__lte=end_date)
        if service_type:
            tr_sq = tr_sq.filter(service__type=service_type)

        tr_sq = tr_sq.order_by("-created_at", "-id").values("id")[:1]
        qs_cus = qs_cus.annotate(latest_tr_id=Subquery(tr_sq)).filter(latest_tr_id__isnull=False)

        # 3) Lấy các phác đồ đã annotate ở trên
        tr_ids = list(qs_cus.values_list("latest_tr_id", flat=True))
        trs = (TreatmentRequest.objects
               .filter(id__in=tr_ids)
               .select_related("customer", "service", "treatment_package"))

        # 4) Build kết quả
        rows = []
        for tr in trs:
            customer = tr.customer
            pkg = tr.treatment_package  # TreatmentPackage; value = tổng buổi
            total_sessions = int(getattr(pkg, "value", 0) or 0)

            # Đếm số BUỔI có ít nhất 1 kỹ thuật has_come=True
            done_sessions = (
                SessionTechicalSetting.objects
                .filter(session__treatment_request=tr, has_come=True)
                .values("session_id").distinct().count()
            )

            remaining = max(total_sessions - done_sessions, 0)
            status_label = "Đã hoàn thành" if tr.compute_is_done() else "Chưa hoàn thành"

            rows.append({
                "customer_id": customer.id,
                "customer_code": customer.code,
                "customer_name": customer.name,
                "mobile": customer.mobile,
                "treatment_type": getattr(tr.service, "type", None),
                "total_sessions": total_sessions,
                "done_sessions": done_sessions,
                "remaining_sessions": remaining,
                "status": status_label,
            })

        # sort nhẹ cho đẹp mắt: theo tên KH
        rows.sort(key=lambda x: (x["customer_name"] or "").lower())

        return Response(rows, status=status.HTTP_200_OK)

    # ---------- CREATE ----------
    def perform_create(self, serializer):
        validated = dict(serializer.validated_data)
        problems_data = validated.pop("customer_problems", [])
        service_data = validated.pop("service", [])

        # chuẩn hoá code sớm (serializer.validate_code cũng đã làm)
        code = (serializer.validated_data.get("code") or "").strip().upper()
        if code and Customer.objects.filter(code=code).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"code": "Mã khách hàng đã tồn tại."})

        try:
            with transaction.atomic():
                customer = serializer.save(user=self.request.user, code=code,
                                           main_status=serializer.validated_data.get("main_status", "1"))

                if service_data:
                    customer.service.set(service_data)

                # problems inline
                for p in problems_data:
                    CustomerProblem.objects.create(
                        customer=customer, user=self.request.user,
                        problem=p.get("problem"), encounter_pain=p.get("encounter_pain"),
                        desire=p.get("desire"),
                    )

                # nguồn 1–1
                self._apply_referral(customer)

        except IntegrityError as e:
            if "code" in str(e).lower():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({"code": "Mã khách hàng đã tồn tại."})
            raise

    # ---------- UPDATE ----------
    def perform_update(self, serializer):
        validated = serializer.validated_data
        problems_data = validated.pop("customer_problems", [])
        service_data = validated.pop("service", [])

        customer = serializer.instance

        with transaction.atomic():
            # cập nhật phần còn lại
            customer = serializer.save()

            if service_data:
                customer.service.set(service_data)

            # reset + set lại problems
            customer.customer_problems.all().delete()
            for p in problems_data:
                CustomerProblem.objects.create(
                    customer=customer, user=self.request.user,
                    problem=p.get("problem"), encounter_pain=p.get("encounter_pain"),
                    desire=p.get("desire"),
                )

            # nguồn 1–1
            self._apply_referral(customer)

    # ---------- Reports ----------
    @action(detail=False, methods=["get"], url_path="referral-leaders")
    def referral_leaders(self, request):
        """
        KH có số lượt giới thiệu (ref_type=customer) >= min (mặc định 5)
        """
        try:
            min_count = int(request.query_params.get("min", 5))
        except ValueError:
            min_count = 5

        qs = (
            Customer.objects
            .annotate(referral_count=Count("referred_others"))  # related_name từ Referral.ref_customer
            .filter(referral_count__gte=min_count)
            .order_by("-referral_count", "-id")
            .values("id", "name", "mobile", "email", "gender", "address", "code", "referral_count")
        )
        return Response(list(qs), status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="referred-customers")
    def referred_customers(self, request, pk=None):
        """
        Danh sách KH được <pk> giới thiệu (ref_type=customer).
        """
        qs = (
            Customer.objects
            .filter(primary_referral__ref_type="customer",
                    primary_referral__ref_customer_id=pk)
            .order_by("-created")
            .values("id", "name", "gender", "mobile", "created", "code", "email")
        )
        return Response(list(qs), status=status.HTTP_200_OK)

@extend_schema(tags=["app_customer"])
@customer_care_schema()
class CustomerCareViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerCareSerializer
    permission_classes = [IsAuthenticated]
    queryset = CustomerCare.objects.all()

    def get_queryset(self):
        params = self.request.query_params

        start_date   = params.get("startDate")
        end_date     = params.get("endDate")
        search_term  = params.get("searchTerm")
        call_type    = params.get("type")           # hỗ trợ nhiều giá trị: type=a,b,c
        customer_id  = params.get("customerId") or params.get("customer")
        customer_name= params.get("customerName")
        solidarity   = params.get("solidarity")
        user_id      = params.get("userId")         # nếu muốn lọc theo người phụ trách

        qs = (
            CustomerCare.objects
            .select_related("customer", "user")
            .order_by("-created")
        )

        # Lọc theo ngày
        if start_date and end_date:
            qs = qs.filter(date__range=[start_date, end_date])
        elif start_date:
            qs = qs.filter(date__gte=start_date)
        elif end_date:
            qs = qs.filter(date__lte=end_date)

        # Lọc theo khách hàng (id hoặc tên)
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if customer_name:
            qs = qs.filter(customer__name__icontains=customer_name)

        # Lọc theo loại call (hỗ trợ nhiều loại, phân tách dấu phẩy)
        if call_type:
            types = [t.strip() for t in call_type.split(",") if t.strip()]
            qs = qs.filter(type__in=types)

        # Lọc theo mức độ gắn kết (nếu dùng)
        if solidarity:
            qs = qs.filter(solidarity=solidarity)

        # Lọc theo user chăm sóc (nếu cần)
        if user_id:
            qs = qs.filter(user_id=user_id)

        # Tìm kiếm chung: tên/điện thoại/email khách + ghi chú
        if search_term:
            qs = qs.filter(
                Q(customer__name__icontains=search_term) |
                Q(customer__mobile__icontains=search_term) |
                Q(customer__email__icontains=search_term) |
                Q(note__icontains=search_term)
            )
        qs = qs.order_by(
            F("date").desc(nulls_last=True),  # nếu date = NULL thì đẩy xuống sau
            "-created",
            "-id",
        )
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
@extend_schema(tags=["app_customer"])
@feedback_schema()
class FeedBackViewSet(viewsets.ModelViewSet):
    serializer_class = FeedBackSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)
        format = self.request.query_params.get('format', None)

        filters = Q()

        if start_date and end_date:
            filters &= Q(date__range=[start_date, end_date])

        # Lọc theo từ khóa tìm kiếm
        if search_term:
            search_filters = (
                Q(name__icontains=search_term) |
                Q(source__name__icontains=search_term) |
                Q(source_link__icontains=search_term) |
                Q(mobile__icontains=search_term) |
                Q(email__icontains=search_term)
            )
            filters &= search_filters

        if format:
            filters &= Q(format=format)

        return FeedBack.objects.filter(filters).order_by('-created')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
class LeadSourceActorViewSet(viewsets.ModelViewSet):
    queryset = LeadSourceActor.objects.select_related('source', 'hr_profile').all().order_by('-id')
    serializer_class = LeadSourceActorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        source = self.request.query_params.get('source')
        q = self.request.query_params.get('q')
        if source:
            qs = qs.filter(source_id=source)
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q) | Q(external_id__icontains=q))
        return qs