from django.db import models, transaction
from django.db.models import F, Q
from django.conf import settings
from app_home.models import TreatmentPackage, generate_random_code,\
Unit
from django.utils import timezone
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.apps import apps
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from app_accounting.models import *
STATUS_CHOICES = [
    ('active', 'Hoạt động'),
    ('inactive', 'Không hoạt động'),
]
SUPPLIE_STATUS = [
    ('new', 'Mới'),
    ('inuse', 'Đang sử dụng'),
    ('old', 'Cũ')
]
REPAIR_STATUS = [
    ('1', 'wait'),
    ('2', 'in progress'),
    ('3', 'delayed'),
    ('4', 'finished'),
    ('5', 'cancel')
]
STOCK_IN_STATUS = [
    ('pending', 'Chờ duyệt'),
    ('approve', 'Đã duyệt'),
    ('deny', 'Từ chối'),
    ('stocked_in', 'Đã nhập kho'),
]
STOCK_OUT_STATUS = [
    ('pending', 'Chờ duyệt'),
    ('approve', 'Đã duyệt'),
    ('stocked_out_missing', 'Đã xuất (thiếu)'),
    ('stocked_out', 'Đã xuất'),
    ('deny', 'Từ chối'),
]
STOCK_OUT_TYPE = [
    ('customer', 'Khách hàng'),
    ('employee', 'Nội bộ'),
]
class Service(models.Model):
    SERVICE_TYPE =[
        ('TLCB', 'Trị liệu chữa bệnh'),
        ('TLDS', 'Trị liệu dưỡng sinh'),
    ]
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    code = models.CharField(max_length=255,unique=True, blank=True, null=True)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, null=True, blank=True)

    type = models.CharField(max_length=255, choices=SERVICE_TYPE, null=True, blank=True)


    def __str__(self):
        return f"{self.name}|{self.status}"

    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                new_code = generate_random_code()
                if not Service.objects.filter(code=new_code).exists():
                    self.code = new_code
                    break
        super().save(*args, **kwargs)

    class Meta:
        app_label = "app_product"
# Dịch vụ gói liệu trình 
class ServiceTreatmentPackage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='service_treatment_packages')
    treatment_package = models.ForeignKey(TreatmentPackage, on_delete=models.CASCADE, related_name='treatment_services')
    price = models.DecimalField(max_digits=20, decimal_places=2)
    duration = models.IntegerField(default=0)
    class Meta:
        unique_together = ('service', 'treatment_package')
        app_label = "app_product"

    def __str__(self):
        return f"{self.service.name} - {self.treatment_package.name} ({self.price})"
    
class Product(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('thuoc', 'Thuốc'),
        ('tpchucnang', 'Thực phẩm chức năng'),
        ('consumable', 'Vật tư tiêu hao'),
        ('device', 'Thiết bị')
    ]
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    code = models.CharField(max_length=255,unique=True, blank=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    effect = models.TextField(null=True, blank=True)

    origin = models.CharField(max_length=255, null=True, blank=True)
    sell_price = models.DecimalField(max_digits=40, decimal_places=2, null=True, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name}"
    
    def save(self, *args, **kwargs):
        print('hello')
        if not self.code:
            while True:
                new_code = generate_random_code()
                if not Product.objects.filter(code=new_code).exists():
                    self.code = new_code
                    break
        super().save(*args, **kwargs)

    class Meta:
        app_label = "app_product"

class Facility(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    code = models.CharField(max_length=255, unique=True)

    name = models.CharField(max_length=255)
    origin = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    import_price = models.DecimalField(max_digits=40,decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=100, choices=SUPPLIE_STATUS, default="new")
    is_malfunction = models.BooleanField(default=False)
    effect = models.TextField(null=True, blank=True)
    malfunction_status = models.TextField(null=True, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.name}|{self.status}"

    def maintenance_count(self):
        return Maintenance.objects.filter(facility=self, is_maintenanced=True).count()

    def fix_count(self):
        return FixSchedule.objects.filter(facility=self, is_fixed=True).count()

    class Meta:
        app_label = "app_product"
class FacilityExport(models.Model):
    """
    Bản ghi xuất kho. Khi tạo/sửa/xóa sẽ tự động cập nhật Facility.quantity qua signals.
    """
    EXPORT_TYPE = (
        ("internal", "Dùng nội bộ"),
        ("customer", "Bán cho khách hàng"),
    )

    facility = models.ForeignKey(Facility, on_delete=models.PROTECT, related_name="exports")
    supplier = models.ForeignKey("Supplier", on_delete=models.PROTECT, null=True, blank=True)
    export_type = models.CharField(max_length=20, choices=EXPORT_TYPE)
    quantity = models.PositiveIntegerField()  # Số lượng xuất (đơn vị theo Facility.unit)
    unit_price = models.DecimalField(max_digits=40, decimal_places=2, null=True, blank=True)  # dùng khi bán KH
    # Thông tin tham chiếu (tùy dự án có thể để null):
    customer = models.ForeignKey("app_customer.Customer", on_delete=models.SET_NULL, null=True, blank=True)  # Dùng khi bán KH(max_length=255, null=True, blank=True)
    internal_department = models.CharField(max_length=255, null=True, blank=True)

    note = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "app_product"
        ordering = ["-id"]

    def __str__(self):
        return f"Export#{self.id}-{self.facility.code}-{self.quantity}"

    @property
    def total_amount(self):
        # Tổng tiền xuất (áp dụng khi bán KH)
        if self.unit_price and self.export_type == "customer":
            return self.unit_price * self.quantity
        return None

    # Chặn xuất vượt tồn trong level ứng dụng
    def clean(self):
        # Lấy tồn hiện tại
        current_qty = Facility.objects.filter(pk=self.facility_id).values_list("quantity", flat=True).first() or 0

        if self.pk:
            # đang update: cộng bù lại số cũ rồi kiểm tra
            old = FacilityExport.objects.get(pk=self.pk)
            # Nếu đổi kho (facility) thì phải hoàn về kho cũ
            if old.facility_id != self.facility_id:
                # tồn kho mới phải đủ xuất số lượng mới
                if self.quantity > current_qty:
                    raise ValidationError("Số lượng tồn không đủ để xuất (đổi kho).")
            else:
                # cùng kho: chỉ cần kiểm tra phần tăng thêm
                delta = self.quantity - old.quantity
                if delta > 0 and delta > current_qty:
                    raise ValidationError("Số lượng tồn không đủ để tăng số lượng xuất.")
        else:
            # tạo mới
            if self.quantity > current_qty:
                raise ValidationError("Số lượng tồn không đủ để xuất.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
class Maintenance(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    date = models.DateField()
    note = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=100, choices=REPAIR_STATUS, default="1")
    is_maintenanced = models.BooleanField(default=False)

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="facility_maintenance")
    
    def __str__(self):
        return f"{self.date}|{self.status}"
    
    class Meta:
        app_label = "app_product"

class FixSchedule(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    date = models.DateField()
    note = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=100, choices=REPAIR_STATUS, default="1")
    is_fixed = models.BooleanField(default=False)

    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="facility_fixschedule")
    
    def __str__(self):
        return f"{self.date}|{self.status}"
    
    class Meta:
        app_label = "app_product"
        
class Supplier(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(max_length=255)
    MST = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, null=True, blank=True)
    mobile = models.CharField(max_length=10)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    product = models.ManyToManyField(Product, through='Warehouse')

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.mobile}|{self.name}"

    def get_related_products(self):
        return Product.objects.filter(warehouse__supplier=self)
    class Meta:
        app_label = "app_product"

class Warehouse(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    code = models.CharField(max_length=255, unique=True, blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    import_date = models.DateField(null=True, blank=True)
    export_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.supplier.name} - {self.product.name} - {self.quantity}"
    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                new_code = generate_random_code()
                if not Warehouse.objects.filter(code=new_code).exists():
                    self.code = new_code
                    break
        super().save(*args, **kwargs)
    class Meta:
        app_label = "app_product"

# models_stockin.py
from decimal import Decimal
from django.db import models, transaction
from django.conf import settings
from django.db.models import Sum, F, Q
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from app_product.models import (
    Supplier, Product, Facility, Warehouse,
    SupplierProductDebt, SupplierFacilityDebt,
    ProductDebtDetail, FacilityDebtDetail,
)

class StockIn(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_in_creator")

    code = models.CharField(max_length=255, unique=True, blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    # CHỌN 1 TRONG 2
    product  = models.ForeignKey(Product,  on_delete=models.CASCADE, null=True, blank=True)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, null=True, blank=True)

    quantity     = models.PositiveIntegerField(default=0)
    import_price = models.DecimalField(max_digits=20, decimal_places=2)
    full_paid    = models.BooleanField(default=False)
    import_date  = models.DateField()

    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_in_approver')
    note     = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        name = self.product.name if self.product_id else (self.facility.name if self.facility_id else "N/A")
        return f"{name}|{self.supplier.name}|{self.quantity}"

    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                new_code = f"SI{timezone.now().strftime('%Y%m%d%H%M%S')}"
                if not StockIn.objects.filter(code=new_code).exists():
                    self.code = new_code
                    break
        super().save(*args, **kwargs)

    def get_total(self) -> Decimal:
        return Decimal(self.quantity) * Decimal(self.import_price)

    def update_full_paid_status(self):
        if self.product_id:
            total_paid = ProductDebtDetail.objects.filter(stock_in=self)\
                           .aggregate(s=Sum('paid_amount'))['s'] or Decimal('0')
        else:
            total_paid = FacilityDebtDetail.objects.filter(stock_in=self)\
                           .aggregate(s=Sum('paid_amount'))['s'] or Decimal('0')
        new_full_paid = total_paid >= self.get_total()
        # tránh lặp post_save
        if new_full_paid != self.full_paid:
            StockIn.objects.filter(pk=self.pk).update(full_paid=new_full_paid)

    class Meta:
        app_label = "app_product"
        constraints = [
            models.CheckConstraint(
                name="stockin_one_of_product_or_facility",
                check=((Q(product__isnull=False) & Q(facility__isnull=True)) |
                       (Q(product__isnull=True)  & Q(facility__isnull=False))),
            ),
        ]

from decimal import Decimal
from django.db import transaction
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.db.models import F

from app_product.models import (
    StockIn, Facility, Warehouse,
    SupplierProductDebt, SupplierFacilityDebt,
    ProductDebtDetail, FacilityDebtDetail
)

# ---- helpers ----
def _total(amount_or_q, price=None) -> Decimal:
    if price is None:
        return Decimal(amount_or_q)
    return Decimal(amount_or_q) * Decimal(price)

def _adjust_product_debt(supplier, delta_amount: Decimal):
    if delta_amount == 0:
        return
    debt, _ = SupplierProductDebt.objects.get_or_create(
        supplier=supplier, defaults={"total_amount": Decimal("0")}
    )
    debt.total_amount = (debt.total_amount or Decimal("0")) + delta_amount
    debt.save(update_fields=["total_amount"])

def _adjust_facility_debt(supplier, delta_amount: Decimal):
    if delta_amount == 0:
        return
    debt, _ = SupplierFacilityDebt.objects.get_or_create(
        supplier=supplier, defaults={"total_amount": Decimal("0")}
    )
    debt.total_amount = (debt.total_amount or Decimal("0")) + delta_amount
    debt.save(update_fields=["total_amount"])


@receiver(pre_save, sender=StockIn)
def stockin_pre_save(sender, instance: StockIn, **kwargs):
    instance._old = None
    if instance.pk:
        try:
            instance._old = StockIn.objects.get(pk=instance.pk)
        except StockIn.DoesNotExist:
            pass


@receiver(post_save, sender=StockIn)
def stockin_post_save(sender, instance: StockIn, created, **kwargs):
    """
    - Nếu là nhập Facility: CẬP NHẬT tồn Facility theo delta số lượng.
    - Cập nhật đầu sổ nợ theo LOẠI (product/facility) và theo delta tiền.
    - Nếu là nhập Product: cập nhật Warehouse theo delta số lượng.
    """
    with transaction.atomic():
        old = getattr(instance, "_old", None)

        # ---------- 1) FACILITY INVENTORY ----------
        if instance.facility_id:
            if created or not old:
                Facility.objects.filter(pk=instance.facility_id)\
                    .update(quantity=F("quantity") + instance.quantity)
            else:
                if old.facility_id == instance.facility_id:
                    delta_qty = instance.quantity - old.quantity
                    if delta_qty:
                        Facility.objects.filter(pk=instance.facility_id)\
                            .update(quantity=F("quantity") + delta_qty)
                else:
                    # chuyển facility
                    if old.facility_id:
                        Facility.objects.filter(pk=old.facility_id)\
                            .update(quantity=F("quantity") - old.quantity)
                    Facility.objects.filter(pk=instance.facility_id)\
                        .update(quantity=F("quantity") + instance.quantity)

        # ---------- 2) DEBT HEADS (delta tiền) ----------
        # Tính tổng cũ / mới
        old_total = _total(old.quantity, old.import_price) if old else Decimal("0")
        new_total = instance.get_total()

        # Case phân loại (cũng xét đổi loại/sp/supplier)
        if created or not old:
            delta_amount = new_total
            if instance.product_id:
                _adjust_product_debt(instance.supplier, delta_amount)
            else:
                _adjust_facility_debt(instance.supplier, delta_amount)
        else:
            # Nếu đổi supplier hoặc đổi loại (product<->facility) hoặc đổi giá/số lượng
            if old.product_id and instance.product_id:
                # cùng loại PRODUCT
                if old.supplier_id == instance.supplier_id:
                    delta_amount = new_total - old_total
                    _adjust_product_debt(instance.supplier, delta_amount)
                else:
                    # đổi NCC
                    _adjust_product_debt(old.supplier, -old_total)
                    _adjust_product_debt(instance.supplier, new_total)

            elif old.facility_id and instance.facility_id:
                # cùng loại FACILITY
                if old.supplier_id == instance.supplier_id:
                    delta_amount = new_total - old_total
                    _adjust_facility_debt(instance.supplier, delta_amount)
                else:
                    # đổi NCC
                    _adjust_facility_debt(old.supplier, -old_total)
                    _adjust_facility_debt(instance.supplier, new_total)

            elif old.product_id and instance.facility_id:
                # Chuyển từ PRODUCT -> FACILITY
                _adjust_product_debt(old.supplier, -old_total)
                _adjust_facility_debt(instance.supplier, new_total)

            elif old.facility_id and instance.product_id:
                # Chuyển từ FACILITY -> PRODUCT
                _adjust_facility_debt(old.supplier, -old_total)
                _adjust_product_debt(instance.supplier, new_total)

        # ---------- 3) WAREHOUSE (chỉ cho PRODUCT) ----------
        if instance.product_id:
            if created or not old or not old.product_id or old.product_id != instance.product_id or old.supplier_id != instance.supplier_id:
                # tạo mới hoặc đổi product/supplier: set theo số mới
                wh, _ = Warehouse.objects.get_or_create(
                    product=instance.product, supplier=instance.supplier,
                    defaults={"user": instance.user, "quantity": 0, "import_date": instance.import_date},
                )
                # nếu trước đó có warehouse khác (do đổi product/supplier) thì trừ ở warehouse cũ
                if old and old.product_id and (old.product_id != instance.product_id or old.supplier_id != instance.supplier_id):
                    try:
                        old_wh = Warehouse.objects.get(product=old.product, supplier=old.supplier)
                        old_wh.quantity = F("quantity") - old.quantity
                        old_wh.save(update_fields=["quantity"])
                    except Warehouse.DoesNotExist:
                        pass
                # cộng số mới vào warehouse hiện tại
                wh.quantity = F("quantity") + instance.quantity if (created or not old) else F("quantity") + (instance.quantity if (not old or (old.product_id != instance.product_id or old.supplier_id != instance.supplier_id)) else (instance.quantity - old.quantity))
                wh.import_date = instance.import_date
                wh.save(update_fields=["quantity", "import_date"])
            else:
                # cùng product/supplier: chỉ cần delta
                delta_qty = instance.quantity - old.quantity
                if delta_qty:
                    Warehouse.objects.filter(product=instance.product, supplier=instance.supplier)\
                        .update(quantity=F("quantity") + delta_qty)


@receiver(post_delete, sender=StockIn)
def stockin_post_delete(sender, instance: StockIn, **kwargs):
    with transaction.atomic():
        total = instance.get_total()

        # 1) tồn Facility (nếu có)
        if instance.facility_id:
            Facility.objects.filter(pk=instance.facility_id)\
                .update(quantity=F("quantity") - instance.quantity)

        # 2) debt head đúng loại
        if instance.product_id:
            _adjust_product_debt(instance.supplier, -total)
        else:
            _adjust_facility_debt(instance.supplier, -total)

        # 3) Warehouse cho product
        if instance.product_id:
            Warehouse.objects.filter(product=instance.product, supplier=instance.supplier)\
                .update(quantity=F("quantity") - instance.quantity)
class StockOut(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_out_creator")

    code = models.CharField(max_length=255, unique=True, blank=True, null=True)

    # supplier: tham chiếu để biết hàng nhập từ NCC nào (không dùng kiểm kho)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    export_date = models.DateField()

    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_out_approver")
    type = models.CharField(max_length=255, choices=STOCK_OUT_TYPE, null=True, blank=True)

    # Đơn giá xuất (đơn giá thực tế)
    actual_stockout_price = models.DecimalField(max_digits=20, decimal_places=2)

    # Thêm khách hàng
    customer = models.ForeignKey('app_customer.Customer', on_delete=models.SET_NULL, null=True, blank=True)

    note = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # optional khi xuất thiếu
    actual_quantity = models.PositiveIntegerField(null=True, blank=True)
    missing_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.product.name}|{self.type or ''}"

    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                new_code = f"SO{timezone.now().strftime('%Y%m%d%H%M%S')}"
                if not StockOut.objects.filter(code=new_code).exists():
                    self.code = new_code
                    break
        super().save(*args, **kwargs)

    # Thành tiền thực tế (đúng với FE “Thành tiền”)
    def original_stockout_price(self):
        from decimal import Decimal
        q = Decimal(self.quantity or 0)
        p = self.actual_stockout_price or Decimal('0')
        return q * p

    class Meta:
        app_label = "app_product"
        
# Ghi nhớ bản cũ để tính delta/điều kiện xoá
@receiver(pre_save, sender=StockOut)
def stockout_pre_save(sender, instance: StockOut, **kwargs):
    instance._old = None
    if instance.pk:
        try:
            instance._old = StockOut.objects.get(pk=instance.pk)
        except StockOut.DoesNotExist:
            pass

def _stockout_amount(instance: StockOut) -> Decimal:
    # Thành tiền = quantity * actual_stockout_price
    # (đồng nhất với FE “Thành tiền” và helper original_stockout_price)
    qty = Decimal(instance.actual_quantity or instance.quantity or 0)
    price = Decimal(instance.actual_stockout_price or 0)
    return qty * price

def _sync_ar_for_stockout(instance: StockOut):
    """
    Đồng bộ ARItem cho 'xuất vật tư':
    - Tạo/Update khi là vật tư tiêu hao + có customer + số tiền > 0
    - Xoá khi không còn thỏa điều kiện hoặc số tiền <= 0
    """
    ARItem = apps.get_model('app_treatment', 'ARItem')
    ct = ContentType.objects.get_for_model(StockOut)

    qs = ARItem.objects.select_for_update().filter(content_type=ct, object_id=instance.id)

    # Điều kiện tạo công nợ: vật tư + có khách + có đơn giá
    is_consumable = getattr(instance.product, "product_type", None) == "consumable"
    has_customer = bool(instance.customer_id)
    amount = _stockout_amount(instance)

    if is_consumable and has_customer and amount > 0:
        if qs.exists():
            ar = qs.first()
            # đảm bảo đồng bộ KH & mô tả & số tiền
            ar.customer = instance.customer
            ar.description = "Xuất vật tư"
            ar.amount_original = amount
            ar.save(update_fields=["customer", "description", "amount_original"])
        else:
            ARItem.objects.create(
                customer=instance.customer,
                content_type=ct,
                object_id=instance.id,
                description="Xuất vật tư",
                amount_original=amount,
            )
    else:
        # Không thỏa điều kiện -> xoá AR nếu có
        qs.delete()

@receiver(post_save, sender=StockOut)
def stockout_post_save(sender, instance: StockOut, created, **kwargs):
    with transaction.atomic():
        _sync_ar_for_stockout(instance)

@receiver(post_delete, sender=StockOut)
def stockout_post_delete(sender, instance: StockOut, **kwargs):
    # Xoá ARItem gắn với StockOut bị xoá
    ARItem = apps.get_model('app_treatment', 'ARItem')
    ct = ContentType.objects.get_for_model(StockOut)
    ARItem.objects.filter(content_type=ct, object_id=instance.id).delete()

class TechicalSetting(models.Model):
    SERVICE_TYPE =[
        ('TLCB', 'Trị liệu chữa bệnh'),
        ('TLDS', 'Trị liệu dưỡng sinh'),
    ]
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(max_length=255)
    duration = models.PositiveIntegerField(null=True, blank=True)
    price = models.DecimalField(max_digits=25, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    type = models.CharField(max_length=20, choices=SERVICE_TYPE, null=True, blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        app_label = "app_product"

class ServiceTechnicalSetting(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='service_technical_settings')
    technical_setting = models.ForeignKey(TechicalSetting, on_delete=models.CASCADE, related_name='technical_services')

    class Meta:
        unique_together = ('service', 'technical_setting')
        app_label = "app_product"

    def __str__(self):
        return f"{self.service.name} - {self.technical_setting.name}"