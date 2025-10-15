from django.contrib import admin
from app_treatment.models import Bill, Booking, DoctorProcess, DoctorHealthCheck, ServiceAssign, SessionTechicalSetting, TreatmentRequest, TreatmentSession, diagnosis_medicine
# # Registering models to the admin site


class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'customer', 'has_come', 
        'is_treatment','type', 'created'
    )
    list_filter = ( 'has_come', 'is_treatment')
    search_fields = ('customer__name', 'customer__code', 'user__username', 'note')

class DoctorHealthCheckAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_booking_customer_name', 'get_booking_customer_code')
    search_fields = ('customer__code', 'customer__name')

    def get_booking_customer_name(self, obj):
        return obj.booking.customer.name if obj.booking and obj.booking.customer else "N/A"
    
    def get_booking_customer_code(self, obj):
        return obj.booking.customer.code if obj.booking and obj.booking.customer else "N/A"
    
    get_booking_customer_name.short_description = "Tên khách hàng"
    get_booking_customer_code.short_description = "Mã khách hàng"

class DiagnosisMedicineInline(admin.TabularInline):
    model = diagnosis_medicine
    extra = 1  # Cho phép thêm thuốc mới trực tiếp từ giao diện DoctorProcess


class DoctorProcessAdmin(admin.ModelAdmin):

    list_display = ('id','medicines_has_paid', 'total_amount', 'total_after_discount')
    list_filter = ('medicines_has_paid',)
    search_fields = ('booking__customer__name',)
    readonly_fields = ('total_amount', 'total_after_discount')
    inlines = [DiagnosisMedicineInline] 

    def total_amount(self, obj):

        return obj.total_amount()

    def total_after_discount(self, obj):
        return obj.total_after_discount()

    total_amount.short_description = "Tổng tiền thuốc"
    total_after_discount.short_description = "Tổng tiền sau giảm giá"

from django.contrib import admin
from .models import Bill, PaymentHistory, TreatmentRequest, TreatmentSession, SessionTechicalSetting

# Inline để hiển thị các treatment_request trong Bill
class TreatmentRequestInline(admin.TabularInline):
    model = TreatmentRequest
    extra = 1  # Hiển thị thêm 1 dòng trống để người dùng có thể thêm TreatmentRequest

# Inline để hiển thị các treatment_session trong TreatmentRequest
class TreatmentSessionInline(admin.TabularInline):
    model = TreatmentSession
    extra = 1  # Hiển thị thêm 1 dòng trống để người dùng có thể thêm TreatmentSession

class SessionTechicalSettingInline(admin.TabularInline):
    model = SessionTechicalSetting
    extra = 1  # Hiển thị thêm 1 dòng trống để người dùng có thể thêm SessionTechicalSetting

# Cấu hình hiển thị trong admin cho Bill
class BillAdmin(admin.ModelAdmin):
    list_display = ('id','code', 'created', 'user', 'customer', 'method', 'paid_ammount', 'fully_paid')
    inlines = [TreatmentRequestInline]  # Hiển thị TreatmentRequest trong Bill

class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('id','bill', 'paid_amount', 'paid_method', 'user', 'created')

class TreatmentRequestAdmin(admin.ModelAdmin):
    list_display = ('id','code', 'service', 'user', 'is_done', 'created_at')
    inlines = [TreatmentSessionInline]  # Hiển thị TreatmentSession trong TreatmentRequest

class TreatmentSessionAdmin(admin.ModelAdmin):
    list_display = ('id','treatment_request', 'is_done', 'note')
    inlines = [SessionTechicalSettingInline]

class SessionTechicalSettingAdmin(admin.ModelAdmin):
    list_display = ('id','session', 'techical_setting', 'calculate_expert_payment')




admin.site.register(Booking, BookingAdmin)
admin.site.register(DoctorHealthCheck, DoctorHealthCheckAdmin)
admin.site.register(DoctorProcess, DoctorProcessAdmin)
admin.site.register(ServiceAssign)
admin.site.register(Bill, BillAdmin)
admin.site.register(PaymentHistory, PaymentHistoryAdmin),
admin.site.register(TreatmentRequest, TreatmentRequestAdmin)
admin.site.register(TreatmentSession, TreatmentSessionAdmin)
admin.site.register(SessionTechicalSetting, SessionTechicalSettingAdmin)
