from django.db import models
from django.utils import timezone


class Assignment(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PUBLISHED = 'PUBLISHED', 'Published'
        CLOSED = 'CLOSED', 'Closed'

    course = models.ForeignKey('academics.Course', on_delete=models.CASCADE, related_name='assignments')
    teacher = models.ForeignKey('accounts.TeacherProfile', on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    attachment = models.FileField(upload_to='assignments/briefs/', blank=True, null=True)
    max_marks = models.PositiveIntegerField(default=100)
    due_date = models.DateTimeField()
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PUBLISHED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.course.code} - {self.title}"

    @property
    def is_past_due(self):
        return timezone.now() > self.due_date

    @property
    def total_submissions(self):
        return self.submissions.count()

    @property
    def total_graded(self):
        return self.submissions.filter(status=Submission.Status.GRADED).count()

    @property
    def pending_grading(self):
        return self.submissions.exclude(status=Submission.Status.GRADED).count()

    @property
    def average_score(self):
        graded = self.submissions.filter(status=Submission.Status.GRADED, marks_obtained__isnull=False)
        if not graded.exists():
            return None
        avg = graded.aggregate(models.Avg('marks_obtained'))['marks_obtained__avg']
        return round(avg, 1) if avg is not None else None


class Submission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        LATE = 'LATE', 'Submitted Late'
        GRADED = 'GRADED', 'Graded'
        RESUBMIT = 'RESUBMIT', 'Resubmission Requested'

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='submissions')
    file = models.FileField(upload_to='assignments/submissions/', blank=True, null=True)
    submission_text = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now=True)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.SUBMITTED)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(
        'accounts.TeacherProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['assignment', 'student'], name='unique_assignment_submission')
        ]
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.roll_number} - {self.assignment.title}"

    @property
    def percentage(self):
        if self.marks_obtained is not None and self.assignment.max_marks > 0:
            return round((float(self.marks_obtained) / float(self.assignment.max_marks)) * 100, 1)
        return None

    @property
    def letter_grade(self):
        pct = self.percentage
        if pct is None:
            return 'N/A'
        if pct >= 90:
            return 'A+'
        elif pct >= 80:
            return 'A'
        elif pct >= 70:
            return 'B'
        elif pct >= 60:
            return 'C'
        elif pct >= 50:
            return 'D'
        else:
            return 'F'
