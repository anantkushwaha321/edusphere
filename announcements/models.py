from django.db import models
from django.conf import settings


class Announcement(models.Model):
    class Audience(models.TextChoices):
        ALL = 'ALL', 'All (Campus-wide)'
        STUDENTS = 'STUDENTS', 'Students Only'
        TEACHERS = 'TEACHERS', 'Faculty Only'
        DEPARTMENT = 'DEPARTMENT', 'Specific Department'

    class Priority(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        IMPORTANT = 'IMPORTANT', 'Important'
        URGENT = 'URGENT', 'Urgent Notice'

    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='announcements')
    target_audience = models.CharField(max_length=20, choices=Audience.choices, default=Audience.ALL)
    department = models.ForeignKey(
        'academics.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='announcements'
    )
    priority = models.CharField(max_length=15, choices=Priority.choices, default=Priority.NORMAL)
    attachment = models.FileField(upload_to='announcements/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.priority}] {self.title}"


class Notification(models.Model):
    class Type(models.TextChoices):
        ASSIGNMENT = 'ASSIGNMENT', 'Assignment'
        GRADE = 'GRADE', 'Grade'
        ATTENDANCE = 'ATTENDANCE', 'Attendance'
        ANNOUNCEMENT = 'ANNOUNCEMENT', 'Announcement'
        SYSTEM = 'SYSTEM', 'System'

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    notification_type = models.CharField(max_length=20, choices=Type.choices, default=Type.SYSTEM)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient.username}: {self.title}"
