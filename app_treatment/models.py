
from decimal import Decimal
from django.apps import apps
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q, Count, F
from django.core.exceptions import ValidationError
from django.db.models.functions import Coalesce
from django.db.models import Sum, Value, DecimalField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from typing import Optional, List, Dict, Tuple

from app_customer.models import Customer
from app_home.models import Department, Discount, Floor, TestService, TimeFrame, TreatmentPackage, Unit, generate_random_code
from app_product.models import Product, Service, ServiceTreatmentPackage, TechicalSetting
from django.db import transaction

from django.conf import settings

from django.utils.crypto import get_random_string

def unique_code(model, prefix: str, field: str = "code", length: int = 8) -> str:
    """
    Sinh mã duy nhất cho model theo field 'code'.
    Ví dụ: unique_code(Bill, "BILL_") -> "BILL_AB12CD34"
    """
    while True:
        code = f"{prefix}{get_random_string(length).upper()}"
        if not model.objects.filter(**{field: code}).exists():
            return code

class Booking(models.Model):
    BOOKING_TYPE = [
        ("examination", 'Khám'),
        ("treatment_cure", "Trị liệu chữa bệnh"),
        ("treatment_relax", "Trị liệu dưỡng sinh"),
        ("re_examination", 'Tái khám'),
    ]

    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=BOOKING_TYPE, default='examination') #khong trueyn
    note = models.TextField(null=True, blank=True)

    has_come = models.BooleanField(default=False) #khong trueyn
    is_treatment = models.BooleanField(blank=False, default=False) #khong trueyn

    receiving_day = models.DateField(null=True, blank=True, verbose_name="Ngày tiếp nhận")
    #use when customer want to set a date to come
    set_date = models.TimeField(null=True, blank=True, verbose_name="Giờ hẹn đến")
    def __str__(self):
        return f"Booking for {self.customer.name}"
    class Meta:
        app_label = "app_treatment" 

class ExaminationOrder(models.Model):

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    doctor_profile = models.ForeignKey('app_hr.HrUserProfile', on_delete=models.SET_NULL, null=True, blank=True)
    diagnosis = models.TextField(null=True, blank=True, verbose_name="Chuẩn đoán")
    note = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)  
    # tiện truy vấn tổng tiền
    class Meta:
        app_label = "app_treatment"
        verbose_name = "Đơn khám"
        verbose_name_plural = "Đơn khám"
    def __str__(self):
        return f"Đơn khám #{self.id} - Customer {self.customer_id}"


class ExaminationOrderItem(models.Model):
    """
    Mỗi dòng test trong đơn khám (nhiều-1 tới đơn khám).
    """
    order = models.ForeignKey(
        ExaminationOrder, on_delete=models.CASCADE, related_name="items"
    )
    test_service = models.ForeignKey(
        TestService, on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.PositiveIntegerField(default=1)

    note = models.TextField(null=True, blank=True)
    test_result = models.TextField(null=True, blank=True)
    class Meta:
        app_label = "app_treatment"
        unique_together = ("order", "test_service")  # tránh trùng service trong cùng 1 đơn

    def __str__(self):
        return f"{self.test_service.name} (Order {self.order_id})"
class DoctorHealthCheck(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name="doctor_health_check",null=True, blank=True)
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)

    nearest_examination = models.TextField(null=True, blank=True)
    blood_presure = models.CharField(max_length=20, null=True, blank=True)
    heart_beat = models.CharField(max_length=20, null=True, blank=True)
    height = models.PositiveSmallIntegerField(null=True, blank=True)
    weight = models.PositiveSmallIntegerField(null=True, blank=True)
    breathing_beat = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        app_label = "app_treatment"
        verbose_name = "Bác sĩ khám sức khỏe"
        verbose_name_plural = "Bác sĩ khám sức khỏe"

class ClinicalExamination(models.Model):
    doctor_health_check_process = models.OneToOneField(DoctorHealthCheck, on_delete=models.CASCADE, related_name="clinical_examination")
    floor = models.ForeignKey(Floor, on_delete=models.SET_NULL, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True)

    medical_history = models.TextField(null=True, blank=True)
    diagnosis = models.TextField(null=True, blank=True)
    present_symptom = models.TextField(null=True, blank=True)
    treatment_method = models.TextField(null=True, blank=True)
    def __str__(self):
        return f"Clinical Examination for {self.doctor_health_check_process.customer.name}"

    class Meta:
        app_label = "app_treatment"
    

class DoctorProcess(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE,
        related_name="doctor_process", null=True, blank=True
    )
    doctor_profile = models.ForeignKey('app_hr.HrUserProfile', on_delete=models.SET_NULL, null=True, blank=True)

    # 🔗 Quan hệ cha–con (versioning)
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT,
        null=True, blank=True, related_name="children",
        help_text="Bản gốc mà bản này được tạo ra từ."
    )
    version = models.PositiveIntegerField(default=1, help_text="Số version trong phạm vi 1 khách hàng.")
    is_active = models.BooleanField(default=True, help_text="Bản hiện hành dùng để tính tiền & hiển thị.")
    replace_reason = models.CharField(max_length=255, null=True, blank=True)

    # đơn kê thuốc
    products = models.ManyToManyField(Product, blank=True, through="diagnosis_medicine")
    medicine_discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, blank=True, null=True)
    medicines_has_paid = models.BooleanField(default=False)

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # tiện audit
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        app_label = "app_treatment"
        indexes = [
            models.Index(fields=["customer", "is_active"]),
            models.Index(fields=["customer", "version"]),
        ]
        constraints = [
            # Tuỳ bạn: đảm bảo mỗi (customer) chỉ có 1 process active.
            models.UniqueConstraint(
                fields=["customer"],
                condition=models.Q(is_active=True),
                name="uniq_active_process_per_customer",
                violation_error_message="Mỗi khách hàng chỉ có 1 DoctorProcess đang hiệu lực."
            )
        ]

    def total_product_amount_after_discount(self) -> Decimal:
        """
        Tổng tiền đơn thuốc = Σ(price * quantity) của các dòng thuốc
        rồi trừ chiết khấu (nếu bạn có field chiết khấu ở DoctorProcess).
        """
        total = (
            self.diagnosis_medicines.aggregate(  # đổi theo related_name của bạn
                s=Coalesce(
                    Sum(F('price') * F('quantity'),
                        output_field=DecimalField(max_digits=18, decimal_places=2)),
                    Value(0, output_field=DecimalField(max_digits=18, decimal_places=2))
                )
            )['s'] or Decimal('0.00')
        )

        # (Tuỳ chọn) Nếu bạn có chiết khấu cấp đơn thuốc, ví dụ:
        disc_type = getattr(self, 'medicine_discount_type', None)   # 'percent' | 'amount' | None
        disc_value = getattr(self, 'medicine_discount_value', None) # số Decimal/float
        if disc_type and disc_value:
            disc_value = Decimal(str(disc_value))
            if disc_type == 'percent':
                total = total * (Decimal('100') - disc_value) / Decimal('100')
            elif disc_type == 'amount':
                total = max(Decimal('0.00'), total - disc_value)

        return total
    
    def __str__(self):
        return f"DP#{self.id} C{getattr(self.customer,'id',None)} v{self.version} ({'active' if self.is_active else 'archived'})"

    # ====== Tổng tiền thuốc của *bản này*
    def total_amount(self):
        total = sum(
            (dm.price or 0) * (dm.quantity or 0)
            for dm in self.diagnosis_medicines.all()
        )
        return total

    def total_after_discount(self):
        total = self.total_amount()
        d = getattr(self, "medicine_discount", None)
        if d:
            if d.type in ("percentage", "percent"):
                total = total - (total * d.rate) / 100
            elif d.type in ("fixed", "amount"):  # 👈 chấp nhận cả 'amount'
                total = total - d.rate
        return max(total, 0)

    # ====== Helper: clone/fork một process mới từ process hiện tại
    @transaction.atomic
    def fork(self, *, replace_reason: Optional[str] = None) -> "DoctorProcess":
        """
        Tạo 1 DoctorProcess mới từ bản hiện tại:
        - set parent = self
        - tăng version
        - copy toàn bộ diagnosis_medicines (và các field chính)
        - deactivate bản cũ (is_active=False), bản mới active=True
        """
        # Tính version mới trong phạm vi customer
        last_version = (DoctorProcess.objects
                        .filter(customer=self.customer)
                        .order_by("-version")
                        .values_list("version", flat=True)
                        .first() or 0)
        new_dp = DoctorProcess.objects.create(
            customer=self.customer,
            parent=self,
            version=last_version + 1,
            is_active=True,
            replace_reason=replace_reason,
            medicine_discount=self.medicine_discount,
            medicines_has_paid=False,    # bản mới chưa thanh toán
            start_time=timezone.now(),   # tuỳ ý: coi như bắt đầu mới
            end_time=None,
        )

        # Copy các dòng thuốc
        bulk_items = []
        for dm in self.diagnosis_medicines.all():
            bulk_items.append(diagnosis_medicine(
                doctor_process=new_dp,
                product=dm.product,
                quantity=dm.quantity,
                unit=dm.unit,
                dose=dm.dose,
                note=dm.note,
                price=dm.price,  # copy giá đang dùng
            ))
        diagnosis_medicine.objects.bulk_create(bulk_items)

        # Vô hiệu hoá bản cũ
        if self.is_active:
            self.is_active = False
            self.end_time = timezone.now()
            self.save(update_fields=["is_active", "end_time", "updated_at"])

        return new_dp

    # ====== Manager tiện dụng
    @classmethod
    def active_for_customer(cls, customer: Customer):
        return cls.objects.filter(customer=customer, is_active=True).order_by("-version").first()

#use only for service path
class diagnosis_medicine(models.Model):
    doctor_process = models.ForeignKey(DoctorProcess, on_delete=models.CASCADE, related_name="diagnosis_medicines")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)

    quantity = models.PositiveSmallIntegerField(default=1)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    dose = models.CharField(max_length=255, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=25, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.product:
            if not self.unit:
                self.unit = self.product.unit
            if self.price is None:
                self.price = self.product.sell_price
        super().save(*args, **kwargs)

    class Meta:
        app_label = "app_treatment" 

class ServiceAssign(models.Model):
    doctor_process = models.ForeignKey(DoctorProcess, on_delete=models.CASCADE, related_name="service_assign", null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    assigned_expert = models.ForeignKey(User, on_delete=models.CASCADE)
    treatment_method = models.TextField(null=True, blank=True)
    #for purchase service
    services = models.ManyToManyField(Service, blank=True, through="diagnosis_service")
    service_discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, blank=True, null=True)
    services_has_paid = models.BooleanField(default=False)

    def total_amount(self):

        total = Decimal(0)
        for diagnosis in self.diagnosis_services.all():
            service = diagnosis.service
            treatment_package = getattr(diagnosis, "treatment_package", None)

            if service:
                if treatment_package:
                    # Lấy giá theo gói liệu trình
                    try:
                        stp = ServiceTreatmentPackage.objects.get(
                            service=service, treatment_package=treatment_package
                        )
                        total += stp.price * diagnosis.quantity
                    except ServiceTreatmentPackage.DoesNotExist:
                        total += service.price * diagnosis.quantity  # fallback
                else:
                    total += service.price * diagnosis.quantity
        return total

        
    def total_after_discount(self):
        total = self.total_amount()
        if self.service_discount:
            if self.service_discount.type == 'percentage':
                discount_value = (total * self.service_discount.rate) / 100
                return total - discount_value
            elif self.service_discount.type == 'fixed':
                return total - self.service_discount.rate
        return total

    
    class Meta:
        app_label = "app_treatment" 

#use only for service path
class diagnosis_service(models.Model):
    service_assign = models.ForeignKey(ServiceAssign, on_delete=models.CASCADE, related_name="diagnosis_services")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    treatment_package = models.ForeignKey(TreatmentPackage, on_delete=models.SET_NULL, null=True, blank=True)

    quantity = models.PositiveSmallIntegerField(default=1)

    class Meta:
        app_label = "app_treatment" 

from decimal import Decimal

class Bill(models.Model):
    PAID_METHOD = [
        ('cash', 'Tiền mặt'),
        ('transfer', 'Chuyển khoản'),
    ]
    code = models.CharField(max_length=255, unique=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # 🔁 ĐÃ SỬA: liên kết trực tiếp tới Customer
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="bills", null=True, blank=True)

    method = models.CharField(max_length=25, choices=PAID_METHOD, default="cash")
    paid_ammount = models.DecimalField(max_digits=25, decimal_places=2, default=Decimal(0))
    note = models.TextField(null=True, blank=True)

    # ⚠️ Tùy quan niệm: fully_paid theo bill riêng hay theo toàn khách hàng?
    # Ở dưới mình sẽ set theo "toàn khách hàng" như mô tả của bạn.
    fully_paid = models.BooleanField(default=False)

    class Meta:
        app_label = "app_treatment"
    def _ensure_customer(self):
        if not self.customer_id:
            return False
        return True

    # ==============================
    # A. TÍNH THEO BILL HIỆN TẠI (giữ nguyên logic cũ)
    # ==============================
    def _get_active_doctor_process(self):
        try:
            return DoctorProcess.active_for_customer(self.customer)
        except Exception:
            return None

    def _get_service_assigns(self):
        """
        Chỉ lấy các chỉ định dịch vụ từ DoctorProcess đang hiệu lực.
        """
        dp = self._get_active_doctor_process()
        return list(dp.service_assign.all()) if dp else []

    def get_total_product_amount(self) -> Decimal:
        """
        Tổng tiền thuốc/sản phẩm chỉ theo DoctorProcess đang hiệu lực.
        """
        dp = self._get_active_doctor_process()
        return dp.total_after_discount() if dp else Decimal(0)

    def get_total_service_amount(self) -> Decimal:
        """
        Tổng tiền *dịch vụ* của Bill = tổng giá *phác đồ* gắn với Bill,
        trong đó giá của mỗi phác đồ = package_price() (ưu tiên ServiceTreatmentPackage).
        KHÔNG cộng tiền kỹ thuật (techical_setting) – chỉ dùng cho payroll.
        """
        total = Decimal(0)
        # Dùng related_name="treatment_requests" từ FK ở TreatmentRequest
        for tr in self.treatment_requests.all():
            total += tr.package_price()
        return total

    def get_doctor(self):
        """
        Nếu bạn muốn show bác sĩ gắn với process hiện hành:
        - Nếu lưu ở DoctorHealthCheck: return self.customer.doctor_health_check.doctor
        - Nếu bạn có field bác sĩ ngay trên DoctorProcess, lấy từ dp active.
        """
        # Ví dụ lấy theo DoctorHealthCheck:
        try:
            return self.customer.doctor_health_check.doctor
        except Exception:
            pass

        # Hoặc nếu có field trên DoctorProcess:
        dp = self._get_active_doctor_process()
        return getattr(dp, "assigned_doctor", None) if dp else None

    def get_total_service_amount(self) -> Decimal:
        total = Decimal(0)
        for assign in self._get_service_assigns():
            total += assign.total_after_discount()
        return total


    def get_total_amount(self) -> Decimal:
        """
        Tổng tiền của BILL HIỆN TẠI (dịch vụ + sản phẩm).
        """
        return self.get_total_service_amount() + self.get_total_product_amount()

    def get_total_amount_real(self) -> Decimal:
        return self.get_total_amount()

    def bill_amount_remaining(self) -> Decimal:
        """
        Số tiền còn lại của RIÊNG bill này = total (bill) - paid_ammount (của bill).
        (Giữ lại nếu bạn vẫn muốn theo dõi ở cấp bill).
        """
        remaining = self.get_total_amount_real() - self.paid_ammount
        return remaining if remaining > 0 else Decimal(0)

    # ==============================
    # B. TÍNH THEO TOÀN BỘ KHÁCH HÀNG (theo yêu cầu mới)
    # ==============================
    def get_customer_total_billed(self) -> Decimal:
        """
        Tổng số tiền đã xuất hóa đơn cho KHÁCH HÀNG = sum(total của TẤT CẢ bill của khách hàng).
        Vì total là hàm Python (không lưu trong DB), ta cộng bằng Python.
        """
        total = Decimal(0)
        # Tránh N+1 ở phần doctor_process nếu cần, nhưng ở đây khó prefetch vì total là hàm tuỳ logic.
        for b in Bill.objects.filter(customer=self.customer).iterator():
            total += b.get_total_amount_real()
        return total

    def get_customer_total_paid(self) -> Decimal:
        """
        Tổng số tiền KHÁCH HÀNG đã thanh toán = sum(paid_ammount của tất cả bill).
        """
        agg = Bill.objects.filter(customer=self.customer).aggregate(s=Sum('paid_ammount'))
        return agg['s'] or Decimal(0)

    def amount_remaining(self) -> Decimal:
        """
        ⚠️ ĐÃ SỬA: Trả về "số tiền CÒN NỢ của KHÁCH HÀNG" (không phải riêng bill này).
        = Tổng tiền tất cả hóa đơn - Tổng đã thanh toán tất cả hóa đơn.
        Ví dụ của bạn: 1.000.000 - 200.000 = 800.000.
        """
        remaining = self.get_customer_total_billed() - self.get_customer_total_paid()
        return remaining if remaining > 0 else Decimal(0)

    def get_product_fee_remaining(self) -> Decimal:
        """
        (Tuỳ bạn có còn cần các hàm 'remaining' tách riêng không)
        Ở cấp 'khách hàng', nếu vẫn muốn giữ API cũ:
        - Có thể để = tổng product fee của bill hiện tại (như cũ)
        - Hoặc sửa thành tổng product fee (mọi bill). Ở đây mình giữ theo BILL hiện tại.
        """
        return self.get_total_product_amount()

    def get_service_fee_remaining(self) -> Decimal:
        # Giữ theo BILL hiện tại (như cũ). Nếu muốn chuyển sang tổng-cho-khách, cần có cách tính product/service tách rời ở nhiều bill.
        return self.get_total_service_amount()

    # ==============================
    # C. NHÂN SỰ
    # ==============================
    # ==============================
    # D. LIFE CYCLE
    # ==============================
    # --- LIÊN QUAN ĐẾN SESSION ---
    def get_treatment_sessions_remaining(self) -> int:
        """
        Số buổi trị liệu CHƯA hoàn thành của tất cả TreatmentRequest thuộc bill này.
        """
        return TreatmentSession.objects.filter(
            treatment_request__bill=self,
            is_done=False
        ).count()

    def get_treatment_sessions_done(self) -> int:
        """
        Số buổi trị liệu ĐÃ hoàn thành của tất cả TreatmentRequest thuộc bill này.
        """
        return TreatmentSession.objects.filter(
            treatment_request__bill=self,
            is_done=True
        ).count()

    def get_uncompleted_sessions_for_tlcb_service(self) -> int:
        """
        Số buổi CHƯA hoàn thành cho các phác đồ có service.type = 'TLCB'.
        """
        return TreatmentSession.objects.filter(
            treatment_request__bill=self,
            treatment_request__service__type='TLCB',
            is_done=False
        ).count()

    def get_completed_sessions_for_tlcb_service(self) -> int:
        """
        Số buổi ĐÃ hoàn thành cho các phác đồ có service.type = 'TLCB'.
        """
        return TreatmentSession.objects.filter(
            treatment_request__bill=self,
            treatment_request__service__type='TLCB',
            is_done=True
        ).count()

    def get_uncompleted_sessions_for_tlds_service(self) -> int:
        """
        Số buổi CHƯA hoàn thành cho các phác đồ có service.type = 'TLDS'.
        """
        return TreatmentSession.objects.filter(
            treatment_request__bill=self,
            treatment_request__service__type='TLDS',
            is_done=False
        ).count()

    def get_completed_sessions_for_tlds_service(self) -> int:
        """
        Số buổi ĐÃ hoàn thành cho các phác đồ có service.type = 'TLDS'.
        """
        return TreatmentSession.objects.filter(
            treatment_request__bill=self,
            treatment_request__service__type='TLDS',
            is_done=True
        ).count()

    def clean(self):
        """
        ⚠️ ĐÃ ĐỔI NGỮ NGHĨA: fully_paid = KHÁCH HÀNG không còn nợ (tổng mọi bill đã được thanh toán hết).
        Nếu bạn muốn 'fully_paid' chỉ phản ánh RIÊNG bill này, đổi lại về: self.bill_amount_remaining() <= 0
        """
        self.fully_paid = self.amount_remaining() <= Decimal(0)

    def save(self, *args, **kwargs):
        self.clean()
        if not self.code:
            while True:
                new_code = f"BILL_{generate_random_code()}"
                if not Bill.objects.filter(code=new_code).exists():
                    self.code = new_code
                    break
        super().save(*args, **kwargs)
        
class PaymentHistory(models.Model):
    """
    Mỗi PaymentHistory = 1 đợt thanh toán.
    Sau khi lưu, hệ thống phân bổ tiền vào các ARItem (công nợ) và tạo Bill cho đợt thanh toán này.
    """
    bill = models.ForeignKey('app_treatment.Bill', related_name='payments',
                             on_delete=models.CASCADE, null=True, blank=True)
    ar_item = models.ForeignKey('ARItem', on_delete=models.CASCADE, related_name='payment_histories', null=True, blank=True) 
    
    # ⬇️ KHÔNG còn cho null/blank
    customer = models.ForeignKey('app_customer.Customer', on_delete=models.CASCADE,
                                 related_name='payments')
    paid_amount = models.DecimalField(max_digits=25, decimal_places=2)
    paid_method = models.CharField(max_length=25, choices=Bill.PAID_METHOD)
    code = models.CharField(max_length=255, unique=True, null=True, blank=True)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['bill'], name='uniq_one_payment_per_bill'),
        ]

    def clean(self):
        if self.ar_item and self.customer_id and self.ar_item.customer_id != self.customer_id:
            raise ValidationError("Customer của Payment phải trùng với Customer của ARItem.")

    def __str__(self):
        return f"Payment {self.code or ''} {self.paid_amount} for AR#{self.ar_item_id}"

    def _gen_code(self, prefix: str = "PH_") -> str:
        return unique_code(PaymentHistory, prefix)

    @transaction.atomic
    def save(self, *args, **kwargs):
        is_create = self._state.adding
        if not is_create:
            raise ValidationError("Không cho phép sửa PaymentHistory; hãy tạo bút toán điều chỉnh.")

        if self.paid_amount is None or self.paid_amount <= Decimal(0):
            raise ValidationError("paid_amount must be > 0")

        if not self.code:
            self.code = self._gen_code()

        # Chuẩn hoá customer theo ARItem cho chắc chắn
        if self.ar_item and self.customer_id != self.ar_item.customer_id:
            self.customer_id = self.ar_item.customer_id

        # Lưu để có self.id
        super().save(*args, **kwargs)

        # Cập nhật DUY NHẤT ARItem này
        ARItem = apps.get_model('app_treatment', 'ARItem')
        ar = ARItem.objects.select_for_update().get(id=self.ar_item_id)

        # Không cho thanh toán vượt quá dư nợ
        remaining = (ar.amount_original or Decimal('0')) - (ar.amount_paid or Decimal('0'))
        if self.paid_amount > remaining:
            raise ValidationError("Số tiền thanh toán vượt quá dư nợ của phiếu công nợ.")

        ar.amount_paid = (ar.amount_paid or Decimal('0')) + self.paid_amount
        ar.status = 'closed' if ar.amount_paid >= ar.amount_original else 'partial'
        ar.save(update_fields=['amount_paid', 'status'])

        # Bill cho ĐỢT THU (nếu còn dùng Bill)
        if not self.bill_id:
            bill = Bill.objects.create(
                customer=self.customer,
                paid_ammount=self.paid_amount,   # số tiền của đợt này
            )
            if not getattr(bill, 'code', None):
                bill.code = unique_code(Bill, "BILL_")
                bill.save(update_fields=['code'])
            self.bill = bill
            super().save(update_fields=['bill'])
        else:
            self.bill.paid_ammount = self.paid_amount
            self.bill.save(update_fields=['paid_ammount'])

    def delete(self, *args, **kwargs):
        raise ValidationError("Không cho xoá PaymentHistory; hãy tạo bút toán điều chỉnh.")
    
class TreatmentRequest(models.Model):

    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="treatment_requests", null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='treatment_requests')
    code = models.CharField(max_length=20, unique=True,blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    selected_package_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_done = models.BooleanField(default=False)
    
    note = models.TextField(null=True,blank=True,verbose_name="Ghi chú")
    
    doctor_profile = models.ForeignKey(
        'app_hr.HrUserProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='treatment_requests',
        db_index=True,
        verbose_name="Bác sĩ (HR)"
    )
    
    discount = models.ForeignKey(
        'app_home.Discount', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='treatment_requests',
        verbose_name="Mã giảm giá"
    )
    
    diagnosis = models.TextField(null=True, blank=True, verbose_name="Chẩn đoán")
    treatment_package = models.ForeignKey(
        TreatmentPackage, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='treatment_requests', verbose_name="Gói liệu trình"
    )
    
    def package_price_original(self) -> Decimal:
        """Giá gốc (không giảm)"""
        if self.service_id:
            if self.treatment_package_id:
                stp = ServiceTreatmentPackage.objects.filter(
                    service=self.service,
                    treatment_package=self.treatment_package
                ).first()
                if stp and getattr(stp, "price", None) is not None:
                    return stp.price
            return getattr(self.service, "price", Decimal(0)) or Decimal(0)
        return Decimal(0)
    
    def package_price(self) -> Decimal:
        """Giá sau khi áp dụng discount"""
        original = self.package_price_original()
        
        if not self.discount:
            return original
        
        if self.discount.type in ('percentage', 'percent'):
            discount_amount = (original * self.discount.rate) / Decimal('100')
            return original - discount_amount
        elif self.discount.type in ('fixed', 'amount'):
            return max(Decimal('0'), original - self.discount.rate)
        
        return original
    
    def recalc_ar(self):
        """
        Đồng bộ công nợ (ARItem) theo giá sau khuyến mãi.
        - Nếu có ARItem: update amount_original + status.
        - Nếu chưa có và amount > 0: tạo mới.
        - Nếu amount = 0: xoá ARItem (nếu chưa phát sinh thanh toán).
        """

        amount = self.package_price() or Decimal('0')
        ct = ContentType.objects.get_for_model(TreatmentRequest)

        qs = ARItem.objects.select_for_update().filter(
            content_type=ct, object_id=self.id
        )

        if amount > 0:
            if qs.exists():
                ar = qs.first()
                paid = ar.amount_paid or Decimal('0')
                ar.amount_original = amount
                # set trạng thái theo số đã thanh toán
                if paid >= amount:
                    ar.status = 'closed'
                elif paid > 0:
                    ar.status = 'partial'
                else:
                    ar.status = 'open'
                ar.save(update_fields=['amount_original', 'status'])
            else:
                # cần có customer để gán công nợ
                customer = getattr(self, 'customer', None)
                if customer is None:
                    # nếu project lưu customer ở booking, có thể lấy như bạn đang làm:
                    any_sess = self.treatment_sessions.select_related('booking__customer').first()
                    customer = getattr(getattr(any_sess, 'booking', None), 'customer', None)

                ARItem.objects.create(
                    customer=customer,
                    content_type=ct,
                    object_id=self.id,
                    description=f'Phác đồ: {getattr(self.service, "name", "")}',
                    amount_original=amount,
                    status='open',
                )
        else:
            # amount == 0 → có thể xoá nếu chưa phát sinh thanh toán
            if qs.exists():
                ar = qs.first()
                if (ar.amount_paid or Decimal('0')) == 0:
                    qs.delete()
                else:
                    # nếu đã có thanh toán > 0 mà amount=0, tuỳ policy dự án:
                    #  - đánh dấu closed + tạo bút toán điều chỉnh hoàn tiền
                    #  - hoặc log cảnh báo
                    ar.status = 'closed'
                    ar.save(update_fields=['status'])

    def compute_is_done(self) -> bool:
        """
        Phác đồ coi là HOÀN THÀNH khi:
        - Có ít nhất 1 kỹ thuật thuộc bất kỳ buổi nào
        - Và *không còn* kỹ thuật nào has_come=False
        """
        qs = SessionTechicalSetting.objects.filter(session__treatment_request=self)
        return qs.exists() and not qs.filter(has_come=False).exists()

    def refresh_done_status(self, commit: bool = True) -> bool:
        new_val = self.compute_is_done()
        if self.is_done != new_val:
            self.is_done = new_val
            if commit:
                self.save(update_fields=["is_done"])
        return self.is_done

    def __str__(self):
        return f"{self.code}"
    def save(self, *args, **kwargs):
        self.clean()
        if not self.code:
            while True:
                new_code = f"TR_{generate_random_code()}"
                if not TreatmentRequest.objects.filter(code=new_code).exists():
                    self.code = new_code
                    break
        super().save(*args, **kwargs)
    def get_total_price_is_done_treatment_sessions(self):

        total = (
            SessionTechicalSetting.objects
            .filter(session__treatment_request=self, has_come=True)
            .aggregate(total=Coalesce(Sum('techical_setting__price'),
                                    Value(0, output_field=DecimalField(max_digits=18, decimal_places=2))))
        )['total']
        return total

    def get_treatment_sessions_summary(self):
        summary = self.treatment_sessions.aggregate(
            remaining=Count('id', filter=Q(is_done=False)),
            done=Count('id', filter=Q(is_done=True))
        )
        return summary
    
@receiver(post_save, sender=TreatmentRequest)
def create_ar_on_treatment_created(sender, instance: 'TreatmentRequest', created, **kwargs):
    if not created:
        return
    if not instance.customer_id:
        return
    
    amount = instance.package_price() or Decimal('0.00')
    if amount <= 0:
        return
    
    ARItem.objects.create(
        customer=instance.customer,
        content_type=ContentType.objects.get_for_model(sender),
        object_id=instance.id,
        description=f'Phác đồ: {getattr(instance.service, "name", "")}',
        amount_original=amount,
    )

class TreatmentSession(models.Model):
    treatment_request = models.ForeignKey(TreatmentRequest,on_delete=models.CASCADE,verbose_name="Yêu cầu trị liệu",related_name="treatment_sessions")
    floor = models.ForeignKey(Floor,on_delete=models.SET_NULL,null=True,blank=True,verbose_name="Tầng")
    note = models.TextField(null=True,blank=True,verbose_name="Ghi chú")
    content = models.TextField(null=True,blank=True)
    is_done = models.BooleanField(default=False, editable=False)
    designated_experts = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="treatment_session")
    
    index_no = models.PositiveIntegerField(default=1, db_index=True, verbose_name="Số thứ tự buổi")
    booking = models.OneToOneField(Booking, on_delete=models.SET_NULL,
                                   null=True, blank=True, verbose_name="Lịch hẹn")
    
    def compute_is_done(self) -> bool:
        """
        Buổi coi là HOÀN THÀNH khi:
        - Có ít nhất 1 item kỹ thuật, và
        - Không còn item nào has_come=False
        """
        qs = self.sessiontechicalsetting_set
        return qs.exists() and not qs.filter(has_come=False).exists()

    def refresh_done_status(self, commit: bool = True) -> bool:
        """Tính lại is_done theo các kỹ thuật của *buổi*, rồi đồng bộ DB."""
        new_val = self.compute_is_done()
        changed = (self.is_done != new_val)
        if changed:
            self.is_done = new_val
            if commit:
                self.save(update_fields=["is_done"])
        # 🔁 Luôn đồng bộ trạng thái phác đồ “cha”
        if self.treatment_request_id:
            self.treatment_request.refresh_done_status(commit=True)
        return self.is_done

    @property
    def is_completed(self) -> bool:
        """Property chỉ-đọc, luôn tính theo item hiện tại (không phụ thuộc DB field)."""
        return self.compute_is_done()

    def get_designated_experts(self):
        try:
            return ', '.join([expert.get_full_name() for expert in self.designated_experts.all()])
        except AttributeError:
            return None

    def __str__(self):
        return f"Session #{self.id} ({self.sessiontechicalsetting_set.count()} kỹ thuật)"

class SessionTechicalSetting(models.Model):
    
    session = models.ForeignKey(TreatmentSession, on_delete=models.CASCADE, verbose_name="Buổi trị liệu")
    techical_setting = models.ForeignKey(TechicalSetting, on_delete=models.CASCADE, verbose_name="Kỹ thuật thực hiện")
    expert = models.ForeignKey(
        'app_hr.HrUserProfile', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='session_tech_settings'
    )

    duration_minutes = models.PositiveIntegerField(default=10, verbose_name="Thời gian (phút)")
    room = models.CharField(max_length=100, null=True, blank=True, verbose_name="Phòng")
    has_come = models.BooleanField(default=False, db_index=True, verbose_name="Trạng thái")
    
    def clean(self):
        # đảm bảo chỉ chọn CTV
        if self.expert and self.expert.type != 'collaborator':
            raise ValidationError("expert must be a collaborator (CTV).")

    def calculate_expert_payment(self):
        # Với FK expert (1 người/1 kỹ thuật), full price cho người đó:
        return self.techical_setting.price if self.expert_id else 0

    def calculate_expert_time(self):
        # Nếu cần “tỷ lệ” thời gian khi có nhiều chuyên gia,
        # thì phải chuyển sang M2M. Còn FK thì trả 1.0
        return 1.0 if self.expert_id else 0.0
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # bất kỳ thay đổi nào ở item cũng có thể ảnh hưởng đến is_done
        self.session.refresh_done_status(commit=True)

    def delete(self, *args, **kwargs):
        session = self.session
        super().delete(*args, **kwargs)
        session.refresh_done_status(commit=True)
    
    def __str__(self):
        return f"{self.session} - {self.techical_setting}"


class ReExamination(models.Model):
    REEXAMINATION_STATUS = [
        ('pending', 'Chờ tái khám'),
        ('completed', 'Đã tái khám'),
    ]

    status = models.CharField(max_length=20, choices=REEXAMINATION_STATUS, default='pending')
    bill = models.ForeignKey(Bill,on_delete=models.SET_NULL,null=True)
    appointment_date = models.DateField(null=True, blank=True, verbose_name="Ngày hẹn tái khám")
    doctor_evaluation = models.TextField(null=True, blank=True, verbose_name="Đánh giá của bác sĩ")
    recommendation = models.TextField(null=True, blank=True, verbose_name="Lời khuyên")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Tái khám {self.id} - Booking {self.booking.id} - {self.get_status_display()}"

class ExpertSessionRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    treatment_request = models.ForeignKey(TreatmentRequest, on_delete=models.CASCADE,null=True,blank=True)
    techical_setting = models.ForeignKey(TechicalSetting, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'treatment_request', 'techical_setting')
        
class ARItem(models.Model):
    """
    Một mục công nợ phát sinh khi tạo:
    - Phác đồ (TreatmentRequest): amount_original = package_price()
    - Đơn thuốc (DoctorProcess): amount_original = total_product_amount_after_discount()
    Có thể thanh toán nhiều đợt (partial).
    """
    created = models.DateTimeField(default=timezone.now)
    customer = models.ForeignKey('app_customer.Customer', on_delete=models.CASCADE, related_name='ar_items')

    # Liên kết tới nguồn phát sinh công nợ (TR/DoctorProcess)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    source = GenericForeignKey('content_type', 'object_id')

    description = models.CharField(max_length=255, blank=True, default='')
    amount_original = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    STATUS = (('open', 'Open'), ('partial', 'Partial'), ('closed', 'Closed'))
    status = models.CharField(max_length=10, choices=STATUS, default='open')

    class Meta:
        indexes = [models.Index(fields=['customer', 'status'])]

    @property
    def amount_remaining(self) -> Decimal:
        return max(Decimal('0.00'), (self.amount_original or 0) - (self.amount_paid or 0))

    def apply_payment(self, pay_amount: Decimal) -> Decimal:
        """
        Cấn trừ 1 khoản thanh toán vào công nợ này. Trả về số tiền còn dư chưa cấn.
        """
        if pay_amount <= 0:
            return Decimal('0.00')
        can_apply = min(pay_amount, self.amount_remaining)
        self.amount_paid = (self.amount_paid or Decimal('0.00')) + can_apply
        # cập nhật trạng thái
        remaining_after = (self.amount_original or Decimal('0.00')) - self.amount_paid
        if remaining_after <= 0:
            self.status = 'closed'
        elif self.amount_paid > 0:
            self.status = 'partial'
        else:
            self.status = 'open'
        self.save(update_fields=['amount_paid', 'status'])
        return pay_amount - can_apply
