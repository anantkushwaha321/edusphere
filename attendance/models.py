from django.db import models


class AttendanceSession(models.Model):
    course = models.ForeignKey('academics.Course', on_delete=models.CASCADE, related_name='attendance_sessions')
    date = models.DateField()
    taken_by = models.ForeignKey(
        'accounts.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_sessions'
    )
    topic_covered = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['course', 'date'], name='unique_course_date_attendance')
        ]
        ordering = ['-date']

    def __str__(self):
        return f"{self.course.code} Attendance - {self.date}"

    @property
    def total_records(self):
        return self.records.count()

    @property
    def present_count(self):
        return self.records.filter(status=AttendanceRecord.Status.PRESENT).count()

    @property
    def absent_count(self):
        return self.records.filter(status=AttendanceRecord.Status.ABSENT).count()

    @property
    def present_percentage(self):
        total = self.total_records
        if total == 0:
            return 0
        return round((self.present_count / total) * 100, 1)


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LATE = 'LATE', 'Late'
        EXCUSED = 'EXCUSED', 'Excused'

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    remarks = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['session', 'student'], name='unique_session_student_attendance')
        ]
        ordering = ['student__roll_number']

    def __str__(self):
        return f"{self.student.roll_number} - {self.session.date} ({self.get_status_display()})"
