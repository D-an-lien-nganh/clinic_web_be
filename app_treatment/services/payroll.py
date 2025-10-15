from typing import Optional, Dict
from decimal import Decimal
from django.apps import apps
from django.db.models import Q, Count, Sum, Value, DecimalField
from django.db.models.functions import Coalesce

DEC = DecimalField(max_digits=18, decimal_places=2)

def get_performance_payroll(
    start_date,
    end_date,
    *,
    user_type: Optional[str] = None,  # 'employee' / 'collaborator'
    department_id: Optional[int] = None,
    search: Optional[str] = None,  # New search parameter
):
    """
    Tính lương theo hiệu suất dựa trên số lượt thực hiện kỹ thuật.
    
    Logic:
    - Mỗi SessionTechicalSetting với has_come=True = 1 lượt thực hiện kỹ thuật
    - Nhóm theo expert (HrUserProfile) và loại kỹ thuật (TLCB/TLDS)
    - Tính tổng tiền = sum(techical_setting.price) của các kỹ thuật đã thực hiện
    - Lương = coefficient * tổng tiền
    """
    
    Hr = apps.get_model('app_hr', 'HrUserProfile')
    Pos = apps.get_model('app_home', 'Position')
    STS = apps.get_model('app_treatment', 'SessionTechicalSetting')
    
    # ---- 1) Base HR queryset: chỉ employee
    hq = Hr.objects.select_related('position').filter(type="employee")
    if user_type:
        hq = hq.filter(type=user_type)
    if department_id:
        hq = hq.filter(position__department_id=department_id)
    
    # ---- Add search functionality ----
    if search:
        search_query = (
            Q(full_name__icontains=search) |
            Q(code__icontains=search) |
            Q(email__icontains=search)
        )
        hq = hq.filter(search_query)
    
    # ---- 2) Thời gian filter - sửa tên field
    time_q = (
        Q(session__booking__receiving_day__gte=start_date, 
          session__booking__receiving_day__lte=end_date) |
        Q(session__treatment_request__created_at__date__gte=start_date, 
          session__treatment_request__created_at__date__lte=end_date)
    )
    
    # ---- 3) Query SessionTechicalSetting với các điều kiện
    base_sts = (STS.objects
                .select_related('techical_setting', 'expert')
                .filter(
                    has_come=True,  # Chỉ tính kỹ thuật đã thực hiện
                    expert__isnull=False,  # Phải có expert
                    expert__type='employee'  # Chỉ tính cho employee
                )
                .filter(time_q))
    
    # ---- Filter STS by search if provided ----
    if search:
        base_sts = base_sts.filter(
            Q(expert__full_name__icontains=search) |
            Q(expert__code__icontains=search) |
            Q(expert__email__icontains=search)
        )
    
    # ---- 4) Nhóm theo expert và tính thống kê
    grouped = (
        base_sts.values('expert_id')
        .annotate(
            # Đếm số lượt theo loại kỹ thuật
            count_tlcb=Count('id', filter=Q(techical_setting__type='TLCB')),
            count_tlds=Count('id', filter=Q(techical_setting__type='TLDS')),
            
            # Tổng tiền từ giá kỹ thuật đã thực hiện
            amount=Coalesce(
                Sum('techical_setting__price', output_field=DEC),
                Value(0, output_field=DEC)
            ),
            
            # Tổng số lượt thực hiện (tất cả loại)
            total_count=Count('id'),
        )
    )
    
    # ---- 5) Tạo map thống kê theo HR ID
    stats_map: Dict[int, Dict] = {}
    for row in grouped:
        hr_id = row['expert_id']
        if hr_id is None:
            continue
            
        stats_map[hr_id] = {
            'count_tlcb': row['count_tlcb'] or 0,
            'count_tlds': row['count_tlds'] or 0,
            'total_count': row['total_count'] or 0,
            'amount': row['amount'] or Decimal('0'),
        }
    
    # ---- 6) Tạo kết quả cuối cùng
    out = []
    for hr in hq:
        pos = hr.position
        coeff = float(pos.performance_coefficient) if pos and pos.performance_coefficient else 1.0
        
        # Lấy thống kê cho HR này, mặc định = 0 nếu không có
        s = stats_map.get(hr.id, {
            'count_tlcb': 0, 
            'count_tlds': 0, 
            'total_count': 0,
            'amount': Decimal('0')
        })
        
        # Tính lương = hệ số * tổng tiền kỹ thuật
        salary = (Decimal(str(coeff)) * (s['amount'] or Decimal('0'))).quantize(Decimal('0.01'))
        
        out.append({
            "hr_id": hr.id,
            "employee_code": hr.code,
            "full_name": hr.full_name,
            "position": pos.title if pos else None,
            "contract": hr.get_contract_type_display() if hr.contract_type else None,
            "coefficient": coeff,
            "count_tlcb": s['count_tlcb'],
            "count_tlds": s['count_tlds'],
            "total_count": s['total_count'],
            "total_amount": str(s['amount']),
            "salary": str(salary),
        })
    
    # ---- Sort results by name for better UX ----
    out.sort(key=lambda x: (x['full_name'] or '').lower())
    
    return out


def get_expert_technique_detail(expert_id: int, start_date, end_date, technique_type: Optional[str] = None):
    """
    Chi tiết kỹ thuật thực hiện của một expert trong khoảng thời gian.
    
    Returns:
    - Danh sách các buổi với kỹ thuật đã thực hiện
    - Nhóm theo khách hàng và ngày
    """
    STS = apps.get_model('app_treatment', 'SessionTechicalSetting')
    
    time_q = (
        Q(session__booking__receiving_day__gte=start_date, 
          session__booking__receiving_day__lte=end_date) |
        Q(session__treatment_request__created_at__date__gte=start_date, 
          session__treatment_request__created_at__date__lte=end_date)
    )
    
    base = (STS.objects
            .select_related(
                'session__booking__customer',
                'session__treatment_request__customer', 
                'techical_setting',
                'expert'
            )
            .filter(
                has_come=True,
                expert_id=expert_id,
            )
            .filter(time_q))
    
    if technique_type in ("TLCB", "TLDS"):
        base = base.filter(techical_setting__type=technique_type)
    
    # Group by customer, date, technique
    rows = (
        base.values(
            'session__booking__customer_id',
            'session__booking__customer__name',
            'session__booking__customer__code',
            'session__booking__receiving_day',
            'session__treatment_request__created_at__date',
            'techical_setting__id',
            'techical_setting__name',
            'techical_setting__type',
            'techical_setting__price',
        )
        .annotate(
            execution_count=Count('id')  # Số lần thực hiện kỹ thuật này trong ngày
        )
        .order_by(
            'session__booking__customer__name',
            '-session__booking__receiving_day',
            'techical_setting__name'
        )
    )
    
    return list(rows)