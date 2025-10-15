from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Value, OuterRef, Subquery, F
from django.db import transaction
from rest_framework.views import APIView
from rest_framework import generics
from django.db.models import Prefetch
from datetime import date
from django.db.models.functions import Coalesce
from collections import defaultdict
from typing import Optional
import time

from app_home.pagination import CustomPagination
from app_home.views import CollaboratorReadOnlyPermission
from .services.payroll import get_performance_payroll

from .serializers import (
    ARItemSerializer,
)

from app_treatment.models import Bill, Booking, DoctorProcess, DoctorHealthCheck, ServiceAssign,ReExamination
from app_treatment.serializers import BookingSerializer, DoctorProcessSerializer, DoctorHealthCheckSerializer,ReExaminationSerializer, BillNeedSerializer


from drf_spectacular.utils import extend_schema

from app_product.serializers import ProductSerializer, ServiceSerializer
from app_product.models import TechicalSetting

from .docs import *
@extend_schema(tags=["app_treatment"])
@booking_schema()
class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, CollaboratorReadOnlyPermission]

    def get_queryset(self):
        """
        ✅ SIÊU TỐI ƯU:
        - Prefetch đầy đủ: Booking → Customer → TreatmentRequest → TreatmentSession → SessionTechicalSetting
        - Dùng Subquery để chỉ lấy TR mới nhất
        - Loại bỏ hoàn toàn N+1 query
        """
        # ✅ Parse query params
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', '').strip()
        is_treatment = self.request.query_params.get('is_treatment', None)
        has_come_param = self.request.query_params.get('has_come', None)
        customer_id = self.request.query_params.get('customer', None)

        # ✅ Parse types
        raw_types = []
        raw_types.extend(self.request.query_params.getlist('type'))
        types_csv = self.request.query_params.get('types', '').strip()
        if types_csv:
            raw_types.extend(types_csv.split(','))

        valid_types = {choice for choice, _ in Booking.BOOKING_TYPE}
        selected_types = list(set([
            t.strip().lower() 
            for t in raw_types 
            if t.strip().lower() in valid_types
        ]))

        # ✅ Build filters
        filters = Q()

        if customer_id:
            filters &= Q(customer_id=customer_id)
            
        if start_date and end_date:
            filters &= Q(receiving_day__range=[start_date, end_date])
        elif start_date:
            filters &= Q(receiving_day__gte=start_date)
        elif end_date:
            filters &= Q(receiving_day__lte=end_date)
            
        if search_term:
            filters &= (
                Q(customer__name__icontains=search_term) |
                Q(customer__code__icontains=search_term) |
                Q(user__username__icontains=search_term) |
                Q(note__icontains=search_term)
            )
            
        if is_treatment is not None:
            val = str(is_treatment).strip().lower()
            if val in ['true', '1', 'yes']:
                filters &= Q(is_treatment=True)
            elif val in ['false', '0', 'no']:
                filters &= Q(is_treatment=False)
                
        if has_come_param is not None:
            hv = str(has_come_param).strip().lower()
            if hv in ('true', '1', 'yes'):
                filters &= Q(has_come=True)
            elif hv in ('false', '0', 'no'):
                filters &= Q(has_come=False)
                
        if selected_types:
            filters &= Q(type__in=selected_types)

        # ✅ CRITICAL: Subquery để lấy ID của TR mới nhất
        latest_tr_subquery = (
            TreatmentRequest.objects
            .filter(customer_id=OuterRef('customer_id'))
            .order_by('-created_at', '-id')
            .values('id')[:1]
        )

        # ✅ SUPER OPTIMIZED QUERYSET với prefetch đầy đủ
        queryset = (
            Booking.objects
            .filter(filters)
            .select_related(
                'customer',                  # Customer info
                'customer__lead_status',     # Lead status
                'user'                       # User tạo booking
            )
            .prefetch_related(
                Prefetch(
                    'customer__treatment_requests',  # ✅ related_name từ model
                    queryset=(
                        TreatmentRequest.objects
                        .filter(id=Subquery(latest_tr_subquery))
                        .select_related(
                            'user',              # User tạo TR
                            'doctor_profile',    # Bác sĩ (HrUserProfile)
                            'service'            # Service cho plan_type
                        )
                        .prefetch_related(
                            Prefetch(
                                'treatment_sessions',  # ✅ related_name
                                queryset=(
                                    TreatmentSession.objects
                                    .prefetch_related(
                                        # ✅ Prefetch tất cả SessionTechicalSetting
                                        'sessiontechicalsetting_set'
                                    )
                                    .order_by('id')
                                )
                            )
                        )
                    ),
                    to_attr='latest_tr_list'  # ✅ Custom attr cho serializer
                )
            )
            .order_by('-created')
        )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        t0 = time.perf_counter()
        qs = self.filter_queryset(self.get_queryset())
        t1 = time.perf_counter()
        page = self.paginate_queryset(qs)
        t2 = time.perf_counter()

        if page is not None:
            ser_build_0 = time.perf_counter()
            serializer = self.get_serializer(page, many=True)
            ser_build_1 = time.perf_counter()

            ser_eval_0 = time.perf_counter()
            data = serializer.data        # 🔥 CHỖ NÀY MỚI THỰC SỰ “serialize”
            ser_eval_1 = time.perf_counter()

            resp_0 = time.perf_counter()
            resp = self.get_paginated_response(data)
            resp_1 = time.perf_counter()
        else:
            ser_build_0 = time.perf_counter()
            serializer = self.get_serializer(qs, many=True)
            ser_build_1 = time.perf_counter()

            ser_eval_0 = time.perf_counter()
            data = serializer.data
            ser_eval_1 = time.perf_counter()

            resp_0 = time.perf_counter()
            resp = Response(data)
            resp_1 = time.perf_counter()

        print(
        f"[TIMING] qs={(t1-t0):.3f}s | paginate={(t2-t1):.3f}s | "
        f"ser_build={(ser_build_1-ser_build_0):.3f}s | "
        f"ser_eval={(ser_eval_1-ser_eval_0):.3f}s | "
        f"wrap={(resp_1-resp_0):.3f}s | total={(resp_1-t0):.3f}s"
        )
        return resp

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        print("PATCH request received:", request.data)  # Debug print
        instance = self.get_object()  # Get the existing booking
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True  # Allow partial updates
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path="update-has-come")
    def update_has_come(self, request, pk=None):
        booking = self.get_object()
        if booking.has_come:
            return Response({"error": "Trạng thái has_come đã được cập nhật trước đó."}, status=status.HTTP_400_BAD_REQUEST)
        booking.has_come = True
        booking.save(update_fields=["has_come"])
        return Response({"message": "Cập nhật has_come thành công."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path="update-status")
    def update_status(self, request, pk=None):
        booking = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response({"error": "Trường 'status' là bắt buộc."}, status=status.HTTP_400_BAD_REQUEST)

        valid_statuses = [choice[0] for choice in Booking.BOOKING_STATUS]
        if new_status not in valid_statuses:
            return Response({"error": f"Trạng thái không hợp lệ. Các giá trị hợp lệ: {valid_statuses}"},
                            status=status.HTTP_400_BAD_REQUEST)

        booking.status = new_status
        booking.save()
        return Response({"message": "Cập nhật trạng thái thành công.", "status": booking.status})


@extend_schema(tags=["app_treatment"])
def _parse_ids(param: str):
    if not param:
        return None
    out = []
    for p in str(param).split(","):
        p = p.strip()
        if p.isdigit():
            out.append(int(p))
    return out or None

@extend_schema(tags=["app_treatment"])
class ExaminationOrderViewSet(viewsets.ModelViewSet):
    serializer_class = ExaminationOrderSerializer

    def get_queryset(self):
        qs = (ExaminationOrder.objects
            .select_related("customer", "doctor_profile")  # Sửa "doctor" thành "doctor_profile"
            .prefetch_related(Prefetch("items", queryset=ExaminationOrderItem.objects.select_related("test_service")))
            .order_by("-id"))

        customer_ids = _parse_ids(self.request.query_params.get("customer_id"))
        doctor_ids = _parse_ids(self.request.query_params.get("doctor"))

        if customer_ids:
            qs = qs.filter(customer_id__in=customer_ids)   # ✅
        if doctor_ids:
            qs = qs.filter(doctor_profile_id__in=doctor_ids)  # Sửa "doctor_id" thành "doctor_profile_id"
        return qs

    @action(detail=True, methods=["post"], url_path="add-services")
    def add_services(self, request, pk=None):
        """
        Thêm nhanh nhiều test-service vào 1 đơn:
        {
          "items": [
            {"test_service": 1, "quantity": 1, "note": "máu tổng quát"},
            {"test_service": 2, "quantity": 2}
          ]
        }
        """
        order = self.get_object()
        items = request.data.get("items", [])
        if not isinstance(items, list) or not items:
            return Response({"detail": "items phải là danh sách không rỗng."},
                            status=status.HTTP_400_BAD_REQUEST)

        payload = []
        for it in items:
            payload.append(ExaminationOrderItem(order=order, **it))
        ExaminationOrderItem.objects.bulk_create(payload, ignore_conflicts=True)

        order.refresh_from_db()
        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)

@extend_schema(tags=["app_treatment"])
class ExaminationOrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = ExaminationOrderItemSerializer

    def get_queryset(self):
        qs = (ExaminationOrderItem.objects
              .select_related("order", "order__customer", "test_service")
              .order_by("-id"))

        order_ids = _parse_ids(self.request.query_params.get("order"))
        customer_ids = _parse_ids(self.request.query_params.get("customer"))

        if order_ids:
            qs = qs.filter(order_id__in=order_ids)

        if customer_ids:
            qs = qs.filter(order__customer_id__in=customer_ids)

        return qs
@extend_schema(tags=["app_treatment"])
@nurse_process_schema()
class DoctorHealthCheckViewSet(viewsets.ModelViewSet):
    queryset = DoctorHealthCheck.objects.all()
    serializer_class = DoctorHealthCheckSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, CollaboratorReadOnlyPermission]

    def get_queryset(self):
        search_term = self.request.query_params.get('searchTerm', None)
        customer_id   = self.request.query_params.get('customer_id',None)
        filters = Q()
        if search_term:
            search_filters = (
                Q(customer__name__icontains=search_term)|
                Q(customer__code__icontains=search_term)|
                Q(customer__mobile__icontains=search_term)|
                Q(customer__email__icontains=search_term)
            )
            filters &= search_filters
        if customer_id:
            filters &= Q(customer_id=customer_id)
        queryset = DoctorHealthCheck.objects.filter(filters)

        return queryset
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED )

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

@extend_schema(tags=["app_treatment"])
class ClinicalExaminationViewSet(viewsets.ModelViewSet):
    queryset = ClinicalExamination.objects.all()
    serializer_class = ClinicalExaminationSerializer
    permission_classes = [IsAuthenticated, CollaboratorReadOnlyPermission]
    pagination_class = CustomPagination

    def get_queryset(self):
        search_term = self.request.query_params.get("searchTerm")
        filters = Q()
        if search_term:
            filters &= Q(doctor_health_check_process__customer__name__icontains=search_term)  # ✅

        return (ClinicalExamination.objects
                .filter(filters)
                .select_related(
                    "doctor_health_check_process__customer",  # ✅
                    "floor", "department"
                )
                .order_by("-id"))

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

@extend_schema(tags=["app_treatment"])
@doctor_process_schema()
class DoctorProcessViewSet(viewsets.ModelViewSet):
    queryset = DoctorProcess.objects.all()
    serializer_class = DoctorProcessSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, CollaboratorReadOnlyPermission]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if ServiceAssign.objects.filter(doctor_process__pk=instance.pk).exists():
            return Response(
                {"error": "Không thể cập nhật dữ liệu của bác sĩ vì đã có dữ liệu của chuyên gia chỉ định."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if instance.medicines_has_paid and 'diagnosis_medicines' in request.data:
            return Response(
                {"error": "Không thể cập nhật vì thuốc đã được thanh toán"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if ServiceAssign.objects.filter(doctor_process__pk=instance.pk).exists():
            return Response(
                {"error": "Không thể xóa dữ liệu của bác sĩ vì đã có dữ liệu của chuyên gia chỉ định."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if instance.medicines_has_paid:
            return Response(
                {"error": "Không thể xóa vì thuốc đã được thanh toán"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)
    
    def get_queryset(self):
        qs = (super()
            .get_queryset()
            .select_related("medicine_discount", "doctor_profile")
            .prefetch_related(
                Prefetch("diagnosis_medicines",
                        queryset=diagnosis_medicine.objects.select_related("product", "unit"))
            ))
        customer_id = self.request.query_params.get("customer_id")
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        return qs

@extend_schema(tags=["app_treatment"])
class DiagnosisMedicineViewSet(viewsets.ModelViewSet):
    serializer_class = DiagnosisMedicineV2Serializer

    def get_queryset(self):
        qs = diagnosis_medicine.objects.select_related(
            "doctor_process__customer",
            "product", "unit"
        )
        customer_id = self.request.query_params.get("customer")
        doctor_id = self.request.query_params.get("doctor")
        if customer_id:
            qs = qs.filter(doctor_process__customer_id=customer_id)
        if doctor_id:
            qs = qs.filter(doctor_process__assigned_doctor_id=doctor_id)  # nếu có field
        return qs

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Có thể thêm validation ở đây nếu cần
        return super().destroy(request, *args, **kwargs)

@extend_schema(tags=["app_treatment"])
@service_assign_schema()
class ServiceAssignViewSet(viewsets.ModelViewSet):
    queryset = ServiceAssign.objects.all()
    serializer_class = ServiceAssignSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, CollaboratorReadOnlyPermission]

    def perform_create(self, serializer):
        serializer.save()
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.services_has_paid:
            return Response({"error": "Không thể xóa vì dịch vụ đã được thành toán"},status=status.HTTP_400_BAD_REQUEST)

        return super().destroy(request, *args, **kwargs)
    @action(detail=True, methods=['post'])
    def update_booking_from_experience_to_service(self, request, pk=None):
        instance = self.get_object()  # Lấy ServiceAssign hiện tại
        doctor_process = instance.doctor_process
        try:
            booking = doctor_process.nurse_process.booking
        except AttributeError:
            return Response(
                {"error": "DoctorProcess không liên kết với Booking hợp lệ."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if booking.classification == "experience":
            booking.classification = "experience_to_service"
            booking.save(update_fields=["classification"])
            return Response({"message": "Booking đã được cập nhật thành 'experience_to_service'."},status=status.HTTP_200_OK)
        elif booking.classification == "experience_to_service":
            return Response({"message": "Booking đã ở trạng thái 'experience_to_service', không cần cập nhật."},status=status.HTTP_200_OK)
        else:
            return Response({"error": "Chỉ có thể cập nhật khi booking đang ở trạng thái 'experience'."},status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_service_assign(self, request, pk=None):
        instance = self.get_object()
        doctor_process = instance.doctor_process
        try:
            booking = doctor_process.nurse_process.booking
        except AttributeError:
            return Response(
                {"error": "DoctorProcess không liên kết với Booking hợp lệ."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if booking.classification != "experience_to_service":
            return Response(
                {"error": "Chỉ có thể tạo ServiceAssign mới khi booking có classification 'experience_to_service'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        assigned_expert_id = request.data.get("assigned_expert_id", None)
        treatment_method = request.data.get("treatment_method", "")
        service_discount = request.data.get("service_discount", None)
        diagnosis_services_data = request.data.get("diagnosis_services", [])

        new_service_assign = ServiceAssign.objects.create(
            doctor_process=doctor_process,
            assigned_expert_id=assigned_expert_id,
            treatment_method=treatment_method,
            type="service",
            service_discount_id=service_discount,
        )

        for service_data in diagnosis_services_data:
            diagnosis_service.objects.create(
                service_assign=new_service_assign,
                service_id=service_data.get("service"),
                quantity=service_data.get("quantity", 1)
            )

        return Response(
            {
                "message": "ServiceAssign mới đã được tạo thành công.",
                "new_service_assign_id": new_service_assign.id
            },
            status=status.HTTP_201_CREATED
        )

@extend_schema(tags=["app_treatment"])
@bill_schema()
class BillViewSet(viewsets.ModelViewSet):
    active_dp_qs = DoctorProcess.objects.filter(is_active=True).order_by("-version", "-id")
    queryset = (
        Bill.objects
        .select_related("customer")
        .prefetch_related(Prefetch("customer__doctor_process", queryset=active_dp_qs))
        .order_by("-created")
    )
    serializer_class = BillListSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        customer_id = self.request.query_params.get('customer_id')
        customer    = self.request.query_params.get('customer')  # <-- tên cần tìm (chuỗi)
        start_date  = self.request.query_params.get('startDate')
        end_date    = self.request.query_params.get('endDate')
        paid_method = self.request.query_params.get('paid_method')

        filters = Q()
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])

        # Ưu tiên ID; nếu không có ID thì dùng tên (search tự do)
        if customer_id:
            filters &= Q(customer_id=customer_id)
        elif customer:
            s = customer.strip()
            # mở rộng: tên, mã KH, số ĐT
            filters &= (
                Q(customer__name__icontains=s) |
                Q(customer__code__icontains=s) |
                Q(customer__mobile__icontains=s)
            )

        qs = (
            self.queryset
            .filter(filters)
            .annotate(
                source_type = F('payments__ar_item__content_type__model'),
                source_id   = F('payments__ar_item__object_id'),
                pay_method  = F('payments__paid_method'),
            )
            .order_by('-created')
        )

        if paid_method:
            qs = qs.filter(pay_method=paid_method)

        return qs
    
    # 🆕 Tổng hợp theo KH dựa trên *Bill* đã lọc
    @action(detail=False, methods=['get'], url_path='customers-summary')
    def customers_summary(self, request):
        """
        Gộp theo customer từ queryset Bill (đã áp dụng filter của get_queryset()).
        Trả về:
          - ma_kh, ho_ten
          - cac_loai_dich_vu_su_dung: ['phác đồ','đơn thuốc','xuất vật tư',...]
          - so_tien_da_thanh_toan: tổng PaymentHistory.paid_amount
          - lan_thanh_toan_gan_nhat: MAX PaymentHistory.created
        """
        # 1) Lấy danh sách KH xuất hiện trong tập Bill đã filter
        bills_qs = self.get_queryset().select_related('customer').only('customer_id', 'customer__id', 'customer__code', 'customer__name')
        customer_ids = list({b.customer_id for b in bills_qs if b.customer_id})
        if not customer_ids:
            return Response([])

        # (Optional) Lọc khoảng thời gian thanh toán nếu muốn: ?paymentStart=YYYY-MM-DD&paymentEnd=YYYY-MM-DD
        pay_start = request.query_params.get('paymentStart')
        pay_end   = request.query_params.get('paymentEnd')

        pay_filter = {'customer_id__in': customer_ids}
        if pay_start:
            pay_filter['created__date__gte'] = pay_start
        if pay_end:
            pay_filter['created__date__lte'] = pay_end

        # 2) Lấy ARItem để suy loại dịch vụ sử dụng
        ar_items = (ARItem.objects
                    .filter(customer_id__in=customer_ids)
                    .select_related('content_type')
                    .only('customer_id', 'content_type'))

        # 3) Lấy PaymentHistory để tổng tiền + lần gần nhất
        payments = PaymentHistory.objects.filter(**pay_filter).only('customer_id', 'paid_amount', 'created')

        # 4) Map loại dịch vụ từ content_type.model
        type_map = defaultdict(set)
        for ar in ar_items:
            model = getattr(ar.content_type, 'model', None)
            if model == 'doctorprocess':
                label = 'đơn thuốc'
            elif model == 'treatmentrequest':
                label = 'phác đồ'
            elif model in ('materialissue', 'warehouseissue', 'issuematerial'):
                label = 'xuất vật tư'
            else:
                label = model or 'khác'
            type_map[ar.customer_id].add(label)

        # 5) Tổng tiền & lần thanh toán gần nhất
        total_paid_map = defaultdict(Decimal)
        latest_paid_map = {}
        for p in payments:
            amt = p.paid_amount or Decimal('0')
            total_paid_map[p.customer_id] += amt
            if p.customer_id not in latest_paid_map or p.created > latest_paid_map[p.customer_id]:
                latest_paid_map[p.customer_id] = p.created

        # 6) Build output (mỗi KH chỉ 1 dòng)
        out = []
        seen = set()
        for b in bills_qs:
            c = b.customer
            if not c or c.id in seen:
                continue
            seen.add(c.id)
            out.append({
                "ma_kh": c.code,
                "ho_ten": c.name,
                "cac_loai_dich_vu_su_dung": sorted(type_map.get(c.id, set())),
                "so_tien_da_thanh_toan": str(total_paid_map.get(c.id, Decimal('0'))),
                "lan_thanh_toan_gan_nhat": latest_paid_map.get(c.id),
            })

        # (Optional) sort theo tên KH
        out.sort(key=lambda x: (x["ho_ten"] or "").lower())
        return Response(out)
    
    @action(detail=False, methods=['get'], url_path='customer-bills')
    def customer_bills(self, request):
        customer_id   = request.query_params.get('customer_id')
        customer_code = request.query_params.get('customer_code')  # = ma_kh
        start_date    = request.query_params.get('startDate')
        end_date      = request.query_params.get('endDate')

        # Map customer_code -> customer_id nếu cần
        if not customer_id and customer_code:
            from app_customer.models import Customer
            customer_id = (Customer.objects
                        .filter(code=customer_code)
                        .values_list('id', flat=True)
                        .first())

        if not customer_id:
            return Response({"detail": "Missing customer_id or customer_code"}, status=400)

        pay_filters = Q(customer_id=customer_id)
        if start_date and end_date:
            pay_filters &= Q(created__date__range=[start_date, end_date])

        payments = (PaymentHistory.objects
                    .filter(pay_filters)
                    .select_related('ar_item__content_type')
                    .only('paid_amount', 'paid_method', 'created',
                        'ar_item__content_type__model'))

        # ✅ dùng Optional thay vì str | None
        def map_type(model: Optional[str]) -> str:
            if model == 'doctorprocess':
                return 'Đơn thuốc'
            if model == 'treatmentrequest':
                return 'Phác đồ'
            if model in ('materialissue', 'warehouseissue', 'issuematerial', 'stockout'):
                return 'Xuất vật tư'
            return 'Khác'

        def map_method(m: Optional[str]) -> str:
            if not m:
                return '—'
            if m == 'cash':
                return 'Tiền mặt'
            if m == 'transfer':
                return 'Chuyển khoản'
            return m

        data = []
        for p in payments:
            ct = getattr(getattr(p, 'ar_item', None), 'content_type', None)
            model = getattr(ct, 'model', None)
            data.append({
                "type": map_type(model),
                "method": map_method(p.paid_method),
                "amount": str(p.paid_amount or Decimal('0')),
                "created": p.created,  # DRF sẽ serialize ISO
            })

        # sort mới nhất trước, handle None
        data.sort(key=lambda x: x["created"] or "", reverse=True)
        return Response(data)

# ----- helpers cho Bill: hỗ trợ cả amount_paid và paid_ammount -----
def _get_bill_paid(bill: Bill) -> Decimal:
    if hasattr(bill, "amount_paid"):
        return bill.amount_paid or Decimal("0")
    return getattr(bill, "paid_ammount", Decimal("0")) or Decimal("0")

def _set_bill_paid(bill: Bill, value: Decimal) -> None:
    if hasattr(bill, "amount_paid"):
        bill.amount_paid = value
        bill.save(update_fields=["amount_paid"])
    else:
        bill.paid_ammount = value
        bill.save(update_fields=["paid_ammount"])

def _new_bill_kwargs(customer, amount: Decimal) -> dict:
    # tạo kwargs tương thích với schema Bill hiện tại
    if "amount_paid" in [f.name for f in Bill._meta.get_fields()]:
        return {"customer": customer, "amount_paid": amount}
    return {"customer": customer, "paid_ammount": amount}
        
class PaymentHistoryViewSet(viewsets.ModelViewSet):
    queryset = PaymentHistory.objects.select_related('ar_item','customer')
    serializer_class = PaymentHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        # hỗ trợ filter theo ar_item, date range, paid_method…
        ar_item = self.request.query_params.get('ar_item')
        if ar_item: qs = qs.filter(ar_item_id=ar_item)
        start = self.request.query_params.get('startDate')
        end = self.request.query_params.get('endDate')
        if start and end: qs = qs.filter(created__date__range=[start, end])
        method = self.request.query_params.get('paid_method')
        if method: qs = qs.filter(paid_method=method)
        return qs.order_by('-created')

@extend_schema(tags=["app_treatment"])
class TreatmentRequestAPIView(APIView):
    serializer_class = TreatmentRequestSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        """API PATCH để cập nhật is_done"""
        instance = get_object_or_404(TreatmentRequest, pk=pk)

        if "is_done" not in request.data:
            return Response({"error": "Only 'is_done' field can be updated"}, status=status.HTTP_400_BAD_REQUEST)

        if instance.is_done:
            return Response({"error": "Không thể cập nhật khi đã hoàn thành"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            instance.is_done = request.data["is_done"]
            instance.save(update_fields=["is_done"])

        serializer = TreatmentRequestSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(tags=["app_treatment"])
@treatment_request_schema()
class TreatmentRequestViewSet(viewsets.ModelViewSet):
    queryset = TreatmentRequest.objects.all()
    serializer_class = TreatmentRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        qs = (super().get_queryset()
              .select_related('service', 'doctor_profile', 'discount')
              .prefetch_related('treatment_sessions__booking'))  # ✅ đúng related_name

        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            # Lọc qua chuỗi: TreatmentRequest -> treatment_sessions -> booking -> customer
            qs = qs.filter(
                treatment_sessions__booking__customer_id=customer_id
            ).distinct()  # tránh trùng TR vì nhiều session

        return qs.order_by('-created_at', '-id')
    
@extend_schema(tags=["app_treatment"])
class TreatmentSessionViewSet(viewsets.ModelViewSet):
    queryset = TreatmentSession.objects.all().select_related("treatment_request", "floor")
    serializer_class = TreatmentSessionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            treatment_session = serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            treatment_session = serializer.save()
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Delete operation is not allowed."}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['post'], url_path='create-techical-setting')
    def create_session_techical_setting(self, request, pk=None):
        session = self.get_object()
        data_list = request.data.get('session_techical_settings', [])
        if not data_list:
            return Response({"detail": "Thiếu danh sách item"}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        for row in data_list:
            tech_id = row.get('techical_setting')
            expert_id = row.get('expert_id')  # ⬅️ đổi sang singular
            duration_minutes = row.get('duration_minutes', 10)
            room = row.get('room')
            has_come = row.get('has_come', False)

            ts = TechicalSetting.objects.filter(id=tech_id).first()
            if not ts:
                return Response({"detail": f"Kỹ thuật {tech_id} không tồn tại"}, status=status.HTTP_400_BAD_REQUEST)

            item = SessionTechicalSetting.objects.create(
                session=session,
                techical_setting=ts,
                duration_minutes=duration_minutes,
                room=room,
                has_come=has_come,
                expert_id=expert_id,   # ⬅️ gán trực tiếp, cho phép None
            )
            created.append(item)

        return Response(SessionTechicalSettingSerializer(created, many=True).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='add-designated-experts')
    def add_designated_experts(self, request, pk=None):
        session = self.get_object()  # ✅ đúng model
        user_ids = request.data.get('user_ids', [])
        if not isinstance(user_ids, list) or not user_ids:
            return Response({"detail": "Danh sách user_ids không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST)

        users = User.objects.filter(id__in=user_ids)
        if users.count() != len(set(user_ids)):
            return Response({"detail": "Một hoặc nhiều user_id không tồn tại."}, status=status.HTTP_400_BAD_REQUEST)

        session.designated_experts.add(*users)  # ✅ đúng field
        return Response({"detail": "Chuyên gia đã được thêm thành công."}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch'], url_path='update-techical-setting')
    def update_session_techical_setting(self, request, pk=None):
        session = self.get_object()
        item_id = request.data.get('id')
        if not item_id:
            return Response({"detail": "Thiếu id item"}, status=status.HTTP_400_BAD_REQUEST)

        item = SessionTechicalSetting.objects.filter(id=item_id, session=session).first()
        if not item:
            return Response({"detail": "Item không thuộc buổi này"}, status=status.HTTP_404_NOT_FOUND)

        tech_id = request.data.get('techical_setting_id')
        if tech_id:
            ts = TechicalSetting.objects.filter(id=tech_id).first()
            if not ts:
                return Response({"detail": "Kỹ thuật không tồn tại"}, status=status.HTTP_400_BAD_REQUEST)
            req = session.treatment_request
            if getattr(ts, 'service_id', None) and req.service_id and ts.service_id != req.service_id:
                return Response({"detail": "Kỹ thuật không thuộc dịch vụ của phác đồ"}, status=status.HTTP_400_BAD_REQUEST)
            item.techical_setting = ts

        if 'duration_minutes' in request.data:
            item.duration_minutes = request.data['duration_minutes']
        if 'room' in request.data:
            item.room = request.data['room']
        if 'has_come' in request.data:
            item.has_come = bool(request.data['has_come'])

        if 'expert_id' in request.data:              # ⬅️ cập nhật chuyên gia đơn
            item.expert_id = request.data.get('expert_id') or None

        item.save()
        return Response(SessionTechicalSettingSerializer(item).data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'], url_path='delete-techical-setting/(?P<item_id>[^/.]+)')
    def delete_session_techical_setting(self, request, item_id=None, pk=None):
        session = self.get_object()
        item = SessionTechicalSetting.objects.filter(id=item_id, session=session).first()
        if not item:
            return Response({"detail": "Item không thuộc buổi này"}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _sync_booking_has_come(self, session):
        """Đồng bộ booking.has_come = tồn tại ít nhất 1 kỹ thuật has_come=True trong buổi."""
        booking = getattr(session, "booking", None)
        if not booking:  # buổi có thể chưa tạo booking
            return
        any_true = session.sessiontechicalsetting_set.filter(has_come=True).exists()
        if booking.has_come != any_true:
            booking.has_come = any_true
            booking.save(update_fields=["has_come"])

    @action(detail=True, methods=['post'], url_path='mark-come')
    def mark_come(self, request, pk=None):
        """
        Cập nhật nhanh trạng thái đến trị liệu cho một item kỹ thuật của buổi này.
        Body: {"item_id": 123, "has_come": true}
        """
        session = self.get_object()
        item_id = request.data.get('item_id')
        has_come = bool(request.data.get('has_come', True))
        if not item_id:
            return Response({"detail": "Thiếu item_id"}, status=status.HTTP_400_BAD_REQUEST)

        item = SessionTechicalSetting.objects.filter(id=item_id, session=session).first()
        if not item:
            return Response({"detail": "Item không thuộc buổi này"}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            # 1) Cập nhật kỹ thuật
            if item.has_come != has_come:
                item.has_come = has_come
                item.save(update_fields=['has_come'])

            # 2) Đồng bộ booking của buổi
            self._sync_booking_has_come(session)

        return Response(SessionTechicalSettingSerializer(item).data, status=status.HTTP_200_OK)
    
@extend_schema(tags=["app_treatment"])
class ReExaminationViewSet(viewsets.ModelViewSet):
    queryset = ReExamination.objects.all()
    serializer_class = ReExaminationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        status = self.request.query_params.get('status', None)
        search_term = self.request.query_params.get('searchTerm', None)

        filters = Q(is_active=True)
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (

            )
            filters &= search_filters

        if status:
            filters &= Q(status=status)

        queryset = ReExamination.objects.filter(filters).order_by('-created')

        return queryset

@extend_schema(tags=["app_treatment"])
class BillNeedViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillNeedSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        customer_id = self.request.query_params.get('customer_id')
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')

        filters = Q()
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if customer_id:
            filters &= Q(customer_id=customer_id)   # ✅
        return Bill.objects.filter(filters).order_by('-created')

    @action(detail=True, methods=['get'])
    def used_products_services(self, request, pk=None):
        # giống như BillViewSet.used_products_services ở trên
        bill = self.get_object()
        total_amount = bill.get_total_amount()
        products, services = [], []
        try:
            dhc = bill.customer.doctor_health_check
            ce = getattr(dhc, "clinical_examination", None)
            if ce:
                dps = ce.doctor_process.all()
                if dps.exists():
                    for dp in dps:
                        products.extend(list(dp.products.all()))
                        for sa in dp.service_assign.all():
                            services.extend(list(Service.objects.filter(diagnosis_service__service_assign=sa).distinct()))
        except Exception:
            pass

        product_serializer = ProductSerializer(products, many=True)
        service_serializer = ServiceSerializer(services, many=True)
        return Response({
            "total_amount": total_amount,
            "products": product_serializer.data,
            "services": service_serializer.data
        })
@extend_schema(tags=["app_treatment"])
@extend_schema_view(
    list=extend_schema(
        tags=["app_treatment"],
        summary="Danh sách thống kê phác đồ theo user",
        description=(
            "Trả về danh sách user kèm **số phác đồ** theo loại dịch vụ:\n"
            "- `total_tlcb`: số phác đồ Trị liệu chữa bệnh (TLCB)\n"
            "- `total_tlds`: số phác đồ Trị liệu dưỡng sinh (TLDS)\n\n"
            "Hỗ trợ **lọc theo thời gian** và **tìm kiếm user**."
        ),
        parameters=[
            # Lọc theo thời gian (áp dụng vào TreatmentRequest.created_at)
            OpenApiParameter(
                name="start",
                description="Ngày bắt đầu (YYYY-MM-DD). Lọc theo `treatment_request__created_at >= start`.",
                required=False, type=str, location=OpenApiParameter.QUERY
            ),
            OpenApiParameter(
                name="end",
                description="Ngày kết thúc (YYYY-MM-DD). Lọc theo `treatment_request__created_at <= end`.",
                required=False, type=str, location=OpenApiParameter.QUERY
            ),

            # Tìm kiếm user
            OpenApiParameter(
                name="search",
                description="Tìm theo username, họ tên (first/last) hoặc email.",
                required=False, type=str, location=OpenApiParameter.QUERY
            ),

            # Lọc user theo hoạt động có phát sinh phác đồ trong khoảng thời gian
            OpenApiParameter(
                name="has_activity",
                description="`true|false` - Chỉ lấy user có/không có phác đồ trong khoảng thời gian lọc.",
                required=False, type=str, location=OpenApiParameter.QUERY,
                examples=[
                    {"name": "Có hoạt động", "value": "true"},
                    {"name": "Không hoạt động", "value": "false"},
                ]
            ),

            # Lọc theo trạng thái kích hoạt tài khoản
            OpenApiParameter(
                name="is_active",
                description="`true|false` - Lọc theo trạng thái hoạt động của user.",
                required=False, type=str, location=OpenApiParameter.QUERY
            ),

            # (tuỳ chọn) Lọc theo loại dịch vụ: chỉ giữ user có ít nhất 1 phác đồ loại đó
            OpenApiParameter(
                name="service_type",
                description="Chỉ giữ user có phát sinh **ít nhất một phác đồ** thuộc loại này trong khoảng thời gian. Enum: TLCB, TLDS.",
                required=False, type=str, location=OpenApiParameter.QUERY,
                enum=["TLCB", "TLDS"]
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Danh sách user + thống kê phác đồ",
                response=UserServiceStatsSerializer(many=True)
            )
        },
        examples=[
            # Ví dụ gọi API
        ]
    )
)
class UserServiceStatsListView(generics.ListAPIView):
    """
    GET /api/users/service-stats/?start=2025-08-01&end=2025-08-31
    Trả về danh sách tất cả user + số phác đồ TLCB, TLDS
    """
    queryset = User.objects.all()
    serializer_class = UserServiceStatsSerializer
    permission_classes = [IsAuthenticated]

class PayrollAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        data = get_performance_payroll(start_date, end_date)
        return Response(data)
    
class ExpertTechniqueDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, expert_id: int):
        ttype  = request.query_params.get("type")  # "TLCB" | "TLDS" | None
        start  = parse_date(request.query_params.get("startDate") or "") or date.min
        end    = parse_date(request.query_params.get("endDate") or "") or date.today()

        if start > end:
            return Response({"detail": "startDate must be <= endDate"}, status=status.HTTP_400_BAD_REQUEST)

        # ⚙️ Đồng bộ cửa sổ thời gian với payroll:
        # - receiving_day ∈ [start, end]  OR  treatment_request.created_at::date ∈ [start, end]
        time_filter = (
            Q(session__booking__receiving_day__range=(start, end)) |
            Q(session__treatment_request__created_at__date__range=(start, end))
        )

        base = (
            SessionTechicalSetting.objects
            .select_related("session", "session__booking", "techical_setting", "expert")
            .filter(
                has_come=True,
                expert_id=expert_id,
            )
            .filter(time_filter)
        )

        if ttype in ("TLCB", "TLDS"):
            base = base.filter(techical_setting__type=ttype)

        rows = (
            base.values(
                "session__booking__customer_id",
                "session__booking__customer__name",
                "session__booking__customer__code",
                "session__booking__receiving_day",
                "techical_setting__name",
                "techical_setting__type",
            )
            .annotate(count=Count("id"))
            .order_by(
                "session__booking__customer__name",
                "-session__booking__receiving_day",
                "techical_setting__name",
            )
        )

        groups_map = {}
        for r in rows:
            cid   = r["session__booking__customer_id"]
            cname = r["session__booking__customer__name"]
            ccode = r["session__booking__customer__code"]
            ctype = r["techical_setting__type"] or None

            key = (cid, ctype)
            if key not in groups_map:
                groups_map[key] = {
                    "customer": {"id": cid, "name": cname, "code": ccode},
                    "treatment_type": ctype,
                    "total_count": 0,
                    "details": [],
                }

            groups_map[key]["details"].append({
                "date": r["session__booking__receiving_day"],
                "technique_name": r["techical_setting__name"],
                "count": r["count"],
            })
            groups_map[key]["total_count"] += r["count"]

        groups = list(groups_map.values())

        user = User.objects.filter(id=expert_id).only("id", "first_name", "last_name", "username").first()
        full_name = (user.get_full_name() or user.username) if user else None

        summary = {
            "total_customers": len({g["customer"]["id"] for g in groups}),
            "total_sessions": sum(g["total_count"] for g in groups),
        }

        return Response({
            "employee": {"id": expert_id, "full_name": full_name},
            "summary": summary,
            "groups": groups
        })
        
class ARItemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Danh sách công nợ theo khách / theo trạng thái.
    GET /api/app-treatments/v1/ar-items/?customer_id=1&status=open,partial
    """
    queryset = ARItem.objects.all().select_related("customer", "content_type")
    serializer_class = ARItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        customer_id = self.request.query_params.get("customer_id")
        status_in = self.request.query_params.get("status")  # csv: open,partial,closed
        source_type = self.request.query_params.get("source_type")  # "treatmentrequest" | "doctorprocess"
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if status_in:
            statuses = [s.strip() for s in status_in.split(",") if s.strip()]
            qs = qs.filter(status__in=statuses)
        if source_type:
            qs = qs.filter(content_type__model=source_type.lower())
        return qs.order_by("-created", "-id")

    @action(detail=False, methods=["get"], url_path="by-customer/(?P<customer_id>[^/.]+)")
    def by_customer(self, request, customer_id=None):
        qs = self.get_queryset().filter(customer_id=customer_id)
        return Response(self.get_serializer(qs, many=True).data)
