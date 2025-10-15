from django.contrib import admin
from .models import FacilityExport, Service, Product, Facility, Maintenance, FixSchedule, ServiceTechnicalSetting, ServiceTreatmentPackage, Warehouse, Supplier, StockIn, StockOut,TechicalSetting

class ServiceTechnicalSettingInline(admin.TabularInline):
    model = ServiceTechnicalSetting
    extra = 0
    fields = ('technical_setting', )
class ServiceTreatmentPackageInline(admin.TabularInline):
    model = ServiceTreatmentPackage
    extra = 0
    fields = ('treatment_package', 'price')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name', 'user', 'type', 'status')
    list_filter = ('status',)
    search_fields = ('code', 'name')
    readonly_fields = ('created',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'status')
        }),
        ('Service Details', {
            'fields': ('description', 'type')
        }),
        ('System Fields', {
            'fields': ('created', 'user'),
            'classes': ('collapse',)
        }),
    )

    inlines = [ServiceTreatmentPackageInline, ServiceTechnicalSettingInline]
    def treatment_packages_display(self, obj):
        return ", ".join(
            f"{tp.treatment_package.name} ({tp.price})"
            for tp in obj.service_treatment_packages.all()
        )
    treatment_packages_display.short_description = "Gói liệu trình"

    list_display = ('id', 'code', 'name', 'user', 'type', 'status', 'treatment_packages_display')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','code', 'name', 'origin', 'sell_price', 'unit')
    list_filter = ('unit', 'origin')
    search_fields = ('code', 'name', 'description')
    readonly_fields = ('created',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'effect')
        }),
        ('Product Details', {
            'fields': ('origin', 'sell_price', 'unit')
        }),
        ('System Fields', {
            'fields': ('created', 'user'),
            'classes': ('collapse',)
        }),
    )

class MaintenanceInline(admin.TabularInline):
    model = Maintenance
    extra = 0
    readonly_fields = ('created',)
    fields = ('date', 'note', 'status', 'is_maintenanced', 'user')

class FixScheduleInline(admin.TabularInline):
    model = FixSchedule
    extra = 0
    readonly_fields = ('created',)
    fields = ('date', 'note', 'status', 'is_fixed', 'user')

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'origin', 'quantity', 'import_price', 'status', 'is_malfunction', 'unit')
    list_filter = ('status', 'is_malfunction', 'unit', 'origin')
    search_fields = ('name', 'effect', 'malfunction_status')
    readonly_fields = ('created', 'maintenance_count', 'fix_count')
    inlines = [MaintenanceInline, FixScheduleInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'origin', 'unit')
        }),
        ('Status & Condition', {
            'fields': ('status', 'is_malfunction', 'effect', 'malfunction_status')
        }),
        ('Inventory Details', {
            'fields': ('quantity', 'import_price')
        }),
        ('Statistics', {
            'fields': ('maintenance_count', 'fix_count'),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('created', 'user'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('id','facility', 'date', 'status', 'is_maintenanced')
    list_filter = ('status', 'is_maintenanced', 'date')
    search_fields = ('facility__name', 'note')
    readonly_fields = ('created',)
    fieldsets = (
        ('Maintenance Details', {
            'fields': ('facility', 'date', 'status', 'is_maintenanced', 'note')
        }),
        ('System Fields', {
            'fields': ('created', 'user'),
            'classes': ('collapse',)
        }),
    )

@admin.register(FixSchedule)
class FixScheduleAdmin(admin.ModelAdmin):
    list_display = ('id','facility', 'date', 'status', 'is_fixed')
    list_filter = ('status', 'is_fixed', 'date')
    search_fields = ('facility__name', 'note')
    readonly_fields = ('created',)
    fieldsets = (
        ('Fix Schedule Details', {
            'fields': ('facility', 'date', 'status', 'is_fixed', 'note')
        }),
        ('System Fields', {
            'fields': ('created', 'user'),
            'classes': ('collapse',)
        }),
    )

class WarehouseInline(admin.TabularInline):
    model = Warehouse
    extra = 1
    fields = ['product', 'quantity', 'import_date']
    raw_id_fields = ['product']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'mobile', 'email', 'contact_person', 'MST']
    search_fields = ['name', 'mobile', 'email', 'MST']
    list_filter = ['created']
    inlines = [WarehouseInline]
    readonly_fields = ['created','id']

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'supplier', 'product', 'quantity','import_date', 'export_date', 'user', 'created')
    list_filter = ('supplier', 'product', 'import_date', 'export_date')
    search_fields = ('code', 'supplier__name', 'product__name')
    readonly_fields = ('code', 'created')

@admin.register(StockIn)
class StockInAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'code', 
        'supplier', 
        'product', 
        'quantity', 
        'import_price', 
        'import_date', 
        'approver', 
        'user', 
        'is_active',
        'created'
    )
    list_filter = ('supplier', 'product',  'import_date', 'is_active')
    search_fields = ('code', 'supplier__name', 'product__name', 'approver__username', 'user__username')
    readonly_fields = ('code', 'created')
    ordering = ('-created',)
    fieldsets = (
        (None, {
            'fields': ('code', 'supplier', 'product', 'quantity', 'import_price', 'import_date', 'note')
        }),
        ('Additional Info', {
            'fields': ('approver', 'user', 'is_active', 'created'),
        }),
    )

@admin.register(StockOut)
class StockOutAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'code', 'product', 'supplier', 'quantity',
        'export_date', 'type', 'actual_stockout_price',
        'is_active', 'created', 'approver'
    )
    
    # Các trường có thể tìm kiếm
    search_fields = (
        'code', 'product__name', 'supplier__name',
        'approver__username'
    )
    
    # Bộ lọc bên phải
    list_filter = (
        'type', 'is_active', 'export_date',
    )
    
    # Sắp xếp mặc định
    ordering = ('-created',)
    # list_editable = ('is_active')
    readonly_fields = ('code', 'created', 'original_stockout_price')
    fieldsets = (
        ("Thông tin chung", {
            'fields': ('code', 'product', 'supplier', 'quantity', 'export_date', 'type', 'actual_stockout_price', 'original_stockout_price', 'note')
        }),
        ("Người dùng liên quan", {
            'fields': ('user', 'approver')
        }),
        ("Thông tin bổ sung", {
            'fields': ('is_active', 'actual_quantity', 'missing_reason')
        }),
    )


@admin.register(FacilityExport)
class FacilityExportAdmin(admin.ModelAdmin):
    list_display = ("id", "facility", "export_type", "quantity", "created_at", "created_by")
    list_filter = ("export_type", "created_at")
    search_fields = ("facility__code", "customer_name", "internal_department")
admin.site.register(TechicalSetting)