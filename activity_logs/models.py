from django.db import models
from django.conf import settings


class ActivityLog(models.Model):
    class Category(models.TextChoices):
        AUTH = 'AUTH', 'Authentication'
        ASSIGNMENT = 'ASSIGNMENT', 'Assignment'
        SUBMISSION = 'SUBMISSION', 'Submission'
        GRADING = 'GRADING', 'Grading'
        ATTENDANCE = 'ATTENDANCE', 'Attendance'
        MATERIAL = 'MATERIAL', 'Study Material'
        ANNOUNCEMENT = 'ANNOUNCEMENT', 'Announcement'
        ADMIN = 'ADMIN', 'Administration'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.ADMIN)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        user_name = self.user.username if self.user else "Anonymous"
        return f"[{self.category}] {user_name}: {self.action} ({self.timestamp:%Y-%m-%d %H:%M})"


def log_activity(request=None, user=None, action="", category=ActivityLog.Category.ADMIN, details=""):
    """Helper utility to log audit activity from any view or signal."""
    actor = user
    ip = None
    if request:
        if not actor and request.user.is_authenticated:
            actor = request.user
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', None))
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()

    try:
        ActivityLog.objects.create(
            user=actor,
            action=action,
            category=category,
            ip_address=ip,
            details=details
        )
    except Exception:
        # Don't let logging failures crash user workflows
        pass
