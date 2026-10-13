from django.contrib import admin
from .models import DataSubjectRequest, EmailPreference, CookieConsentLog, ParentalConsentRecord

@admin.register(DataSubjectRequest)
class DataSubjectRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'request_type', 'status', 'requested_at', 'resolved_at')
    list_filter = ('request_type', 'status', 'requested_at')
    search_fields = ('user__username', 'user__email', 'reason')

@admin.register(EmailPreference)
class EmailPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'academic_announcements', 'assignment_alerts', 'grade_notifications', 'marketing_and_surveys', 'updated_at')
    list_filter = ('marketing_and_surveys', 'academic_announcements')
    search_fields = ('user__username', 'user__email')

@admin.register(CookieConsentLog)
class CookieConsentLogAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'user', 'essential_accepted', 'functional_accepted', 'analytics_accepted', 'timestamp')
    list_filter = ('functional_accepted', 'analytics_accepted')

@admin.register(ParentalConsentRecord)
class ParentalConsentRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'guardian_name', 'guardian_email', 'consent_given', 'consent_date')
    search_fields = ('student__roll_number', 'guardian_name', 'guardian_email')
