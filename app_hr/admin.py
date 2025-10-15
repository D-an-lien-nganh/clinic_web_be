from django.contrib import admin
from .models import HrUserProfile

@admin.register(HrUserProfile)
class HrUserProfileAdmin(admin.ModelAdmin):
    # Các trường hiển thị trong danh sách
    list_display = [
        'id', 
        'user_profile', 
        'contract_type', 
        'contract_status', 
        'contract_start', 
        'contract_end', 
        'level', 
        'calculate_seniority_display'
    ]
    # Các trường có thể tìm kiếm
    search_fields = ['user__username', 'user_profile__user__username', 'contract_type']
    # Các bộ lọc bên phải
    list_filter = ['contract_type', 'contract_status', 'contract_start', 'contract_end']
    # Các trường hiển thị trong form chỉnh sửa
    fields = [
        'user_profile', 
        'contract', 
        'contract_type', 
        'contract_status', 
        'contract_start', 
        'contract_end', 
        'start_date', 
        'level'
    ]
    # Chỉ đọc một số trường
    readonly_fields = ['created', 'calculate_seniority_display']

    def calculate_seniority_display(self, obj):
        """
        Hiển thị thâm niên trong admin.
        """
        return obj.calculate_seniority()
    
    calculate_seniority_display.short_description = "Thâm niên"
