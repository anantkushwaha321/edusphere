from django.db import models
from django.conf import settings


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=15, unique=True)
    description = models.TextField(blank=True, null=True)
    head_of_department = models.ForeignKey(
        'accounts.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def student_count(self):
        return self.students.count()

    @property
    def teacher_count(self):
        return self.teachers.count()

    @property
    def course_count(self):
        return self.courses.count()


class AcademicYear(models.Model):
    name = models.CharField(max_length=50)  # e.g., '2026-2027'
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        status = " (Current)" if self.is_current else ""
        return f"{self.name}{status}"

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    teacher = models.ForeignKey(
        'accounts.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_courses'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses'
    )
    semester = models.PositiveSmallIntegerField(default=1)
    credits = models.PositiveSmallIntegerField(default=3)
    description = models.TextField(blank=True, null=True)
    syllabus_file = models.FileField(upload_to='syllabi/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def active_enrollments_count(self):
        return self.enrollments.filter(is_active=True).count()


class CourseEnrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['course', 'student'], name='unique_course_enrollment')
        ]
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.roll_number} enrolled in {self.course.code}"
