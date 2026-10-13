from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        TEACHER = 'TEACHER', 'Teacher'
        STUDENT = 'STUDENT', 'Student'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        blank=True,
        null=True
    )
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        full_name = self.get_full_name()
        return f"{full_name} ({self.username}) - {self.get_role_display()}" if full_name else f"{self.username} - {self.get_role_display()}"

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_teacher_role(self):
        return self.role == self.Role.TEACHER

    @property
    def is_student_role(self):
        return self.role == self.Role.STUDENT

    def get_profile(self):
        if self.role == self.Role.STUDENT and hasattr(self, 'student_profile'):
            return self.student_profile
        elif self.role == self.Role.TEACHER and hasattr(self, 'teacher_profile'):
            return self.teacher_profile
        elif self.role == self.Role.ADMIN and hasattr(self, 'admin_profile'):
            return self.admin_profile
        return None


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_number = models.CharField(max_length=30, unique=True)
    admission_number = models.CharField(max_length=30, unique=True, blank=True, null=True)
    department = models.ForeignKey(
        'academics.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    academic_year = models.ForeignKey(
        'academics.AcademicYear',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )
    current_semester = models.PositiveSmallIntegerField(default=1)
    guardian_name = models.CharField(max_length=100, blank=True, null=True)
    guardian_phone = models.CharField(max_length=20, blank=True, null=True)
    parent_email = models.EmailField(blank=True, null=True, help_text="Required for students under legal age")
    is_minor = models.BooleanField(default=False, help_text="True if student is under 18 years of age")
    parental_consent_verified = models.BooleanField(
        default=False,
        help_text="Required under COPPA (<13) and GDPR Article 8 (<16) before non-essential data processing"
    )
    parental_consent_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Student: {self.user.get_full_name() or self.user.username} ({self.roll_number})"


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=30, unique=True)
    department = models.ForeignKey(
        'academics.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teachers'
    )
    designation = models.CharField(max_length=100, default='Assistant Professor')
    qualifications = models.CharField(max_length=200, blank=True, null=True)
    joining_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Teacher: {self.user.get_full_name() or self.user.username} ({self.employee_id})"


class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    staff_id = models.CharField(max_length=30, unique=True, blank=True, null=True)
    designation = models.CharField(max_length=100, default='Academic Administrator')

    def __str__(self):
        return f"Admin: {self.user.get_full_name() or self.user.username}"


class EmailOTPChallenge(models.Model):
    class Purpose(models.TextChoices):
        LOGIN = 'LOGIN', 'Account Login'
        REGISTER = 'REGISTER', 'User Registration'

    email = models.EmailField(db_index=True)
    otp_hash = models.CharField(max_length=255)
    purpose = models.CharField(max_length=15, choices=Purpose.choices, default=Purpose.LOGIN)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='otp_challenges')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_used', 'expires_at']),
        ]

    def __str__(self):
        return f"OTP for {self.email} ({self.purpose}) - {'Used' if self.is_used else 'Active'}"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

    @property
    def is_valid_challenge(self):
        return not self.is_used and not self.is_expired and self.attempts < self.max_attempts

    def verify(self, plain_otp: str, mark_used: bool = True) -> bool:
        from django.contrib.auth.hashers import check_password
        if not self.is_valid_challenge:
            return False

        self.attempts += 1
        is_match = check_password(str(plain_otp).strip(), self.otp_hash)
        if is_match:
            self.is_verified = True
            if mark_used:
                self.is_used = True
                self.save(update_fields=['attempts', 'is_verified', 'is_used'])
            else:
                self.save(update_fields=['attempts', 'is_verified'])
            return True
        else:
            self.save(update_fields=['attempts'])
            return False

