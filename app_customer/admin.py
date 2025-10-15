from django.contrib import admin
from django.utils.html import format_html
from django.contrib import admin
from .models import  CustomerRequest, LeadStatus, TreatmentState, Customer, CustomerCare, FeedBack, CustomerProblem,  customer_introducers
admin.site.site_header = 'Thabicare Admin'
admin.site.site_title = 'Quản Lý Hệ Thống'
admin.site.index_title = 'Quản Trị Hệ Thống'

class LeadStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'user', 'created',)
    list_filter = ('user','created')
    search_fields = ('name', 'user',)
class TreatmentStateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'user', 'created',)
    list_filter = ('user','created')
    search_fields = ('name', 'user',)
class CustomerCareInline(admin.TabularInline): 
    model = CustomerCare
    extra = 1 
class CustomerCareAdmin(admin.ModelAdmin):
    list_display = ('customer', 'type', 'date', 'note')
    list_filter = ('type', 'date')
    search_fields = ('customer__name', 'note')

class CustomerIntroducerInline(admin.TabularInline):
    model = customer_introducers
    extra = 1  # Số hàng trống mặc định để nhập mới

class CustomerProblemInline(admin.TabularInline):
    model = CustomerProblem
    extra = 1 

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'mobile', 'email', 'city', 'main_status', 'is_active')
    list_filter = ('main_status', 'is_active', 'city')
    search_fields = ('name', 'mobile', 'email')
    inlines = [CustomerIntroducerInline, CustomerCareInline, CustomerProblemInline]  # Thêm Inline mới

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'code',
                'name',
                'gender',
                'birth',
                'is_active',
                'customer_request'
            )
        }),
        ('Contact Information', {
            'fields': (
                'mobile',
                'email',
            )
        }),
        ('Address Details', {
            'fields': (
                'city',
                'district',
                'ward',
                'address',
            ),
            'classes': ('collapse',)
        }),
        ('Source Information', {
            'fields': (
                'source',
                'source_link',
                'marketer',
                'contact_date',
            )
        }),
        ('Status Information', {
            'fields': (
                'main_status',
                'lead_status',
                'treatment_status',
            ),
            'classes': ('wide',)
        }),
        ('Additional Information', {
            'fields': (
                'user',
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created',)

class FeedBackAdmin(admin.ModelAdmin):
    list_display = ('name', 'format', 'created', 'user','source','email','mobile','satification_level')
    list_filter = (
        'created',
        'format',
        'source',
        'gender',
        'satification_level',
        'service_quality',
        'examination_quality',
        'serve_quality',
        'customercare_quality'
    )
    
    search_fields = (
        'name',
        'email',
        'mobile',
        'unsatify_note',
        'suggest_note'
    )
    
    readonly_fields = ('created',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'user',
                'name',
                'gender',
                'email',
                'mobile',
                'created'
            )
        }),
        ('Source Information', {
            'fields': (
                'source',
                'source_link',
                'format'
            )
        }),
        ('Ratings', {
            'fields': (
                'satification_level',
                'service_quality',
                'examination_quality',
                'serve_quality',
                'customercare_quality'
            )
        }),
        ('Notes', {
            'fields': (
                'unsatify_note',
                'suggest_note'
            )
        }),
    )

admin.site.register(LeadStatus, LeadStatusAdmin)
admin.site.register(TreatmentState, TreatmentStateAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(CustomerCare, CustomerCareAdmin)
admin.site.register(FeedBack, FeedBackAdmin)
admin.site.register(CustomerRequest)

