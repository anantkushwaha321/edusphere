from django.contrib import admin
from .models import Department, AcademicYear, Course, CourseEnrollment

admin.site.register(Department)
admin.site.register(AcademicYear)
admin.site.register(Course)
admin.site.register(CourseEnrollment)
