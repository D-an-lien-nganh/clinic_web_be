from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.apps import apps as django_apps
from django.conf import settings
from django.db import models, transaction
from django.db.models import F, Sum, Q, Value, DecimalField
from django.db.models.functions import Coalesce

from app_home.models import UserProfile, get_file_path, Position

DEC = DecimalField(max_digits=18, decimal_places=2)

class HrRunningNumber(models.Model):
    KIND_CHOICES = [
        ('employee', 'Nhân viên'),
        ('collaborator', 'Cộng tác viên'),
    ]
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, unique=True)
    value = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_hr"

    def __str__(self):
        return f"{self.kind}:{self.value}"

class HrUserProfile(models.Model):
    CONTRACT_STATUS = [
        ('AC', 'Còn hiệu lực'),
        ('EX', 'Hết liệu lực'),
    ]
    CONTRACT_TYPE = [
        ('OF', 'Chính thức'),
        ('IN', 'Thực tập sinh'),
    ]
    TYPE_CHOICES = [
        ('employee', 'Nhân viên'),
        ('collaborator', 'Cộng tác viên'),
    ]

    created = models.DateTimeField(auto_now_add=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name="hr_user_profile",
    )
    
    code = models.CharField(
        max_length=20, unique=True, null=True, blank=True, db_index=True, verbose_name="Mã nhân sự"
    )

    user_profile = models.OneToOneField(
        UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='hr_profile'
    )

    # Thuộc tính nhân sự
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='employee')
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    mobile = models.CharField(max_length=30, blank=True, null=True)
    
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)

    contract = models.FileField(upload_to=get_file_path, null=True, blank=True)
    directory_string_var = "THABICARE/app_hr/Contracts/"
    contract_start = models.DateField(null=True, blank=True)
    contract_end = models.DateField(null=True, blank=True)
    contract_status = models.CharField(max_length=2, choices=CONTRACT_STATUS, null=True, blank=True)
    contract_type = models.CharField(max_length=2, choices=CONTRACT_TYPE, null=True, blank=True)

    start_date = models.DateField(null=True, blank=True)
    level = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.full_name or self.email or f"HR#{self.pk}"

    # ---------- Helpers ----------
    def _base_qs(self, start: date | None = None, end: date | None = None):
        if not self.user_id:
            from django.db.models import QuerySet
            return django_apps.get_model('app_treatment', 'SessionTechicalSetting').objects.none()

        SessionTechicalSetting = django_apps.get_model('app_treatment', 'SessionTechicalSetting')
        qs = SessionTechicalSetting.objects.filter(
            expert_id=self.user_id,
            has_come=True,
        )
        if start and end:
            qs = qs.filter(session__booking__receiving_day__range=[start, end])
        return qs

    def _latest_coeff(self) -> float:
        if self.position and self.position.performance_coefficient is not None:
            return float(self.position.performance_coefficient)
        return 1.0

    # ---------- Tính thâm niên ----------
    def calculate_seniority(self) -> str | None:
        if not self.start_date:
            return None
        today = date.today()
        delta_years = today.year - self.start_date.year
        delta_months = today.month - self.start_date.month
        if delta_months < 0:
            delta_years -= 1
            delta_months += 12
        if delta_years < 1:
            total_months = delta_years * 12 + delta_months
            return f"{total_months} tháng"
        return f"{delta_years} năm"

    # ---------- Thống kê lượt kỹ thuật ----------
    def calculate_expert_done_session_exp(self, start: date | None = None, end: date | None = None) -> int:
        """
        Số lượt kỹ thuật thuộc nhóm TLCB (Trị liệu chữa bệnh) mà nhân sự đã thực hiện.
        """
        return self._base_qs(start, end).filter(techical_setting__type='TLCB').count()

    def calculate_expert_done_session_ser(self, start: date | None = None, end: date | None = None) -> int:
        """
        Số lượt kỹ thuật thuộc nhóm TLDS (Trị liệu dưỡng sinh) mà nhân sự đã thực hiện.
        """
        return self._base_qs(start, end).filter(techical_setting__type='TLDS').count()

    # ---------- Tính lương hiệu suất ----------
    def calculate_expert_salary(self, start: date | None = None, end: date | None = None) -> Decimal:
        """
        Lương hiệu suất = ∑(giá kỹ thuật) × hệ số chức vụ.
        (Theo logic mới: 1 kỹ thuật chỉ 1 người làm → không chia đầu người.)
        """
        total_price = self._base_qs(start, end).aggregate(
            s=Coalesce(Sum(F('techical_setting__price'), output_field=DEC), Value(0, output_field=DEC))
        )['s'] or Decimal('0')

        coeff = Decimal(str(self._latest_coeff()))
        return (total_price * coeff).quantize(Decimal('0.01'))  # làm tròn 2 số thập phân
    
    def _gen_code(self) -> str:
        """Sinh mã theo type, tăng số thứ tự độc lập cho từng type, đuôi năm hiện tại (yy)."""
        prefix = 'NV' if self.type == 'employee' else 'CTV'
        with transaction.atomic():
            counter, _ = HrRunningNumber.objects.select_for_update().get_or_create(
                kind=self.type, defaults={'value': 0}
            )
            counter.value += 1
            counter.save(update_fields=['value'])
            seq = counter.value

        yy = date.today().year % 100
        return f"{prefix}{seq:03d}-{yy:02d}"

    def save(self, *args, **kwargs):
        # Chỉ sinh code khi tạo mới và chưa có code
        if self.pk is None and not self.code:
            self.code = self._gen_code()
        super().save(*args, **kwargs)
