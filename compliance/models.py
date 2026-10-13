import uuid
from django.db import models
from django.conf import settings


class DataSubjectRequest(models.Model):
    class RequestType(models.TextChoices):
        ACCESS = 'ACCESS', 'Right of Access (GDPR Art. 15 / CCPA)'
        PORTABILITY = 'PORTABILITY', 'Data Export / Portability (GDPR Art. 20)'
        ERASURE = 'ERASURE', 'Right to Erasure / Account Deletion (GDPR Art. 17)'
        RECTIFICATION = 'RECTIFICATION', 'Data Rectification (GDPR Art. 16)'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Fulfilled & Closed'
        REJECTED = 'REJECTED', 'Declined (with Legal Justification)'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='data_subject_requests'
    )
    request_type = models.CharField(max_length=20, choices=RequestType.choices, default=RequestType.PORTABILITY)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reason = models.TextField(blank=True, null=True, help_text="Optional user explanation or context")
    admin_response = models.TextField(blank=True, null=True, help_text="Official institutional DPO response")
    requested_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    export_file = models.FileField(upload_to='compliance/exports/', blank=True, null=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"[{self.get_request_type_display()}] {self.user.username} ({self.get_status_display()})"


class EmailPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_preferences'
    )
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    academic_announcements = models.BooleanField(
        default=True,
        help_text="Essential academic circulars and examination updates"
    )
    assignment_alerts = models.BooleanField(
        default=True,
        help_text="Deadline alerts and new task releases"
    )
    grade_notifications = models.BooleanField(
        default=True,
        help_text="Alerts when a teacher posts a grade or remarks"
    )
    marketing_and_surveys = models.BooleanField(
        default=False,
        help_text="Strictly opt-in: Optional campus surveys, event promotions, newsletter"
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Email Preferences for {self.user.username}"


class CookieConsentLog(models.Model):
    session_id = models.CharField(max_length=128)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cookie_consents'
    )
    essential_accepted = models.BooleanField(default=True)
    functional_accepted = models.BooleanField(default=False)
    analytics_accepted = models.BooleanField(default=False)
    ip_anonymized = models.CharField(max_length=64, blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Consent Log {self.session_id[:8]} - {self.timestamp:%Y-%m-%d %H:%M}"


class ParentalConsentRecord(models.Model):
    student = models.ForeignKey(
        'accounts.StudentProfile',
        on_delete=models.CASCADE,
        related_name='parental_consents'
    )
    guardian_name = models.CharField(max_length=150)
    guardian_email = models.EmailField()
    guardian_phone = models.CharField(max_length=30, blank=True, null=True)
    consent_given = models.BooleanField(default=False)
    consent_method = models.CharField(
        max_length=50,
        default='ELECTRONIC_SIGNATURE',
        choices=[
            ('ELECTRONIC_SIGNATURE', 'Electronic Verification & Form'),
            ('SIGNED_DOCUMENT', 'Physical Signed Institutional Form'),
            ('VERIFIED_EMAIL', 'Verified Guardian Email Response')
        ]
    )
    consent_date = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    verification_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-consent_date']

    def __str__(self):
        return f"Parental Consent for {self.student.user.get_full_name()} by {self.guardian_name}"
