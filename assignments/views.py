from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import Assignment, Submission
from .forms import AssignmentForm, SubmissionForm, GradingForm
from academics.models import Course, CourseEnrollment
from accounts.decorators import teacher_required, student_required
from activity_logs.models import log_activity, ActivityLog
from announcements.models import Notification


@login_required
def assignment_list_view(request):
    user = request.user
    status_filter = request.GET.get('status', '')
    course_filter = request.GET.get('course', '')

    if user.is_student_role and hasattr(user, 'student_profile'):
        # For students: get assignments for enrolled courses
        enrolled_courses = CourseEnrollment.objects.filter(
            student=user.student_profile, is_active=True
        ).values_list('course_id', flat=True)
        assignments = Assignment.objects.filter(
            course_id__in=enrolled_courses,
            status=Assignment.Status.PUBLISHED
        ).select_related('course', 'teacher__user')

        # Attach student submission to each assignment
        student_submissions = {
            s.assignment_id: s
            for s in Submission.objects.filter(student=user.student_profile)
        }
        for a in assignments:
            a.my_submission = student_submissions.get(a.id)

        user_courses = Course.objects.filter(id__in=enrolled_courses)

    elif user.is_teacher_role and hasattr(user, 'teacher_profile') and not user.is_admin_role:
        assignments = Assignment.objects.filter(
            teacher=user.teacher_profile
        ).select_related('course')
        user_courses = Course.objects.filter(teacher=user.teacher_profile)

    else:
        # Admin: see all
        assignments = Assignment.objects.all().select_related('course', 'teacher__user')
        user_courses = Course.objects.all()

    if course_filter:
        assignments = assignments.filter(course_id=course_filter)

    return render(request, 'assignments/assignment_list.html', {
        'assignments': assignments,
        'user_courses': user_courses,
        'selected_course': course_filter,
    })


@login_required
def assignment_detail_view(request, pk):
    assignment = get_object_or_404(Assignment.objects.select_related('course', 'teacher__user'), pk=pk)
    user = request.user

    submission = None
    submission_form = None
    all_submissions = []

    if user.is_student_role and hasattr(user, 'student_profile'):
        submission = Submission.objects.filter(assignment=assignment, student=user.student_profile).first()
        submission_form = SubmissionForm(instance=submission)

    elif user.is_teacher_role or user.is_admin_role:
        all_submissions = assignment.submissions.select_related('student__user').order_by('-submitted_at')

    return render(request, 'assignments/assignment_detail.html', {
        'assignment': assignment,
        'submission': submission,
        'submission_form': submission_form,
        'all_submissions': all_submissions,
        'now': timezone.now(),
    })


@teacher_required
def assignment_create_view(request):
    teacher = getattr(request.user, 'teacher_profile', None)
    if not teacher and not request.user.is_superuser:
        messages.error(request, "Teacher profile required to create assignments.")
        return redirect('assignment_list')

    form = AssignmentForm(request.POST or None, request.FILES or None, teacher=teacher)
    if request.method == 'POST' and form.is_valid():
        assignment = form.save(commit=False)
        if teacher:
            assignment.teacher = teacher
        elif not assignment.teacher:
            # Fallback for admin if creating
            first_teacher = assignment.course.teacher
            if first_teacher:
                assignment.teacher = first_teacher
        assignment.save()

        # Notify enrolled students
        enrolled_students = CourseEnrollment.objects.filter(course=assignment.course, is_active=True).select_related('student__user')
        for enrollment in enrolled_students:
            Notification.objects.create(
                recipient=enrollment.student.user,
                title=f"New Assignment: {assignment.title}",
                message=f"A new assignment for {assignment.course.code} has been published. Due date: {assignment.due_date:%b %d, %Y}.",
                link=f"/assignments/{assignment.id}/",
                notification_type=Notification.Type.ASSIGNMENT
            )

        log_activity(
            request=request,
            action=f"Created assignment: '{assignment.title}' for {assignment.course.code}",
            category=ActivityLog.Category.ASSIGNMENT
        )
        messages.success(request, f"Assignment '{assignment.title}' has been successfully published!")
        return redirect('assignment_detail', pk=assignment.pk)

    return render(request, 'assignments/assignment_form.html', {'form': form, 'title': 'Create New Assignment'})


@teacher_required
def assignment_edit_view(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    teacher = getattr(request.user, 'teacher_profile', None)

    # Allow editing only if teacher owns it or is admin
    if teacher and assignment.teacher != teacher and not request.user.is_admin_role:
        messages.error(request, "You can only edit assignments you created.")
        return redirect('assignment_detail', pk=assignment.pk)

    form = AssignmentForm(request.POST or None, request.FILES or None, instance=assignment, teacher=teacher)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_activity(
            request=request,
            action=f"Updated assignment: '{assignment.title}'",
            category=ActivityLog.Category.ASSIGNMENT
        )
        messages.success(request, f"Assignment '{assignment.title}' updated successfully.")
        return redirect('assignment_detail', pk=assignment.pk)

    return render(request, 'assignments/assignment_form.html', {'form': form, 'title': f'Edit Assignment: {assignment.title}'})


@student_required
def submission_submit_view(request, assignment_pk):
    assignment = get_object_or_404(Assignment, pk=assignment_pk)
    student = request.user.student_profile

    # Verify student is enrolled
    is_enrolled = CourseEnrollment.objects.filter(course=assignment.course, student=student, is_active=True).exists()
    if not is_enrolled:
        messages.error(request, "You are not enrolled in this course.")
        return redirect('assignment_list')

    submission, created = Submission.objects.get_or_create(assignment=assignment, student=student)

    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            sub = form.save(commit=False)
            is_late = timezone.now() > assignment.due_date
            sub.status = Submission.Status.LATE if is_late else Submission.Status.SUBMITTED
            sub.save()

            # Notify the teacher
            if assignment.teacher:
                Notification.objects.create(
                    recipient=assignment.teacher.user,
                    title=f"Submission received from {student.user.get_full_name()}",
                    message=f"{student.user.get_full_name()} submitted assignment '{assignment.title}' for {assignment.course.code}.",
                    link=f"/assignments/{assignment.id}/",
                    notification_type=Notification.Type.ASSIGNMENT
                )

            log_activity(
                request=request,
                action=f"Submitted assignment: '{assignment.title}' ({'Late' if is_late else 'On time'})",
                category=ActivityLog.Category.SUBMISSION
            )
            messages.success(request, "Your assignment was successfully submitted!")
    return redirect('assignment_detail', pk=assignment.pk)


@teacher_required
def submission_grade_view(request, submission_pk):
    submission = get_object_or_404(Submission.objects.select_related('assignment', 'student__user'), pk=submission_pk)
    teacher = getattr(request.user, 'teacher_profile', None)

    form = GradingForm(request.POST or None, instance=submission)
    if request.method == 'POST' and form.is_valid():
        graded = form.save(commit=False)
        graded.status = Submission.Status.GRADED
        graded.graded_at = timezone.now()
        graded.graded_by = teacher
        graded.save()

        # Notify the student
        Notification.objects.create(
            recipient=submission.student.user,
            title=f"Graded: {submission.assignment.title}",
            message=f"Your submission for '{submission.assignment.title}' has been evaluated. Score: {graded.marks_obtained}/{submission.assignment.max_marks}.",
            link=f"/assignments/{submission.assignment.id}/",
            notification_type=Notification.Type.GRADE
        )

        log_activity(
            request=request,
            action=f"Graded submission for {submission.student.user.get_full_name()} on '{submission.assignment.title}' ({graded.marks_obtained}/{submission.assignment.max_marks})",
            category=ActivityLog.Category.GRADING
        )
        messages.success(request, f"Successfully graded submission for {submission.student.user.get_full_name()}.")
        return redirect('assignment_detail', pk=submission.assignment.pk)

    return render(request, 'assignments/submission_grade.html', {
        'submission': submission,
        'form': form
    })
