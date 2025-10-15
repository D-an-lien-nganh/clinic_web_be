from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from django.db.models import Q, Sum, F
from django.db import transaction
from django.utils.dateparse import parse_date 
from decimal import Decimal
from rest_framework.viewsets import GenericViewSet

from .models import STOCK_IN_STATUS, STOCK_OUT_STATUS, FacilityExport,\
Service, Product, Maintenance, FixSchedule, Facility, ServiceTechnicalSetting, ServiceTreatmentPackage, Supplier, StockIn, StockOut, Warehouse,TechicalSetting
from .serializers import FacilityExportSerializer, ServiceSerializer, ProductSerializer, MaintenanceSerializer, FixScheduleSerializer, FacilitySerializer, ServiceTechnicalSettingSerializer, SupplierSerializer, StockInSerializer, StockOutSerializer, ServiceTreatmentPackageReadSerializer, WarehouseSerializer,TechicalSettingSerializer
from app_home.views import CollaboratorReadOnlyPermission
from app_home.pagination import CustomPagination
from .docs import *
@extend_schema(tags=["app_product"])
@service_schema()
class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, CollaboratorReadOnlyPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)
        status = self.request.query_params.get('status', None)

        filters = Q()
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (
                Q(name__icontains=search_term) |
                Q(code__icontains=search_term)|
                Q(effect__icontains=search_term) |
                Q(price__icontains=search_term)
            )
            filters &= search_filters

        if status:
            filters &= Q(status=status)

        queryset = Service.objects.filter(filters).order_by('-created')

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema(tags=["app_product"])
@product_schema_view()
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, CollaboratorReadOnlyPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)
        status = self.request.query_params.get('status', None)

        filters = Q()
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (
                Q(name__icontains=search_term) |
                Q(code__icontains=search_term)|
                Q(effect__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(origin__icontains=search_term)
            )
            filters &= search_filters

        if status:
            filters &= Q(status=status)

        queryset = Product.objects.filter(filters).order_by('-created')

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema(tags=["app_product"])
@maintenance_schema_view()
class MaintenanceViewSet(viewsets.ModelViewSet):
    serializer_class = MaintenanceSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        facility_id = self.request.query_params.get("facility_id")
        if facility_id:
            return Maintenance.objects.filter(facility_id=facility_id)
        return Maintenance.objects.all()
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema(tags=["app_product"])
@fix_schedule_schema_view()
class FixScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = FixScheduleSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        facility_id = self.request.query_params.get("facility_id")
        if facility_id:
            return FixSchedule.objects.filter(facility_id=facility_id)
        return FixSchedule.objects.all()
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema(tags=["app_product"])
@facility_schema_view()
class FacilityViewSet(viewsets.ModelViewSet):
    serializer_class = FacilitySerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, CollaboratorReadOnlyPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)
        status = self.request.query_params.get('status', None)
        is_malfunction = self.request.query_params.get('is_malfunction', None)

        filters = Q(is_active=True)
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (
                Q(name__icontains=search_term) |
                Q(code__icontains=search_term)|
                Q(effect__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(origin__icontains=search_term)
            )
            filters &= search_filters

        if status:
            filters &= Q(status=status)

        if is_malfunction is not None:
            filters &= Q(is_malfunction=is_malfunction.lower() in ['true', '1'])

        queryset = Facility.objects.filter(filters).order_by('-created')

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(
            {"detail": "Đã xóa vật tư (is_active=false)."},
            status=status.HTTP_200_OK
        )
@extend_schema(tags=["app_product"])
class FacilityExportViewSet(viewsets.ModelViewSet):
    queryset = FacilityExport.objects.select_related("facility").all()
    serializer_class = FacilityExportSerializer
@extend_schema(tags=["app_product"])
@supplier_schema_view()
class SupplierViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, CollaboratorReadOnlyPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)

        filters = Q(is_active=True)
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (
                Q(name__icontains=search_term) |
                Q(contact_person__icontains=search_term) |
                Q(mobile__icontains=search_term) |
                Q(email__icontains=search_term)
            )
            filters &= search_filters

        queryset = Supplier.objects.filter(filters).order_by('-created')

        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@extend_schema(tags=["app_product"])
@stock_in_schema_view()
class StockInViewSet(viewsets.ModelViewSet):
    serializer_class = StockInSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, CollaboratorReadOnlyPermission]

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
                Q(code__icontains=search_term) |
                Q(user_username__icontains=search_term)|
                Q(supplier_name__icontains=search_term) |
                Q(supplier_MST__icontains=search_term) |
                Q(product_name_icontains=search_term) |
                Q(product_code__icontains=search_term) |
                Q(approver_username__icontains=search_term)
            )
            filters &= search_filters

        if status:
            filters &= Q(status=status)

        queryset = StockIn.objects.filter(filters).order_by('-created')

        return queryset
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        return super().partial_update(request, *args, **kwargs)
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(
            {"detail": "Đã xóa đơn nhập (is_active=false)."},
            status=status.HTTP_200_OK
        )

@extend_schema(tags=["app_product"])
@stock_out_schema_view()
class StockOutViewSet(viewsets.ModelViewSet):
    serializer_class = StockOutSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated, CollaboratorReadOnlyPermission]

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        type_ = self.request.query_params.get('type', None)
        search_term = self.request.query_params.get('searchTerm', None)

        filters = Q(is_active=True)
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])

        if search_term:
            filters &= (
                Q(code__icontains=search_term) |
                Q(user__username__icontains=search_term) |
                Q(product__name__icontains=search_term) |
                Q(product__code__icontains=search_term) |
                Q(supplier__name__icontains=search_term) |
                Q(supplier__MST__icontains=search_term) |
                Q(approver__username__icontains=search_term) |
                Q(customer__name__icontains=search_term)
            )

        if type_:
            filters &= Q(type=type_)

        return StockOut.objects.filter(filters).order_by('-created')

    def _get_total_stock(self, product):
        return Warehouse.objects.filter(product=product).aggregate(total=Sum('quantity'))['total'] or 0

    def _reduce_total_stock(self, product, need_qty: int):
        """
        Trừ tồn tổng (không theo lô). Duyệt các dòng Warehouse theo id/created, trừ dần.
        Với phương án B, thứ tự không quan trọng; dùng FIFO nhẹ để dễ hiểu.
        """
        remain = need_qty
        # khoá select_for_update để tránh race condition song song xuất cùng sản phẩm
        rows = (Warehouse.objects
                .select_for_update()
                .filter(product=product, quantity__gt=0)
                .order_by('id'))
        for w in rows:
            if remain <= 0:
                break
            take = min(w.quantity, remain)
            w.quantity -= take
            w.save(update_fields=['quantity'])
            remain -= take
        if remain > 0:
            # Không đủ tồn (đã có validate trước, nhưng check lần nữa cho an toàn)
            raise ValidationError({"detail": "Không đủ tồn kho để trừ số lượng yêu cầu."})

    @transaction.atomic
    def perform_create(self, serializer):
        from decimal import Decimal
        product = serializer.validated_data.get('product')
        quantity = int(serializer.validated_data.get('quantity') or 0)
        actual_unit_price = serializer.validated_data.get('actual_stockout_price') or Decimal('0')

        # 1) Đơn giá xuất ≥ đơn giá gốc (đơn giá, không phải tổng)
        base_unit_price = product.sell_price or Decimal('0')
        if actual_unit_price < base_unit_price:
            raise ValidationError({"actual_stockout_price": "Đơn giá xuất không được nhỏ hơn đơn giá gốc."})

        # 2) Kiểm tồn theo tổng sản phẩm
        total_stock = self._get_total_stock(product)
        if quantity > total_stock:
            raise ValidationError({"detail": f"Số lượng cần xuất ({quantity}) lớn hơn tổng tồn kho ({total_stock})."})

        # 3) Trừ tồn ngay (phương án B: theo tổng, không cần theo lô)
        self._reduce_total_stock(product, quantity)

        # 4) Lưu phiếu xuất
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"detail": "Đơn xuất kho đã được tạo thành công.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        return Response({"detail": "Đã xóa đơn xuất (is_active=false)."}, status=status.HTTP_200_OK)
    
@extend_schema(tags=["app_product"])
@warehouse_schema_view()
class WarehouseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated, CollaboratorReadOnlyPermission]
    pagination_class = CustomPagination

    def get_queryset(self):
        start_date = self.request.query_params.get('startDate')
        end_date = self.request.query_params.get('endDate')
        search_term = self.request.query_params.get('searchTerm', None)

        filters = Q()
        if start_date and end_date:
            filters &= Q(created__date__range=[start_date, end_date])
        if search_term:
            search_filters = (
                Q(code__icontains=search_term) |
                Q(user_username__icontains=search_term)|
                Q(product_name_icontains=search_term) |
                Q(supplier_name__icontains=search_term) |
                Q(supplier_MST__icontains=search_term) |
                Q(product_code__icontains=search_term)
            )
            filters &= search_filters

        queryset = Warehouse.objects.filter(filters).order_by('-created')

        return queryset
    
    @action(detail=True, methods=["GET"], url_path="ledger")
    def ledger(self, request, pk=None):
        """
        Sổ chi tiết tồn kho theo Warehouse (lọc theo type bắt buộc).
        Query params:
        - type: import | export  (BẮT BUỘC)
        - scope: product (default) | supplier
        - date_from, date_to: YYYY-MM-DD
        Trả về:
        - Nếu type=import: NCC, đơn vị, số lượng, đơn giá (giá nhập), thành tiền = qty * import_price
        - Nếu type=export: đơn vị, số lượng, đơn giá (giá nhập tham chiếu), giá xuất, thành tiền = qty * export_price
        """
        wh = self.get_object()
        product = wh.product
        supplier = wh.supplier

        _type = (request.query_params.get("type") or "").lower()
        if _type not in {"import", "export"}:
            return Response(
                {"detail": "Param 'type' is required and must be 'import' or 'export'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        scope = (request.query_params.get("scope") or "product").lower()  # product|supplier
        date_from = parse_date(request.query_params.get("date_from") or "")
        date_to = parse_date(request.query_params.get("date_to") or "")

        # helper: lấy đơn giá nhập gần nhất trước (hoặc bằng) ngày chỉ định; fallback nhập mới nhất
        def get_last_import_price(as_of_date=None):
            base_qs = StockIn.objects.filter(product=product)
            if scope == "supplier":
                base_qs = base_qs.filter(supplier=supplier)
            if as_of_date:
                price = (
                    base_qs.filter(import_date__lte=as_of_date)
                    .order_by("-import_date", "-id")
                    .values_list("import_price", flat=True)
                    .first()
                )
                if price is not None:
                    return price
            return (
                base_qs.order_by("-import_date", "-id")
                .values_list("import_price", flat=True)
                .first()
            )

        unit_name = getattr(getattr(product, "unit", None), "name", None)

        header = {
            "warehouse_id": wh.id,
            "scope": scope,
            "type": _type,
            "product": {
                "id": product.id,
                "code": getattr(product, "code", None),
                "name": getattr(product, "name", None),
                "unit_name": unit_name,
            },
            "supplier": (
                {"id": supplier.id, "name": supplier.name} if scope == "supplier" else None
            ),
        }

        # ------------------ IMPORT ONLY ------------------
        if _type == "import":
            in_filters = Q(product=product)
            if scope == "supplier":
                in_filters &= Q(supplier=supplier)
            if date_from and date_to:
                in_filters &= Q(import_date__range=[date_from, date_to])
            elif date_from:
                in_filters &= Q(import_date__gte=date_from)
            elif date_to:
                in_filters &= Q(import_date__lte=date_to)

            stockins = (
                StockIn.objects
                .select_related("supplier", "product__unit")
                .filter(in_filters)
                .order_by("import_date", "id")
                .values("id", "code", "import_date", "quantity", "import_price", "supplier__name")
            )

            items = []
            for si in stockins:
                qty = int(si["quantity"] or 0)
                ip = Decimal(si["import_price"] or 0)
                items.append({
                    "type": "import",
                    "date": si["import_date"],
                    "code": si["code"],
                    "unit_name": unit_name,
                    "supplier_name": si["supplier__name"],
                    "quantity": qty,
                    "import_unit_price": str(ip),
                    "amount": str(ip * qty),
                })

            return Response({"header": header, "items": items, "count": len(items)})

        # ------------------ EXPORT ONLY ------------------
        if _type == "export":
            out_filters = Q(product=product)
            if date_from and date_to:
                out_filters &= Q(export_date__range=[date_from, date_to])
            elif date_from:
                out_filters &= Q(export_date__gte=date_from)
            elif date_to:
                out_filters &= Q(export_date__lte=date_to)

            stockouts = (
                StockOut.objects
                .select_related("product__unit")
                .filter(out_filters)
                .order_by("export_date", "id")
                .values("id", "code", "export_date", "quantity", "actual_stockout_price")
            )

            items = []
            for so in stockouts:
                qty = int(so["quantity"] or 0)
                sell_price = Decimal(so["actual_stockout_price"] or 0)
                ip = Decimal(get_last_import_price(as_of_date=so["export_date"]) or 0)

                items.append({
                    "type": "export",
                    "date": so["export_date"],
                    "code": so["code"],
                    "unit_name": unit_name,
                    "quantity": qty,
                    "import_unit_price": str(ip),          # đơn giá nhập tham chiếu
                    "export_unit_price": str(sell_price),  # giá xuất
                    "amount": str(sell_price * qty),       # thành tiền = qty * giá xuất
                })

            return Response({"header": header, "items": items, "count": len(items)})

@extend_schema(tags=["app_product"])
class TechicalSettingViewSet(viewsets.ModelViewSet):
    serializer_class = TechicalSettingSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    queryset = TechicalSetting.objects.all().order_by("-created")  # Sắp xếp theo mới nhất
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
                Q(user__username__icontains=search_term) |  
                Q(price__icontains=search_term)  
            )
            filters &= search_filters

        queryset = TechicalSetting.objects.filter(filters).order_by('-created')

        return queryset
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return Response(
                {"detail": "Không thể xóa vì đang được tham chiếu ở thực thể khác (ràng buộc PROTECT)."},
                status=status.HTTP_409_CONFLICT,
            )
        except IntegrityError:
            return Response(
                {"detail": "Xóa thất bại do ràng buộc toàn vẹn dữ liệu."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()

@extend_schema(tags=["app_product"])
@service_treatment_package_schema_view()
class ServiceTreatmentPackageViewSet(viewsets.ModelViewSet):
    queryset = ServiceTreatmentPackage.objects.all()
    serializer_class = ServiceTreatmentPackageReadSerializer
@extend_schema(tags=["app_product"])
class ServiceTechnicalSettingViewSet(viewsets.ModelViewSet):
    queryset = ServiceTechnicalSetting.objects.select_related('service', 'technical_setting').all()
    serializer_class = ServiceTechnicalSettingSerializer


    def get_queryset(self):
        queryset = super().get_queryset()
        service_id = self.request.query_params.get('service_id')
        technical_setting_id = self.request.query_params.get('technical_setting_id')

        if service_id:
            queryset = queryset.filter(service_id=service_id)
        if technical_setting_id:
            queryset = queryset.filter(technical_setting_id=technical_setting_id)

        return queryset

    @extend_schema(
        summary="Danh sách ServiceTechnicalSetting",
        parameters=[
            OpenApiParameter(name='service_id', description='Lọc theo ID dịch vụ', required=False, type=int),
            OpenApiParameter(name='technical_setting_id', description='Lọc theo ID kỹ thuật', required=False, type=int),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Tạo mới liên kết dịch vụ - kỹ thuật",
        examples=[
            OpenApiExample(
                name="Tạo liên kết",
                value={
                    "service_id": 1,
                    "technical_setting_id": 3
                }
            )
        ]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Lấy chi tiết 1 liên kết")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Cập nhật toàn phần liên kết")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Cập nhật một phần liên kết")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Xoá liên kết dịch vụ - kỹ thuật")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class InventoryViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def _filter_date_range(self, qs, field, start_date, end_date):
        if start_date:
            qs = qs.filter(**{f"{field}__gte": start_date})
        if end_date:
            qs = qs.filter(**{f"{field}__lte": end_date})
        return qs

    @action(detail=False, methods=["GET"], url_path="inventory-summary")
    def inventory_summary(self, request):
        start_date = parse_date(request.query_params.get("start_date") or "")
        end_date = parse_date(request.query_params.get("end_date") or "")

        data = []
        totals = {
            "open_qty": Decimal(0), "open_val": Decimal(0),
            "in_qty": Decimal(0), "in_val": Decimal(0),
            "out_qty": Decimal(0), "out_val": Decimal(0),
            "close_qty": Decimal(0), "close_val": Decimal(0),
        }

        for product in Product.objects.select_related("unit").all():
            stockins = StockIn.objects.filter(product=product)
            stockouts = StockOut.objects.filter(product=product)

            # FIX: Đầu kỳ là tồn kho đến hết ngày trước start_date
            if start_date:
                # Tính tồn đầu kỳ: tất cả giao dịch TRƯỚC start_date (< start_date)
                stockin_before = stockins.filter(import_date__lt=start_date)
                stockout_before = stockouts.filter(export_date__lt=start_date)
            else:
                # Nếu không có start_date, đầu kỳ = 0
                stockin_before = stockins.none()
                stockout_before = stockouts.none()

            # Giao dịch trong kỳ: từ start_date đến end_date
            stockins_period = self._filter_date_range(stockins, "import_date", start_date, end_date)
            stockouts_period = self._filter_date_range(stockouts, "export_date", start_date, end_date)

            # Tính số lượng và giá trị đầu kỳ
            open_qty = (stockin_before.aggregate(Sum("quantity"))["quantity__sum"] or 0) - \
                    (stockout_before.aggregate(Sum("quantity"))["quantity__sum"] or 0)
            open_val = (stockin_before.aggregate(total=Sum(F("quantity") * F("import_price")))["total"] or 0) - \
                    (stockout_before.aggregate(total=Sum(F("quantity") * F("actual_stockout_price")))["total"] or 0)

            # Giao dịch nhập trong kỳ
            in_qty = stockins_period.aggregate(Sum("quantity"))["quantity__sum"] or 0
            in_val = stockins_period.aggregate(total=Sum(F("quantity") * F("import_price")))["total"] or 0

            # Giao dịch xuất trong kỳ  
            out_qty = stockouts_period.aggregate(Sum("quantity"))["quantity__sum"] or 0
            out_val = stockouts_period.aggregate(total=Sum(F("quantity") * F("actual_stockout_price")))["total"] or 0

            # Tồn cuối kỳ
            close_qty = open_qty + in_qty - out_qty
            close_val = open_val + in_val - out_val

            row = {
                "product_id": product.id, 
                "product_code": product.code,
                "product_name": product.name,
                "unit": product.unit.name if product.unit else None,
                "open_qty": open_qty, "open_val": open_val,
                "in_qty": in_qty, "in_val": in_val,
                "out_qty": out_qty, "out_val": out_val,
                "close_qty": close_qty, "close_val": close_val,
            }
            data.append(row)

            # Cộng dồn tổng
            for key in totals:
                totals[key] += row[key]

        data.append({
            "product_id": None,
            "product_code": "TOTAL",
            "product_name": "TỔNG CỘNG",
            "unit": "",
            **totals,
        })

        # Phân trang kết quả
        page = self.paginate_queryset(data)
        if page is not None:
            return self.get_paginated_response(page)
        return Response(data)

    @action(detail=True, methods=["GET"], url_path="inventory-detail")
    def inventory_detail(self, request, pk=None):
        product = Product.objects.select_related("unit").get(pk=pk)
        start_date = parse_date(request.query_params.get("start_date") or "")
        end_date = parse_date(request.query_params.get("end_date") or "")

        # 1. Tính tồn đầu kỳ (trước start_date)
        open_qty = open_val = Decimal(0)
        if start_date:
            stockin_before = StockIn.objects.filter(product=product, import_date__lt=start_date)
            stockout_before = StockOut.objects.filter(product=product, export_date__lt=start_date)
            
            open_qty = (stockin_before.aggregate(Sum("quantity"))["quantity__sum"] or 0) - \
                    (stockout_before.aggregate(Sum("quantity"))["quantity__sum"] or 0)
            
            # Giá trị đầu kỳ tính theo giá nhập bình quân
            in_val_before = stockin_before.aggregate(total=Sum(F("quantity") * F("import_price")))["total"] or 0
            out_val_before = stockout_before.aggregate(total=Sum(F("quantity") * F("actual_stockout_price")))["total"] or 0
            open_val = in_val_before - out_val_before

        # 2. Lấy giao dịch trong kỳ
        stockins = self._filter_date_range(StockIn.objects.filter(product=product), "import_date", start_date, end_date)
        stockouts = self._filter_date_range(StockOut.objects.filter(product=product), "export_date", start_date, end_date)

        items = []
        
        # 3. Thêm dòng tồn đầu kỳ nếu có start_date
        if start_date and (open_qty != 0 or open_val != 0):
            items.append({
                "type": "opening",
                "product_name": product.name,
                "doc_date": start_date,
                "doc_code": "OPEN",
                "description": "Tồn đầu kỳ",
                "unit": product.unit.name if product.unit else None,
                "unit_price": None,
                "in_qty": 0, "in_val": 0,
                "out_qty": 0, "out_val": 0,
                "balance_qty": open_qty,
                "balance_val": open_val,
            })

        # 4. Thêm tất cả giao dịch và sắp xếp theo ngày
        current_qty = open_qty
        current_val = open_val
        tin_q = tin_v = tout_q = tout_v = Decimal(0)

        # Thu thập tất cả giao dịch
        all_transactions = []
        
        for si in stockins.select_related("supplier"):
            amt = si.get_total()
            all_transactions.append({
                "type": "import",
                "date": si.import_date,
                "product_name": product.name,
                "doc_date": si.import_date,
                "doc_code": si.code,
                "description": si.note or f"Nhập hàng {si.supplier.name if si.supplier else ''}",
                "unit": product.unit.name if product.unit else None,
                "unit_price": si.import_price,
                "in_qty": si.quantity, "in_val": amt,
                "out_qty": 0, "out_val": 0,
            })
            tin_q += si.quantity
            tin_v += amt

        for so in stockouts.select_related("supplier"):
            amt = so.original_stockout_price()
            all_transactions.append({
                "type": "export",
                "date": so.export_date,
                "product_name": product.name,
                "doc_date": so.export_date,
                "doc_code": so.code,
                "description": so.note or "Xuất bán/điều chuyển",
                "unit": product.unit.name if product.unit else None,
                "unit_price": so.actual_stockout_price,
                "in_qty": 0, "in_val": 0,
                "out_qty": so.quantity, "out_val": amt,
            })
            tout_q += so.quantity
            tout_v += amt

        # Sắp xếp theo ngày và thêm số dư running balance
        all_transactions.sort(key=lambda x: (x["date"], x["type"] == "export"))  # import trước export cùng ngày
        
        for trans in all_transactions:
            current_qty += trans["in_qty"] - trans["out_qty"]
            current_val += trans["in_val"] - trans["out_val"]
            
            trans["balance_qty"] = current_qty
            trans["balance_val"] = current_val
            items.append(trans)

        # 5. Thêm dòng tổng cộng
        items.append({
            "type": "TOTAL",
            "product_name": product.name,
            "doc_date": None,
            "doc_code": "TOTAL",
            "description": "TỔNG CỘNG",
            "unit": product.unit.name if product.unit else None,
            "unit_price": None,
            "in_qty": tin_q, "in_val": tin_v,
            "out_qty": tout_q, "out_val": tout_v,
            "balance_qty": current_qty,  # Tồn cuối kỳ
            "balance_val": current_val,
        })

        return Response({
            "product_id": product.id, 
            "product": product.name, 
            "start_date": start_date,
            "end_date": end_date,
            "opening_balance": {"qty": open_qty, "val": open_val},
            "closing_balance": {"qty": current_qty, "val": current_val},
            "items": items, 
            "count": len(items)
        })