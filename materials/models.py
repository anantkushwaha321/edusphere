import os
from django.db import models


class StudyMaterial(models.Model):
    course = models.ForeignKey('academics.Course', on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    unit_module = models.CharField(max_length=100, default='Module 1')
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='study_materials/', blank=True, null=True)
    external_link = models.URLField(blank=True, null=True)
    uploaded_by = models.ForeignKey(
        'accounts.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_materials'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    download_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.course.code} - {self.title}"

    @property
    def file_extension(self):
        if self.file:
            return os.path.splitext(self.file.name)[1].lower().replace('.', '')
        return 'link' if self.external_link else 'file'

    @property
    def file_name(self):
        if self.file:
            return os.path.basename(self.file.name)
        return ''
