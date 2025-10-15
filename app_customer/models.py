from django.db import models
from django.conf import settings
from app_home.models import GENDER_TYPE_CHOICES, Commission, generate_random_code,\
LeadSource, TimeFrame, LeadSourceActor
from app_product.models import Service
from colorfield.fields import ColorField

MAIN_STATUS = [
    ('1', 'Khách chưa sử dụng dịch vụ'),
    ('2', 'Khách đang sử dụng dịch vụ'),
    ('3', 'Khách đã sử dụng dịch vụ'),
]
TYPE_OF_CALL = [
    ('incoming', 'Khách gọi tới'),
    ('outgoing', 'cuộc gọi đi'),
]
CUSTOMER_SOLIDARIETY = [
    ('glls', 'Gọi lại lần sau'),
    ('tb', 'Thuê bao'),
    ('knm', 'Không nghe máy'),
    ('cn', 'Cân nhắc'),
    ('dc', 'Đã chốt'),
    ('tc', 'Từ chối'),
]
FEEDBACK_FORMAT = [
    ('direct', 'Trực tiếp'),
    ('indirect', 'Gián tiếp'),
]
FEEDBACK_RATING = [
    (1, 'Rất tệ'),
    (2, 'Tệ'),
    (3, 'Trung bình'),
    (4, 'Tốt'),
    (5, 'Xuất sắc'),
]
CUSTOMER_REQUEST = [
        ('none', 'Chưa yêu cầu dịch vụ'),
        ('service', 'Yêu cầu dịch vụ'),
        ('experience', 'Yêu cầu trải nghiệm'),
        ('experience_to_service', 'Trải nghiệm chuyển sang dịch vụ'),
    ]
class LeadStatus(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    color = ColorField(default='#0D6EFD')
    note = models.TextField(null=True,blank=True)

    def __str__(self):
        
        return f"{self.name}"
    
    class Meta:
        app_label = "app_customer"

class TreatmentState(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    color = ColorField(default='#0D6EFD')
    note = models.TextField(null=True,blank=True)

    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        app_label = "app_customer"
        
class CustomerLevel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    name = models.CharField(max_length=50)
    level = models.PositiveIntegerField()
    customer_type = models.CharField(max_length=20, choices=MAIN_STATUS, blank=True, default=1)
    lead_status = models.ManyToManyField(LeadStatus, blank=True)
    treatment_state = models.ManyToManyField(TreatmentState, blank=True)
    
    def __str__(self):
        customer_type_label = dict(MAIN_STATUS).get(self.customer_type, "Không xác định")
        return f"{self.name} - {customer_type_label}"
    
    class Meta:
        app_label = "app_customer"
        
class CustomerRequest(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)
    color = ColorField(default='#0D6EFD')
    note = models.TextField(null=True,blank=True)

    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        app_label = "app_customer"
        
class CustomerRunningNumber(models.Model):
    """Model để track số thứ tự tự động tăng cho mã khách hàng"""
    kind = models.CharField(max_length=20, unique=True, default='customer')
    value = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_customer"

    def __str__(self):
        return f"Customer Running Number: {self.value}"
        
class Customer(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    code = models.CharField(max_length=255, unique=True, blank=True)
    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=20, choices=GENDER_TYPE_CHOICES, default='MA')
    birth = models.DateField(null=True, blank=True)

    # ── Thêm 3 trường mới ─────────────────────────────────────────
    birth_date = models.DateField(null=True, blank=True)  # chỉ set khi có đủ dd/mm/yyyy
    birth_raw = models.CharField(max_length=10, null=True, blank=True)
    BIRTH_ACCURACY = (
        ("year", "Year only"),       # "1990"
        ("month", "Month & Year"),   # "01/1990"
        ("day", "Full Date"),        # "09/01/1990"
    )
    birth_accuracy = models.CharField(
        max_length=10, choices=BIRTH_ACCURACY, null=True, blank=True
    )
    
    mobile = models.CharField(max_length=10)
    email = models.EmailField(null=True, blank=True)
    
    city = models.CharField(max_length=100, null=True, blank=True)
    ward = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    contact_date = models.DateField(blank=True, null=True)
    time_frame = models.ForeignKey(TimeFrame, on_delete=models.SET_NULL, blank=True, null=True)

    service = models.ManyToManyField(Service, related_name="customer_interested", blank=True)
    
    main_status = models.CharField(max_length=100, choices=MAIN_STATUS, default='1') # phân ra làm 3 trạng thái là chưa mua, đang mua  và đã mua
    customer_request = models.ManyToManyField(CustomerRequest, blank=True) # phân ra làm 4 trạng thái là chưa yêu cầu dịch vụ,Yêu cầu trải nghiệm, Yêu cầu trải nghiệm  và Trải nghiệm chuyển sang dịch vụ
    lead_status = models.ForeignKey(LeadStatus, on_delete=models.SET_NULL, null=True, blank=True) # trạng thái khi khách hàng đang thuộc khách chưa mua, sau khi mua hàng nhớ set null
    treatment_status = models.ForeignKey(TreatmentState, on_delete=models.SET_NULL, null=True, blank=True) # trạng thái khi khách hàng đã là khách đang mua hoặc đã mua
    is_active = models.BooleanField(default=True)
    carreer = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        status_display = dict(MAIN_STATUS).get(int(self.main_status), "Unknown")
        return f"{self.name}|{status_display}"
    
    def get_all_cus_services(self):
        return self.customer_care.all()
    def get_all_problems(self):
        return self.customer_problems.all()
    
    @property
    def introduced_customer_count(self):
        # Tổng số KH mà KH này đã giới thiệu (ref_type='customer')
        return self.referred_others.count()
    
    # Tiện ích đọc nhanh “nguồn” hiện tại (1-1)
    @property
    def referral_kind(self):
        if hasattr(self, 'primary_referral') and self.primary_referral:
            return self.primary_referral.ref_type
        return None
    
    def _gen_code(self) -> str:
        """Sinh mã khách hàng theo định dạng KH001-25, KH002-25, etc."""
        from django.db import transaction
        from datetime import date
        
        with transaction.atomic():
            counter, _ = CustomerRunningNumber.objects.select_for_update().get_or_create(
                kind='customer', 
                defaults={'value': 0}
            )
            counter.value += 1
            counter.save(update_fields=['value'])
            seq = counter.value

        yy = date.today().year % 100  # Lấy 2 chữ số cuối của năm
        return f"KH{seq:03d}-{yy:02d}"
    
    def save(self, *args, **kwargs):
        """Override save để tự động sinh mã nếu chưa có"""
        if not self.code:
            self.code = self._gen_code()
        super().save(*args, **kwargs)

    @property
    def referral_label(self):
        """
        Chuỗi mô tả gọn nguồn giới thiệu cho hiển thị UI/báo cáo.
        """
        r = getattr(self, 'primary_referral', None)
        if not r:
            return None
        if r.ref_type == 'customer' and r.ref_customer:
            return f"KH:{r.ref_customer.code or r.ref_customer.name}"
        if r.ref_type == 'hr' and r.ref_hr:
            return f"HR:{r.ref_hr.code or r.ref_hr.full_name}"
        if r.ref_type == 'actor' and r.ref_actor:
            return f"{r.ref_actor.source.name}:{r.ref_actor.name}"
        return "unknown"
    
    class Meta:
        app_label = "app_customer"
        
class Referral(models.Model):
    """
    Nguồn giới thiệu CHÍNH (duy nhất) cho mỗi Customer.
    CHỈ 1-1: OneToOne với Customer.
    Ba khả năng: customer | hr | actor (thuộc LeadSource).
    """
    REF_TYPE = [
        ('customer', 'Khách hàng'),
        ('hr', 'CTV/HR'),
        ('actor', 'Actor thuộc LeadSource'),
        ('unknown', 'Khác/Không rõ'),
    ]

    created = models.DateTimeField(auto_now_add=True)
    customer = models.OneToOneField('Customer', on_delete=models.CASCADE, related_name='primary_referral')

    ref_type = models.CharField(max_length=20, choices=REF_TYPE, default='unknown')
    ref_customer = models.ForeignKey('Customer', on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_others')
    ref_hr = models.ForeignKey('app_hr.HrUserProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_customers')
    ref_actor = models.ForeignKey(LeadSourceActor, on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_customers')

    # Lưu vết nhập liệu/mã tra cứu lúc tạo (không bắt buộc)
    lookup_code = models.CharField(max_length=100, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        app_label = "app_customer"
        indexes = [models.Index(fields=['ref_type'])]
        constraints = [
            models.CheckConstraint(
                name='referral_exact_one_branch_or_unknown',
                check=(
                    models.Q(ref_type='customer', ref_customer__isnull=False, ref_hr__isnull=True, ref_actor__isnull=True) |
                    models.Q(ref_type='hr',       ref_customer__isnull=True,  ref_hr__isnull=False, ref_actor__isnull=True) |
                    models.Q(ref_type='actor',    ref_customer__isnull=True,  ref_hr__isnull=True,  ref_actor__isnull=False) |
                    models.Q(ref_type='unknown',  ref_customer__isnull=True,  ref_hr__isnull=True,  ref_actor__isnull=True)
                )
            )
        ]

    def __str__(self):
        if self.ref_type == 'customer' and self.ref_customer:
            return f"{self.customer.name} ⇐ KH:{self.ref_customer.name}"
        if self.ref_type == 'hr' and self.ref_hr:
            return f"{self.customer.name} ⇐ HR:{self.ref_hr.full_name or self.ref_hr.code}"
        if self.ref_type == 'actor' and self.ref_actor:
            return f"{self.customer.name} ⇐ {self.ref_actor.source.name}:{self.ref_actor.name}"
        return f"{self.customer.name} ⇐ unknown"

class customer_introducers(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    introducer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    commission = models.ForeignKey(Commission, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        app_label = "app_customer"

class CustomerProblem(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    problem = models.TextField(null=True, blank=True)
    encounter_pain = models.TextField(null=True, blank=True)
    desire = models.TextField(null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="customer_problems")

    def __str__(self):
        return f"Customer: {self.customer.name}|{self.customer.code} - {self.problem}"

    class Meta:
        app_label = "app_customer"

class CustomerCare(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    date = models.DateField()
    note = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=100, choices=TYPE_OF_CALL, null=True, blank=True)

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="customer_care")
    solidarity = models.CharField(max_length=100, choices=CUSTOMER_SOLIDARIETY, null=True, blank=True)
    def __str__(self):
        return f"{self.customer.name}|{self.type}"
    
class FeedBack(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(max_length=255, null=True, blank=True)
    source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, null=True, blank=True, related_name="feedback_source")
    source_link = models.CharField(max_length=255, null=True, blank=True)
    format = models.CharField(max_length=100, choices=FEEDBACK_FORMAT, blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_TYPE_CHOICES, blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    mobile = models.CharField(max_length=10, blank=True, null=True)

    service = models.ManyToManyField(Service, related_name="feedback_interested", blank=True)
    satification_level = models.CharField(max_length=10, choices=FEEDBACK_RATING, null=True, blank=True)
    service_quality = models.CharField(max_length=10, choices=FEEDBACK_RATING, null=True, blank=True)
    examination_quality = models.CharField(max_length=10, choices=FEEDBACK_RATING, null=True, blank=True)
    serve_quality = models.CharField(max_length=10, choices=FEEDBACK_RATING, null=True, blank=True)
    customercare_quality = models.CharField(max_length=10, choices=FEEDBACK_RATING, null=True, blank=True)

    unsatify_note = models.TextField(null=True, blank=True)
    suggest_note = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}|{self.format}"

    class Meta:
        app_label = "app_customer"

