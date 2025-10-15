from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from decimal import Decimal

from .models import PaymentHistory, TreatmentRequest, TreatmentSession

from app_customer.models import Customer  # hoặc nơi chứa model Customer

@receiver(post_save, sender=TreatmentSession)
def update_is_done_status(sender, instance, **kwargs):
    tr = instance.treatment_request
    # done khi KHÔNG còn session chưa done
    tr_is_done = not tr.treatment_sessions.filter(is_done=False).exists()
    if tr.is_done != tr_is_done:
        tr.is_done = tr_is_done
        tr.save(update_fields=['is_done'])

@receiver(post_save, sender=TreatmentRequest)
def update_customer_status_if_all_requests_done(sender, instance, **kwargs):
    bill = instance.bill
    if not bill or not bill.customer_id:
        return

    customer = bill.customer

    # Lấy tất cả phác đồ của khách hàng
    all_requests = TreatmentRequest.objects.filter(bill__customer=customer)

    if not all_requests.exists():
        return

    # nếu KHÔNG còn phác đồ nào chưa done
    all_done = not all_requests.filter(is_done=False).exists()
    new_status = '3' if all_done else '2'  # '3' = đã mua xong, '2' = đang mua

    if customer.main_status != new_status:
        customer.main_status = new_status
        customer.save(update_fields=['main_status'])