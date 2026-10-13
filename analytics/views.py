import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Avg, Count, Q

from accounts.models import User, StudentProfile, TeacherProfile
from academics.models import Department, Course, CourseEnrollment, AcademicYear
from assignments.models import Assignment, Submission
from attendance.models import AttendanceSession, AttendanceRecord
from announcements.models import Announcement
from activity_logs.models import ActivityLog
from accounts.decorators import admin_required, teacher_required, student_required


@login_required
def dashboard_view(request):
    """Router that sends users to their role-specific dashboard."""
    if request.user.is_admin_role:
        return redirect('admin_dashboard')
    elif request.user.is_teacher_role:
        return redirect('teacher_dashboard')
    elif request.user.is_student_role:
        return redirect('student_dashboard')
    return redirect('login')


@admin_required
def admin_dashboard_view(request):
    total_students = StudentProfile.objects.count()
    total_teachers = TeacherProfile.objects.count()
    total_courses = Course.objects.filter(is_active=True).count()
    total_departments = Department.objects.count()

    total_attendance_records = AttendanceRecord.objects.count()
    present_records = AttendanceRecord.objects.filter(status=AttendanceRecord.Status.PRESENT).count()
    campus_attendance_pct = round((present_records / total_attendance_records * 100), 1) if total_attendance_records > 0 else 0

    recent_activities = ActivityLog.objects.select_related('user').all()[:8]
    recent_announcements = Announcement.objects.select_related('author').all()[:5]

    # Department student distribution for Chart.js
    departments = Department.objects.annotate(student_count=Count('students')).values('name', 'student_count')
    dept_names = [d['name'] for d in departments]
    dept_counts = [d['student_count'] for d in departments]

    # Course stats
    courses = Course.objects.select_related('department', 'teacher__user').annotate(
        enrollment_count=Count('enrollments')
    )[:6]

    return render(request, 'analytics/admin_dashboard.html', {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_courses': total_courses,
        'total_departments': total_departments,
        'campus_attendance_pct': campus_attendance_pct,
        'recent_activities': recent_activities,
        'recent_announcements': recent_announcements,
        'dept_names': dept_names,
        'dept_counts': dept_counts,
        'courses': courses,
    })


@teacher_required
def teacher_dashboard_view(request):
    teacher = getattr(request.user, 'teacher_profile', None)
    if not teacher and request.user.is_superuser:
        teacher = TeacherProfile.objects.first()

    assigned_courses = Course.objects.filter(teacher=teacher, is_active=True) if teacher else Course.objects.none()
    course_ids = assigned_courses.values_list('id', flat=True)

    # Submissions pending grading
    pending_submissions = Submission.objects.filter(
        assignment__course_id__in=course_ids,
        status__in=[Submission.Status.SUBMITTED, Submission.Status.LATE]
    ).select_related('assignment__course', 'student__user').order_by('-submitted_at')[:8]

    pending_count = Submission.objects.filter(
        assignment__course_id__in=course_ids,
        status__in=[Submission.Status.SUBMITTED, Submission.Status.LATE]
    ).count()

    # Active assignments count
    active_assignments_count = Assignment.objects.filter(
        teacher=teacher,
        status=Assignment.Status.PUBLISHED,
        due_date__gte=timezone.now()
    ).count() if teacher else 0

    recent_sessions = AttendanceSession.objects.filter(
        course_id__in=course_ids
    ).select_related('course').order_by('-date')[:5]

    announcements = Announcement.objects.filter(is_active=True)[:5]

    return render(request, 'analytics/teacher_dashboard.html', {
        'teacher': teacher,
        'assigned_courses': assigned_courses,
        'pending_submissions': pending_submissions,
        'pending_count': pending_count,
        'active_assignments_count': active_assignments_count,
        'recent_sessions': recent_sessions,
        'announcements': announcements,
    })


@student_required
def student_dashboard_view(request):
    student = request.user.student_profile
    enrollments = CourseEnrollment.objects.filter(
        student=student, is_active=True
    ).select_related('course__teacher__user', 'course__department')

    course_ids = [e.course_id for e in enrollments]

    # Upcoming Assignments
    upcoming_assignments = Assignment.objects.filter(
        course_id__in=course_ids,
        status=Assignment.Status.PUBLISHED,
        due_date__gte=timezone.now()
    ).select_related('course').order_by('due_date')[:6]

    submitted_assignment_ids = Submission.objects.filter(student=student).values_list('assignment_id', flat=True)
    for a in upcoming_assignments:
        a.is_submitted = a.id in submitted_assignment_ids

    # Recent graded submissions
    recent_grades = Submission.objects.filter(
        student=student,
        status=Submission.Status.GRADED
    ).select_related('assignment__course').order_by('-graded_at')[:5]

    # Attendance calculation
    total_records = AttendanceRecord.objects.filter(student=student).count()
    present_records = AttendanceRecord.objects.filter(
        student=student,
        status__in=[AttendanceRecord.Status.PRESENT, AttendanceRecord.Status.LATE]
    ).count()
    attendance_pct = round((present_records / total_records * 100), 1) if total_records > 0 else 100.0

    announcements = Announcement.objects.filter(is_active=True)[:5]

    return render(request, 'analytics/student_dashboard.html', {
        'student': student,
        'enrollments': enrollments,
        'upcoming_assignments': upcoming_assignments,
        'recent_grades': recent_grades,
        'attendance_pct': attendance_pct,
        'announcements': announcements,
    })


@login_required
def student_report_card_view(request, student_id=None):
    """Detailed academic marksheet & performance report."""
    if student_id and (request.user.is_admin_role or request.user.is_teacher_role):
        student = get_object_or_404(StudentProfile.objects.select_related('user', 'department', 'academic_year'), pk=student_id)
    else:
        if not hasattr(request.user, 'student_profile'):
            messages.error(request, "Student profile not found.")
            return redirect('dashboard')
        student = request.user.student_profile

    enrollments = CourseEnrollment.objects.filter(student=student, is_active=True).select_related('course__teacher__user')

    course_reports = []
    total_credits = 0
    total_weighted_points = 0.0

    for enrollment in enrollments:
        course = enrollment.course
        # Submissions for this course
        submissions = Submission.objects.filter(
            student=student,
            assignment__course=course,
            status=Submission.Status.GRADED
        ).select_related('assignment')

        total_obtained = sum(float(s.marks_obtained or 0) for s in submissions)
        total_possible = sum(float(s.assignment.max_marks) for s in submissions)
        percentage = round((total_obtained / total_possible * 100), 1) if total_possible > 0 else 0.0

        # Letter grade & GPA point
        if percentage >= 90:
            grade, point = 'A+', 4.0
        elif percentage >= 80:
            grade, point = 'A', 3.7
        elif percentage >= 70:
            grade, point = 'B', 3.0
        elif percentage >= 60:
            grade, point = 'C', 2.0
        elif percentage >= 50:
            grade, point = 'D', 1.0
        else:
            grade, point = 'F', 0.0

        # Attendance for course
        course_records = AttendanceRecord.objects.filter(student=student, session__course=course).count()
        present_count = AttendanceRecord.objects.filter(
            student=student,
            session__course=course,
            status__in=[AttendanceRecord.Status.PRESENT, AttendanceRecord.Status.LATE]
        ).count()
        att_pct = round((present_count / course_records * 100), 1) if course_records > 0 else 100.0

        course_reports.append({
            'course': course,
            'submissions': submissions,
            'percentage': percentage,
            'grade': grade,
            'point': point,
            'attendance_pct': att_pct,
            'is_att_low': att_pct < 75.0,
        })

        total_credits += course.credits
        total_weighted_points += (point * course.credits)

    gpa = round(total_weighted_points / total_credits, 2) if total_credits > 0 else 0.0

    return render(request, 'analytics/student_report_card.html', {
        'student': student,
        'course_reports': course_reports,
        'total_credits': total_credits,
        'gpa': gpa,
        'report_date': timezone.now(),
    })


@teacher_required
def course_gradebook_view(request, course_id):
    course = get_object_or_404(Course.objects.select_related('teacher__user', 'department'), pk=course_id)
    assignments = course.assignments.filter(status__in=[Assignment.Status.PUBLISHED, Assignment.Status.CLOSED]).order_by('due_date')
    enrollments = course.enrollments.filter(is_active=True).select_related('student__user').order_by('student__roll_number')

    gradebook_rows = []
    for enrollment in enrollments:
        student = enrollment.student
        scores = {}
        total_obtained = 0.0
        total_possible = 0.0

        for a in assignments:
            sub = Submission.objects.filter(assignment=a, student=student).first()
            if sub and sub.status == Submission.Status.GRADED and sub.marks_obtained is not None:
                marks = float(sub.marks_obtained)
                scores[a.id] = marks
                total_obtained += marks
                total_possible += float(a.max_marks)
            else:
                scores[a.id] = None
                total_possible += float(a.max_marks)

        pct = round((total_obtained / total_possible * 100), 1) if total_possible > 0 else 0.0
        letter = 'A+' if pct >= 90 else 'A' if pct >= 80 else 'B' if pct >= 70 else 'C' if pct >= 60 else 'D' if pct >= 50 else 'F'

        gradebook_rows.append({
            'student': student,
            'scores': scores,
            'total_obtained': total_obtained,
            'percentage': pct,
            'letter': letter,
        })

    return render(request, 'analytics/course_gradebook.html', {
        'course': course,
        'assignments': assignments,
        'gradebook_rows': gradebook_rows,
    })


@teacher_required
def export_gradebook_csv(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    assignments = course.assignments.order_by('due_date')
    enrollments = course.enrollments.filter(is_active=True).select_related('student__user').order_by('student__roll_number')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{course.code}_Gradebook.csv"'

    writer = csv.writer(response)
    header = ['Roll Number', 'Student Name', 'Email'] + [f"{a.title} ({a.max_marks}m)" for a in assignments] + ['Total Score', 'Percentage %', 'Grade']
    writer.writerow(header)

    for enrollment in enrollments:
        student = enrollment.student
        row = [student.roll_number, student.user.get_full_name(), student.user.email]
        total_obtained = 0.0
        total_possible = 0.0

        for a in assignments:
            sub = Submission.objects.filter(assignment=a, student=student).first()
            if sub and sub.marks_obtained is not None:
                marks = float(sub.marks_obtained)
                row.append(marks)
                total_obtained += marks
            else:
                row.append('N/A')
            total_possible += float(a.max_marks)

        pct = round((total_obtained / total_possible * 100), 1) if total_possible > 0 else 0.0
        letter = 'A+' if pct >= 90 else 'A' if pct >= 80 else 'B' if pct >= 70 else 'C' if pct >= 60 else 'D' if pct >= 50 else 'F'

        row.extend([total_obtained, f"{pct}%", letter])
        writer.writerow(row)

    return response


@teacher_required
def export_attendance_csv(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    sessions = course.attendance_sessions.order_by('date')
    enrollments = course.enrollments.filter(is_active=True).select_related('student__user').order_by('student__roll_number')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{course.code}_Attendance_Register.csv"'

    writer = csv.writer(response)
    header = ['Roll Number', 'Student Name'] + [s.date.strftime('%Y-%m-%d') for s in sessions] + ['Total Present', 'Total Sessions', 'Attendance %']
    writer.writerow(header)

    for enrollment in enrollments:
        student = enrollment.student
        row = [student.roll_number, student.user.get_full_name()]
        present_count = 0

        for s in sessions:
            rec = AttendanceRecord.objects.filter(session=s, student=student).first()
            if rec:
                row.append(rec.get_status_display())
                if rec.status in [AttendanceRecord.Status.PRESENT, AttendanceRecord.Status.LATE]:
                    present_count += 1
            else:
                row.append('Not Marked')

        total_sessions = sessions.count()
        pct = round((present_count / total_sessions * 100), 1) if total_sessions > 0 else 100.0
        row.extend([present_count, total_sessions, f"{pct}%"])
        writer.writerow(row)

    return response
