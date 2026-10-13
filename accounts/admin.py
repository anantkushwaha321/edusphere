from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, TeacherProfile, AdminProfile


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('EduSphere Custom Fields', {
            'fields': ('role', 'phone', 'avatar', 'bio', 'address', 'gender', 'date_of_birth')
        }),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)
admin.site.register(AdminProfile)
