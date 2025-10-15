import os
from django.conf import settings
from io import BytesIO
from PIL import Image
from django.db import models
from django.template.defaultfilters import slugify
import random, string
from datetime import date
from colorfield.fields import ColorField

from .custom_storage import MediaStorage
s3_storage = MediaStorage()

def today():
    return date.today()
# for setting up profileprofile
GENDER_TYPE_CHOICES = (
    ('MA', 'Nam'),
    ('FE', 'Nữ'),
    ('OT', 'Khác'),
)
USER_PROFILE_TYPE = (
    ('employee', 'Nhân viên'),
    ('collaborator', 'Cộng tác viên')
)
# for discount purposepurpose
DISCOUNT_TYPE = (
    ('percentage', 'Phần trăm'),
    ('fixed', 'Số tiền'),
)
def generate_random_code(min_length=6, max_length=10):
    length = random.randint(min_length, max_length)
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))

def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = filename + str(''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
    filename = "%s.%s" % (slugify(filename), ext)
    return os.path.join(instance.directory_string_var, filename)

def get_file_path2(instance, filename2):
    ext = filename2.split('.')[-1]
    filename2 = filename2 + str(''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
    filename2 = "%s.%s" % (slugify(filename2), ext)
    return os.path.join(instance.directory_string_var2, filename2)

# Create your models here

# --------------------------- User Related --------------------------------------------
class FunctionCategory(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField(max_length=250, unique=True)
    title = models.CharField(max_length=250)
    desc = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title}"

    class Meta:
        app_label = "app_home"

class DetailFunction(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(FunctionCategory, on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField(max_length=250, unique=True)
    title = models.CharField(max_length=250)
    link = models.CharField(max_length=250)
    desc = models.TextField(null=True, blank=True)
    function_default =  models.BooleanField(default=False)
    def __str__(self):
        return f"{self.code}|{self.title}"

    class Meta:
        app_label = "app_home"

class Department(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    note = models.TextField(null=True,blank=True)

    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        app_label = "app_home"

class Position(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField(max_length=50, verbose_name="Mã chức vụ")
    title = models.CharField(max_length=255, verbose_name="Tên chức vụ")
    performance_coefficient = models.FloatField(default=0)

    def __str__(self):
        return f"{self.code}|{self.title}"  
    
    class Meta:
        app_label = "app_home"
    
class Floor(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    note = models.TextField(null=True,blank=True)

    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        app_label = "app_home"

class UserProfile(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_profile')
    gender = models.CharField(choices=GENDER_TYPE_CHOICES, max_length=2, null=True, blank=True)
    user_mobile_number = models.CharField(max_length=20, null=True, blank=True)
    user_address = models.CharField(max_length=250, null=True, blank=True)
    image = models.ImageField(upload_to=get_file_path, null=True, blank=True)
    directory_string_var = "THABICARE/app_home/userprofile/"
    desc = models.TextField(null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_position')
    floor = models.ForeignKey(Floor, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_floor')
    detail_function = models.ManyToManyField(DetailFunction, through="user_profile_detail_function")

    type = models.CharField(choices=USER_PROFILE_TYPE, max_length=100, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user}|{self.is_admin}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        memfile = BytesIO()
        if self.image:
            img = Image.open(self.image)
            if img.height > 500 or img.width > 800:
                output_size = (800, 500)
                img.thumbnail(output_size, Image.ANTIALIAS)
                picture_format = self.image.name.split('.')[-1]
                if picture_format == "jpg":
                    img.save(memfile, "JPEG", quality=100)
                    s3_storage.save(self.image.name, memfile)
                    memfile.close()
                    img.close()
                elif picture_format == "png":
                    img.save(memfile, "PNG", quality=100)
                    s3_storage.save(self.image.name, memfile)
                    memfile.close()
                    img.close()
                else:
                    pass

    class Meta:
        app_label = "app_home"

    @property
    def introduced_customer_count(self):
        from app_customer.models import Customer
        return Customer.objects.filter(introducers=self.user).count()    
class user_profile_detail_function(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    detail_function = models.ForeignKey(DetailFunction, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "app_home"
        unique_together = ("user_profile", "detail_function")


# -------------------------------------- Other Settings ---------------------------
class Protocol(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=100, null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.code}|{self.name}"
    
    class Meta:
        app_label = "app_home"

class Commission(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    percentage = models.PositiveSmallIntegerField()
    note = models.TextField(null=True,blank=True)

    def __str__(self):
        return f"{self.percentage}%"
    
    class Meta:
        app_label = "app_home"

class Discount(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255,unique=True, blank=True, null=True)
    type = models.CharField(max_length=50, choices=DISCOUNT_TYPE)
    rate = models.PositiveIntegerField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    note = models.TextField(null=True,blank=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_random_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        app_label = "app_home"

class LeadSource(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    color = ColorField(default='#0D6EFD')
    note = models.TextField(null=True, blank=True)
    is_fixed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"

    def delete(self, *args, **kwargs):
        if self.is_fixed:
            raise models.ProtectedError("Không thể xóa nguồn khách hàng cố định", self)
        super().delete(*args, **kwargs)

    class Meta:
        app_label = "app_home"


class LeadSourceActor(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    source = models.ForeignKey('LeadSource', on_delete=models.CASCADE, related_name='actors')
    name = models.CharField(max_length=255)                     # tên actor (hiển thị báo cáo)
    code = models.CharField(max_length=50, db_index=True, null=True, blank=True)   # mã nội bộ
    external_id = models.CharField(max_length=100, null=True, blank=True)          # mã ngoài (ad account, booth id, ...)
    hr_profile = models.ForeignKey('app_hr.HrUserProfile', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='leadsource_actors')
    note = models.TextField(null=True, blank=True)

    class Meta:
        app_label = "app_home"
        unique_together = [('source', 'name')]
        indexes = [
            models.Index(fields=['source']),
            models.Index(fields=['code']),
            models.Index(fields=['external_id']),
        ]

    def __str__(self):
        return f"{self.source.name} | {self.name}"

class TimeFrame(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    start = models.TimeField()
    end = models.TimeField()
    note = models.TextField(null=True,blank=True)

    def __str__(self):
        return f"{self.start} - {self.end}"
    
    class Meta:
        app_label = "app_home"

class Unit(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    color = ColorField(default='#0D6EFD')
    note = models.TextField(null=True,blank=True)

    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        app_label = "app_home"


# cài đặt gói liệu trình
class TreatmentPackage(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Gói liệu trình")
    value = models.PositiveIntegerField(default=0)
    note = models.TextField(blank=True, verbose_name="Ghi chú")

    def __str__(self):
        return self.name

# cài đặt dịch vụ xét nghiệm
class TestService(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Mã dịch vụ")
    name = models.CharField(max_length=255, verbose_name="Tên dịch vụ")
    note = models.TextField(blank=True, verbose_name="Mô tả")

    def __str__(self):
        return self.name
