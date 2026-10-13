from django.contrib import admin
from .models import AttendanceSession, AttendanceRecord

admin.site.register(AttendanceSession)
admin.site.register(AttendanceRecord)
