# app_product/signals.py
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.db.models import F
from django.db import transaction

from .models import FacilityExport, Facility

@receiver(pre_save, sender=FacilityExport)
def facility_export_pre_save(sender, instance: FacilityExport, **kwargs):
    """
    Lưu lại trạng thái cũ để post_save dùng tính delta.
    """
    instance._old = None
    if instance.pk:
        try:
            instance._old = FacilityExport.objects.get(pk=instance.pk)
        except FacilityExport.DoesNotExist:
            instance._old = None


@receiver(post_save, sender=FacilityExport)
def facility_export_post_save(sender, instance: FacilityExport, created, **kwargs):
    """
    Tự động cập nhật tồn kho sau khi lưu.
    - created: trừ luôn số vừa xuất
    - update: tính delta (và xử lý đổi facility nếu có)
    Dùng F() để an toàn cạnh tranh và atomic cập nhật.
    """
    with transaction.atomic():
        if created:
            Facility.objects.filter(pk=instance.facility_id).update(
                quantity=F("quantity") - instance.quantity
            )
        else:
            old = getattr(instance, "_old", None)
            if old is None:
                # không có trạng thái cũ (hiếm), coi như tạo mới
                Facility.objects.filter(pk=instance.facility_id).update(
                    quantity=F("quantity") - instance.quantity
                )
                return

            if old.facility_id == instance.facility_id:
                # Cùng kho: trừ theo delta
                delta = instance.quantity - old.quantity  # >0: trừ thêm, <0: cộng bù
                if delta != 0:
                    Facility.objects.filter(pk=instance.facility_id).update(
                        quantity=F("quantity") - delta
                    )
            else:
                # Đổi kho: hoàn về kho cũ, trừ kho mới
                Facility.objects.filter(pk=old.facility_id).update(
                    quantity=F("quantity") + old.quantity
                )
                Facility.objects.filter(pk=instance.facility_id).update(
                    quantity=F("quantity") - instance.quantity
                )


@receiver(post_delete, sender=FacilityExport)
def facility_export_post_delete(sender, instance: FacilityExport, **kwargs):
    """
    Xóa phiếu xuất => cộng trả lại tồn kho.
    """
    with transaction.atomic():
        Facility.objects.filter(pk=instance.facility_id).update(
            quantity=F("quantity") + instance.quantity
        )

# signals_payment.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from app_product.models import ProductDebtDetail, FacilityDebtDetail

@receiver(post_save, sender=ProductDebtDetail)
@receiver(post_delete, sender=ProductDebtDetail)
def product_payment_update_stockin(sender, instance, **kwargs):
    if instance.stock_in_id:
        instance.stock_in.update_full_paid_status()

@receiver(post_save, sender=FacilityDebtDetail)
@receiver(post_delete, sender=FacilityDebtDetail)
def facility_payment_update_stockin(sender, instance, **kwargs):
    if instance.stock_in_id:
        instance.stock_in.update_full_paid_status()
