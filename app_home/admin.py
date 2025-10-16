from django.contrib import admin
from .models import FunctionCategory, Position, Department, Floor,\
    DetailFunction, TestService, TreatmentPackage, UserProfile, user_profile_detail_function,\
    Protocol, Commission, Discount, LeadSource, TimeFrame, Unit
    

class UserProfileDetailFunctionInline(admin.TabularInline):
    model = user_profile_detail_function
    extra = 1
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'detail_function':
            kwargs['queryset'] = DetailFunction.objects.filter(
                # Lọc chỉ những DetailFunction hợp lệ
                id__isnull=False
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
class PositionInline(admin.TabularInline):
    model = Position
    extra = 1
    readonly_fields = ('code',)
    fields = ('code', 'title', 'user')

class FunctionCategoryAdmin(admin.ModelAdmin):
    list_display = ['user','title','code',]
    search_fields = ['title', 'user__username', 'code']

class DetailFunctionAdmin(admin.ModelAdmin):
    list_display = ['id', 'category_title', 'code', 'title', 'link', 'function_default']
    search_fields = ['code', 'title', 'link', 'user__username' 'category__title']
    list_filter = ['category__title', 'function_default'] 
    ordering = ['code']

    def category_title(self, obj):
        if obj.category:
            return obj.category.title
        return "N/A"
    category_title.short_description = 'Category'

class PositionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user','title','code',]
    list_filter = ['created', 'code',]
    search_fields = ['title', 'user__username', 'code',]

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'code',]
    list_filter = ['created', 'code',]
    search_fields = ['name', 'user_username', 'code',]
    inlines = [PositionInline]

class FloorAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'code',]
    list_filter = ['created', 'code',]
    search_fields = ['name', 'user_username', 'code',]
    
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user','type','gender', 'user_mobile_number', 'user_address', 'is_admin',]
    list_filter = ['created', 'gender', 'is_admin', ]
    search_fields = ['user__username', 'user_mobile_number', 'user_address']
    inlines = (UserProfileDetailFunctionInline,)

class UserProfileDetailFunctionAdmin(admin.ModelAdmin):
    list_display = ['detail_function_title', 'is_active']
    list_filter = ['detail_function__title', 'is_active']
    def detail_function_title(self, obj):
        if obj.detail_function:
            return obj.detail_function.title
        return "N/A"
    
    detail_function_title.short_description = 'Detail Function Title'

class ProtocolAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'code', 'created',]
    list_filter = ['created', 'code',]
    search_fields = ['name', 'user__username', 'code',]

class CommissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'percentage','created',]
    list_filter = ['created', 'user',]
    search_fields = ['user__username',]

class DiscountAdmin(admin.ModelAdmin):
    list_display = ['id', 'name','rate', 'type', 'start_date', 'end_date',]
    list_filter = ['user', 'type', 'start_date', 'end_date',]
    search_fields = ['user__username', 'type', 'name',]

class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ['id', 'user','name',]
    list_filter = ['created',]
    search_fields = ['name', 'user__username',]

class TimeFrameAdmin(admin.ModelAdmin):
    list_display = ['id', 'start', 'end',]
    list_filter = ['start', 'end',]
    search_fields = ['start', 'end', 'user__username']

class UnitAdmin(admin.ModelAdmin):
    list_display = ['id', 'user','name',]
    list_filter = ['created',]
    search_fields = ['name', 'user__username',]

admin.site.register(FunctionCategory, FunctionCategoryAdmin)
admin.site.register(DetailFunction, DetailFunctionAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Floor, FloorAdmin)
admin.site.register(UserProfile, UserProfileAdmin)

admin.site.register(Protocol, ProtocolAdmin)
admin.site.register(Commission, CommissionAdmin)
admin.site.register(Discount, DiscountAdmin)
admin.site.register(LeadSource, LeadSourceAdmin)

admin.site.register(TimeFrame, TimeFrameAdmin)
admin.site.register(Unit, UnitAdmin)

admin.site.register(TreatmentPackage)
admin.site.register(TestService)
