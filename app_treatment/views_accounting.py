from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Sum, Count
from django.contrib.contenttypes.models import ContentType
from app_customer.models import Customer
from typing import Optional
from decimal import Decimal
from collections import defaultdict

from django.utils.dateparse import parse_date

from app_treatment.models import TreatmentRequest, TreatmentSession, ARItem, PaymentHistory, SessionTechicalSetting
from django.db.models.functions import Coalesce
from app_product.models import ServiceTreatmentPackage, TreatmentPackage

class RevenueListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start = request.query_params.get("startDate")
        end   = request.query_params.get("endDate")
        cid   = request.query_params.get("customer_id")
        pm    = request.query_params.get("paid_method")
        q     = (request.query_params.get("searchTerm") or "").strip()

        filters = Q()
        if start and end:
            filters &= Q(created__date__range=[start, end])
        if cid:
            filters &= Q(customer_id=cid)
        if pm:
            filters &= Q(paid_method=pm)
        if q:
            filters &= Q(customer__name__icontains=q) | Q(customer__mobile__icontains=q)

        qs = (PaymentHistory.objects
              .select_related("customer","ar_item")
              .filter(filters)
              .order_by("-created"))

        # map kiểu hóa đơn theo content_type của ARItem
        ct_map = {}
        def _invoice_type(ar):
            if not ar: return None
            ctid = ar.content_type_id
            if ctid not in ct_map:
                m = ContentType.objects.get_for_id(ctid).model.lower()
                ct_map[ctid] = {
                    "treatmentrequest": "Hóa đơn phác đồ",
                    "doctorprocess": "Hóa đơn thuốc",
                }.get(m, m.title())
            return ct_map[ctid]

        rows = [{
            "customer_id": p.customer_id,
            "customer_name": getattr(p.customer, "name", None),
            "mobile": getattr(p.customer, "mobile", None),
            "ar_item_id": p.ar_item_id,
            "invoice_type": _invoice_type(p.ar_item),
            "paid_method": p.paid_method,
            "paid_amount": p.paid_amount,
            "created": p.created,
        } for p in qs]

        total_rev = qs.aggregate(s=Sum("paid_amount"))["s"] or 0
        return Response({"results": rows, "summary": {"total_revenue": total_rev}})

class ARSummaryAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start = request.query_params.get("startDate")
        end   = request.query_params.get("endDate")
        q     = (request.query_params.get("searchTerm") or "").strip()

        if not (start and end):
            return Response({"detail":"startDate & endDate are required"}, status=400)

        cust_qs = Customer.objects.all()
        if q:
            cust_qs = cust_qs.filter(Q(name__icontains=q)|Q(mobile__icontains=q)|Q(code__icontains=q))

        cust_ids = list(cust_qs.values_list("id", flat=True)) or [-1]

        # trước kỳ
        ar_before = (ARItem.objects
                     .filter(customer_id__in=cust_ids, created__date__lt=start)
                     .values("customer_id").annotate(s=Sum("amount_original")))
        pay_before = (PaymentHistory.objects
                      .filter(customer_id__in=cust_ids, created__date__lt=start)
                      .values("customer_id").annotate(s=Sum("paid_amount")))

        # trong kỳ
        ar_period = (ARItem.objects
                     .filter(customer_id__in=cust_ids, created__date__range=[start,end])
                     .values("customer_id").annotate(s=Sum("amount_original")))
        pay_period = (PaymentHistory.objects
                      .filter(customer_id__in=cust_ids, created__date__range=[start,end])
                      .values("customer_id").annotate(s=Sum("paid_amount")))

        # map nhanh
        def m(qs): return {r["customer_id"]: r["s"] or 0 for r in qs}
        m_ar_b, m_pay_b = m(ar_before), m(pay_before)
        m_ar_p, m_pay_p = m(ar_period), m(pay_period)

        rows, sum_open, sum_deb, sum_cre, sum_end = [], 0,0,0,0
        for c in cust_qs:
            opening = (m_ar_b.get(c.id,0) - m_pay_b.get(c.id,0)) or 0
            period_debit  = m_ar_p.get(c.id,0) or 0
            period_credit = m_pay_p.get(c.id,0) or 0
            ending = opening + period_debit - period_credit

            rows.append({
                "customer_id": c.id,
                "customer_code": c.code,
                "customer_name": c.name,
                "opening_debit": opening,
                "period_debit": period_debit,
                "period_credit": period_credit,
                "ending_debit": ending,
            })
            sum_open += opening; sum_deb += period_debit; sum_cre += period_credit; sum_end += ending

        return Response({
            "results": rows,
            "summary": {
                "opening_debit": sum_open,
                "period_debit": sum_deb,
                "period_credit": sum_cre,
                "ending_debit": sum_end
            }
        })
        
class ARDetailByCustomerAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cid   = request.query_params.get("customer_id")
        start = request.query_params.get("startDate")
        end   = request.query_params.get("endDate")
        if not cid:
            return Response({"detail": "customer_id is required"}, status=400)

        # ----- 1) Lọc AR theo thời gian (đÂY là phát sinh NỢ) -----
        ar_filters = Q(customer_id=cid)
        if start and end:
            ar_filters &= Q(created__date__range=[start, end])
        elif start:
            ar_filters &= Q(created__date__gte=start)
        elif end:
            ar_filters &= Q(created__date__lte=end)

        ar_qs = (
            ARItem.objects
            .filter(ar_filters)
            .select_related("content_type")
            .only("id", "created", "amount_original", "description", "content_type")
            .order_by("created", "id")
        )

        # ----- 2) Lọc payments theo thời gian (đÂY là phát sinh CÓ) -----
        pmt_filters = Q(ar_item_id__in=ar_qs.values("id"))
        if start and end:
            pmt_filters &= Q(created__date__range=[start, end])
        elif start:
            pmt_filters &= Q(created__date__gte=start)
        elif end:
            pmt_filters &= Q(created__date__lte=end)

        # Lấy thêm model của AR để mô tả loại chứng từ ở dòng thu
        pmt_qs = (
            PaymentHistory.objects
            .filter(pmt_filters)
            .select_related("ar_item__content_type")
            .values(
                "id",
                "ar_item_id",
                "paid_amount",
                "paid_method",           # 'cash' | 'transfer'
                "created",
                "ar_item__content_type__model",
            )
        )

        # ----- 3) Helper map loại chứng từ -----
        def label_from_model(model: Optional[str]) -> str:
            if model == "doctorprocess":
                return "Đơn thuốc"
            if model == "treatmentrequest":
                return "Phác đồ"
            if model in ("materialissue", "warehouseissue", "issuematerial", "stockout"):
                return "Xuất vật tư"
            return "Khác"

        def method_label(m: Optional[str]) -> str:
            if m == "cash":
                return "Tiền mặt"
            if m == "transfer":
                return "Chuyển khoản"
            return m or ""

        # ----- 4) Gom timeline: AR = debit, Payment = credit -----
        timeline = []
        for ar in ar_qs:
            model = getattr(getattr(ar, "content_type", None), "model", None)
            # Diễn giải AR ưu tiên description có sẵn, fallback theo loại
            ar_desc = ar.description or label_from_model(model) or "Phát sinh công nợ"
            timeline.append({
                "date": ar.created,
                "type_order": 0,            # AR trước payment cùng thời điểm
                "id": ar.id,
                "description": ar_desc,
                "debit": float(ar.amount_original or 0),
                "credit": 0.0,
            })

        for p in pmt_qs:
            model = p.get("ar_item__content_type__model")
            kind  = label_from_model(model)
            mth   = method_label(p.get("paid_method"))
            desc  = f"Thu tiền {kind} (AR #{p['ar_item_id']})"
            # Optional: thêm phương thức trong ngoặc
            if mth:
                desc += f" - {mth}"
            timeline.append({
                "date": p["created"],
                "type_order": 1,
                "id": p["id"],
                "description": desc,
                "debit": 0.0,
                "credit": float(p["paid_amount"] or 0),
            })

        # ----- 5) Sort theo (date, type_order, id) -----
        timeline.sort(key=lambda x: (x["date"] or "", x["type_order"], x["id"]))

        # ----- 6) Tính running balance + tổng trong kỳ -----
        entries = []
        total_debit = 0.0
        total_credit = 0.0
        balance = 0.0  # >0: dư nợ; <0: dư có

        for ev in timeline:
            d = float(ev["debit"] or 0)
            c = float(ev["credit"] or 0)
            total_debit += d
            total_credit += c
            balance += (d - c)

            entries.append({
                "date": ev["date"],
                "description": ev["description"],
                "debit": d,
                "credit": c,
                "balance_debit": balance if balance > 0 else 0.0,
                "balance_credit": (-balance) if balance < 0 else 0.0,
            })

        return Response({
            "customer_id": int(cid),
            "entries": entries,
            "summary": {
                "total_debit": total_debit,        # ✅ tổng Nợ trong kỳ (theo filter)
                "total_credit": total_credit,      # ✅ tổng Có trong kỳ (theo filter)
                "ending_debit": balance if balance > 0 else 0.0,
                "ending_credit": (-balance) if balance < 0 else 0.0,
            }
        })
        
class UnrealizedRevenueAPI(APIView):
    permission_classes = [IsAuthenticated]

    # =========================
    # Helpers
    # =========================
    def _get_treatment_package_prices(self, tr_queryset):
        """
        Tính giá trị gói (price) và số buổi (sessions) cho từng TreatmentRequest.
        - Giá lấy từ ServiceTreatmentPackage theo (service_id, treatment_package_id).
        - KHÔNG còn truy vấn 'service__price' (field này không tồn tại trên Service).
        - Nếu không có STP -> price = 0.
        """
        # Preload bảng STP cho các (service_id, treatment_package_id) cần dùng
        stp_map = {}
        stp_qs = ServiceTreatmentPackage.objects.filter(
            service_id__in=tr_queryset.values_list('service_id', flat=True),
            treatment_package_id__in=tr_queryset.values_list('treatment_package_id', flat=True)
        ).values('service_id', 'treatment_package_id', 'price')

        for stp in stp_qs:
            stp_map[(stp['service_id'], stp['treatment_package_id'])] = stp['price']

        # Lấy dữ liệu cần thiết từ TR — CHỈ lấy field có thật
        # (bỏ 'service__price' để tránh FieldError)
        tr_data = tr_queryset.select_related('service', 'treatment_package').values(
            'id',
            'service_id',
            'treatment_package_id',
            'treatment_package__value',  # số buổi
        )

        result = {}
        for tr in tr_data:
            tr_id = tr['id']
            service_id = tr['service_id']
            package_id = tr['treatment_package_id']

            # Số buổi từ gói
            total_sessions = int(tr.get('treatment_package__value') or 0)

            # Giá từ ServiceTreatmentPackage (nếu có)
            total_price = Decimal('0')
            if service_id and package_id:
                price_val = stp_map.get((service_id, package_id))
                if price_val is not None:
                    # price_val có thể là Decimal/float/int; ép về Decimal chuẩn
                    total_price = Decimal(str(price_val))

            # Nếu treatment_package trống nhưng model có selected_package_id (fallback hiếm)
            # → dùng value của TreatmentPackage + tìm STP theo selected_package_id
            if (not package_id) and hasattr(tr_queryset.model, 'selected_package_id'):
                # Trường hợp này chỉ hữu dụng nếu instance có selected_package_id thực tế.
                # Ta sẽ xử lý ở vòng for instance trong .get() để có access instance attribute.
                pass

            result[tr_id] = {
                'price': total_price,
                'sessions': total_sessions
            }

        return result

    def _get_used_sessions_count(self, tr_ids):
        """
        Số buổi đã phát sinh = số buổi có ÍT NHẤT 1 kỹ thuật has_come=True
        (đếm DISTINCT session_id theo từng TreatmentRequest).
        """
        return dict(
            SessionTechicalSetting.objects
            .filter(session__treatment_request_id__in=tr_ids, has_come=True)
            .values('session__treatment_request_id')
            .annotate(cnt=Count('session_id', distinct=True))
            .values_list('session__treatment_request_id', 'cnt')
        )
        
    def _get_payment_amounts(self, tr_ids):
        """
        Tổng tiền đã thanh toán cho từng TreatmentRequest
        (thông qua ARItem có content_type = TreatmentRequest).
        """
        ct_tr = ContentType.objects.get_for_model(TreatmentRequest)
        return dict(
            PaymentHistory.objects
            .filter(ar_item__content_type=ct_tr, ar_item__object_id__in=tr_ids)
            .values('ar_item__object_id')
            .annotate(total_paid=Coalesce(Sum('paid_amount'), Decimal('0')))
            .values_list('ar_item__object_id', 'total_paid')
        )

    def _calculate_used_amount(self, package_price: Decimal, total_sessions: int, used_sessions: int) -> Decimal:
        """
        Tiền đã sử dụng = (giá gói / tổng buổi) * số buổi đã thực hiện.
        """
        if not package_price or not total_sessions:
            return Decimal('0')
        # Dùng Decimal để tránh sai số
        unit = package_price / Decimal(str(total_sessions))
        return unit * Decimal(str(used_sessions))

    # =========================
    # GET
    # =========================
    def get(self, request):
        # Parse params
        start = request.query_params.get("startDate")
        end = request.query_params.get("endDate")
        search_term = (request.query_params.get("searchTerm") or "").strip()

        # Build filters (TR dùng created_at)
        filters = Q()
        if start:
            d = parse_date(start)
            if d:
                filters &= Q(created_at__date__gte=d)
        if end:
            d = parse_date(end)
            if d:
                filters &= Q(created_at__date__lte=d)
        if search_term:
            filters &= (
                Q(customer__name__icontains=search_term) |
                Q(customer__code__icontains=search_term) |
                Q(customer__mobile__icontains=search_term)
            )

        # Query TR
        tr_queryset = (
            TreatmentRequest.objects
            .select_related("customer", "service", "treatment_package")
            .filter(filters)
            .order_by('customer_id', 'id')
        )

        if not tr_queryset.exists():
            return Response({
                "results": [],
                "summary": {
                    "total_package_price": Decimal('0'),
                    "total_paid": Decimal('0'),
                    "used_amount": Decimal('0'),
                    "unused_amount": Decimal('0'),
                }
            })

        tr_ids = list(tr_queryset.values_list("id", flat=True))

        # Tính price & sessions (theo STP map), và used_sessions, paid amounts
        package_info_map = self._get_treatment_package_prices(tr_queryset)
        used_sessions_map = self._get_used_sessions_count(tr_ids)
        payment_amounts = self._get_payment_amounts(tr_ids)

        # Gom theo khách hàng
        customer_data = defaultdict(lambda: {
            "customer_id": None,
            "customer_code": None,
            "customer_name": None,
            "mobile": None,
            "total_sessions": 0,
            "used_sessions": 0,
            "total_package_price": Decimal('0'),
            "total_paid": Decimal('0'),
            "used_amount": Decimal('0'),
        })

        # Tổng cộng
        summary_totals = {
            "total_package_price": Decimal('0'),
            "total_paid": Decimal('0'),
            "used_amount": Decimal('0'),
        }

        # Duyệt từng TR instance để xử lý fallback selected_package_id (nếu có)
        for tr in tr_queryset:
            tr_id = tr.id
            cid = tr.customer_id
            cust = tr.customer

            # Info mặc định từ map
            info = package_info_map.get(tr_id, {'price': Decimal('0'), 'sessions': 0})
            package_price = Decimal(info['price'] or 0)
            package_sessions = int(info['sessions'] or 0)

            # Fallback hiếm: nếu model có selected_package_id và chưa có sessions/price từ map
            # Lúc này access trực tiếp attribute từ instance.
            if package_sessions == 0 and getattr(tr, "selected_package_id", None):
                # Lấy số buổi (value) từ TreatmentPackage
                pkg_val = TreatmentPackage.objects.filter(
                    id=tr.selected_package_id
                ).values_list('value', flat=True).first()
                package_sessions = int(pkg_val or 0)

                # Lấy giá từ STP theo selected_package_id (nếu có Service)
                if tr.service_id:
                    stp_price = ServiceTreatmentPackage.objects.filter(
                        service_id=tr.service_id,
                        treatment_package_id=tr.selected_package_id
                    ).values_list('price', flat=True).first()
                    if stp_price is not None:
                        package_price = Decimal(str(stp_price))

            # Số buổi đã dùng theo nghiệp vụ cũ
            used_sessions = int(used_sessions_map.get(tr_id, 0))

            # Tổng đã thanh toán của TR
            paid_amount = Decimal(payment_amounts.get(tr_id, Decimal('0')) or 0)

            # Tiền đã sử dụng
            used_amount = self._calculate_used_amount(package_price, package_sessions, used_sessions)

            # Khởi tạo block khách hàng nếu lần đầu
            if customer_data[cid]["customer_id"] is None:
                customer_data[cid].update({
                    "customer_id": cid,
                    "customer_code": getattr(cust, "code", None),
                    "customer_name": getattr(cust, "name", None),
                    "mobile": getattr(cust, "mobile", None),
                })

            # Cộng dồn theo khách hàng
            customer_data[cid]["total_sessions"] += package_sessions
            customer_data[cid]["used_sessions"] += used_sessions
            customer_data[cid]["total_package_price"] += package_price
            customer_data[cid]["total_paid"] += paid_amount
            customer_data[cid]["used_amount"] += used_amount

            # Cộng dồn summary
            summary_totals["total_package_price"] += package_price
            summary_totals["total_paid"] += paid_amount
            summary_totals["used_amount"] += used_amount

        # Build results
        results = []
        for c in customer_data.values():
            unused_amount = c["total_paid"] - c["used_amount"]
            if unused_amount < 0:
                unused_amount = Decimal('0')

            results.append({
                **c,
                "usage_status": f'{c["used_sessions"]}/{c["total_sessions"]}',
                "unused_amount": unused_amount
            })

        # Sort theo tên KH
        results.sort(key=lambda x: (x["customer_name"] or "").lower())

        # Summary: unused
        summary_unused = summary_totals["total_paid"] - summary_totals["used_amount"]
        if summary_unused < 0:
            summary_unused = Decimal('0')

        return Response({
            "results": results,
            "summary": {
                "total_package_price": summary_totals["total_package_price"],
                "total_paid": summary_totals["total_paid"],
                "used_amount": summary_totals["used_amount"],
                "unused_amount": summary_unused,
            }
        })