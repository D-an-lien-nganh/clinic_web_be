from decimal import Decimal
from django.db import models
from django.conf import settings
from django.db.models import Sum
from django.core.exceptions import ValidationError
from app_home.models import generate_random_code

# ----------------- DEBT: PRODUCT -----------------
class SupplierProductDebt(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    supplier= models.ForeignKey('app_product.Supplier', on_delete=models.CASCADE, verbose_name="Nhà cung cấp")
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Tổng nợ sản phẩm")

    class Meta:
        app_label = "app_product"
        verbose_name = "Công nợ sản phẩm"
        verbose_name_plural = "Công nợ sản phẩm"

    def __str__(self):
        return f"ProductDebt - {self.supplier.name}"

    def get_total_paid(self):
        return ProductDebtDetail.objects.filter(stock_in__supplier=self.supplier).aggregate(
            s=Sum("paid_amount")
        )["s"] or Decimal("0")

    def get_remaining(self):
        return max(self.total_amount - self.get_total_paid(), 0)


class ProductDebtDetail(models.Model):
    PAID_METHOD = [("cash", "Tiền mặt"), ("transfer", "Chuyển khoản")]
    created     = models.DateTimeField(auto_now_add=True)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    code        = models.CharField(max_length=20, unique=True, null=True, blank=True)
    method      = models.CharField(max_length=25, choices=PAID_METHOD, default="cash")
    stock_in    = models.ForeignKey("app_product.StockIn", on_delete=models.CASCADE)  # phải là StockIn product
    paid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    note        = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "app_product"
        verbose_name = "Chi tiết thanh toán sản phẩm"
        verbose_name_plural = "Chi tiết thanh toán sản phẩm"

    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                new_code = generate_random_code()
                if not ProductDebtDetail.objects.filter(code=new_code).exists():
                    self.code = new_code
                    break
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.paid_amount <= 0:
            raise ValidationError("Số tiền phải > 0")
        if not self.stock_in.product_id or self.stock_in.facility_id:
            raise ValidationError("DebtDetail sản phẩm yêu cầu StockIn có product và không có facility")


# ----------------- DEBT: FACILITY -----------------
class SupplierFacilityDebt(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    supplier= models.ForeignKey('app_product.Supplier', on_delete=models.CASCADE, verbose_name="Nhà cung cấp")
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0, verbose_name="Tổng nợ vật tư")

    class Meta:
        app_label = "app_product"
        verbose_name = "Công nợ vật tư"
        verbose_name_plural = "Công nợ vật tư"

    def __str__(self):
        return f"FacilityDebt - {self.supplier.name}"

    def get_total_paid(self):
        return FacilityDebtDetail.objects.filter(stock_in__supplier=self.supplier).aggregate(
            s=Sum("paid_amount")
        )["s"] or Decimal("0")

    def get_remaining(self):
        return max(self.total_amount - self.get_total_paid(), 0)


class FacilityDebtDetail(models.Model):
    PAID_METHOD = [("cash", "Tiền mặt"), ("transfer", "Chuyển khoản")]
    created     = models.DateTimeField(auto_now_add=True)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    code        = models.CharField(max_length=20, unique=True, null=True, blank=True)
    method      = models.CharField(max_length=25, choices=PAID_METHOD, default="cash")
    stock_in    = models.ForeignKey("app_product.StockIn", on_delete=models.CASCADE)  # phải là StockIn facility
    paid_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    note        = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "app_product"
        verbose_name = "Chi tiết thanh toán vật tư"
        verbose_name_plural = "Chi tiết thanh toán vật tư"

    def save(self, *args, **kwargs):
        if not self.code:
            while True:
                new_code = generate_random_code()
                if not FacilityDebtDetail.objects.filter(code=new_code).exists():
                    self.code = new_code
                    break
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        if self.paid_amount <= 0:
            raise ValidationError("Số tiền phải > 0")
        if not self.stock_in.facility_id or self.stock_in.product_id:
            raise ValidationError("DebtDetail vật tư yêu cầu StockIn có facility và không có product")
