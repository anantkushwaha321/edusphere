from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from .models import AttendanceSession, AttendanceRecord
from .forms import AttendanceSessionForm
from academics.models import Course, CourseEnrollment
from accounts.models import StudentProfile
from accounts.decorators import teacher_required, student_required
from activity_logs.models import log_activity, ActivityLog


@login_required
def attendance_dashboard_view(request):
    user = request.user
    today = timezone.now().date()

    if user.is_student_role and hasattr(user, 'student_profile'):
        student = user.student_profile
        enrollments = CourseEnrollment.objects.filter(student=student, is_active=True).select_related('course')

        course_attendance_stats = []
        total_sessions_all = 0
        total_present_all = 0

        for enrollment in enrollments:
            course = enrollment.course
            total_course_sessions = AttendanceRecord.objects.filter(student=student, session__course=course).count()
            present_course_sessions = AttendanceRecord.objects.filter(
                student=student,
                session__course=course,
                status__in=[AttendanceRecord.Status.PRESENT, AttendanceRecord.Status.LATE]
            ).count()

            pct = round((present_course_sessions / total_course_sessions * 100), 1) if total_course_sessions > 0 else 100.0
            course_attendance_stats.append({
                'course': course,
                'total_sessions': total_course_sessions,
                'present_sessions': present_course_sessions,
                'percentage': pct,
                'is_low': pct < 75.0,
            })
            total_sessions_all += total_course_sessions
            total_present_all += present_course_sessions

        overall_pct = round((total_present_all / total_sessions_all * 100), 1) if total_sessions_all > 0 else 100.0

        recent_records = AttendanceRecord.objects.filter(student=student).select_related('session__course').order_by('-session__date')[:15]

        return render(request, 'attendance/student_attendance.html', {
            'course_stats': course_attendance_stats,
            'overall_percentage': overall_pct,
            'recent_records': recent_records,
            'is_overall_low': overall_pct < 75.0,
        })

    elif user.is_teacher_role and hasattr(user, 'teacher_profile') and not user.is_admin_role:
        teacher = user.teacher_profile
        courses = Course.objects.filter(teacher=teacher, is_active=True)
        recent_sessions = AttendanceSession.objects.filter(course__in=courses).select_related('course').order_by('-date')[:15]

        return render(request, 'attendance/teacher_attendance.html', {
            'courses': courses,
            'recent_sessions': recent_sessions,
            'today': today,
        })

    else:
        # Admin view
        courses = Course.objects.all().select_related('department', 'teacher__user')
        recent_sessions = AttendanceSession.objects.all().select_related('course', 'taken_by__user').order_by('-date')[:20]

        total_sessions = AttendanceSession.objects.count()
        total_records = AttendanceRecord.objects.count()
        present_records = AttendanceRecord.objects.filter(status=AttendanceRecord.Status.PRESENT).count()
        campus_avg = round((present_records / total_records * 100), 1) if total_records > 0 else 0

        return render(request, 'attendance/admin_attendance.html', {
            'courses': courses,
            'recent_sessions': recent_sessions,
            'total_sessions': total_sessions,
            'campus_avg': campus_avg,
        })


@teacher_required
def take_attendance_view(request):
    teacher = getattr(request.user, 'teacher_profile', None)
    course_id = request.GET.get('course') or request.POST.get('course')
    selected_date = request.GET.get('date') or request.POST.get('date') or timezone.now().date().isoformat()

    courses = Course.objects.filter(teacher=teacher, is_active=True) if teacher else Course.objects.filter(is_active=True)
    selected_course = None
    enrolled_students = []
    existing_session = None
    existing_records = {}

    if course_id:
        selected_course = get_object_or_404(Course, pk=course_id)
        enrolled_students = CourseEnrollment.objects.filter(
            course=selected_course, is_active=True
        ).select_related('student__user').order_by('student__roll_number')

        existing_session = AttendanceSession.objects.filter(course=selected_course, date=selected_date).first()
        if existing_session:
            existing_records = {r.student_id: r for r in existing_session.records.all()}

    if request.method == 'POST' and selected_course:
        topic_covered = request.POST.get('topic_covered', '').strip()

        with transaction.atomic():
            session, _ = AttendanceSession.objects.get_or_create(
                course=selected_course,
                date=selected_date,
                defaults={'taken_by': teacher, 'topic_covered': topic_covered}
            )
            if topic_covered:
                session.topic_covered = topic_covered
                session.save()

            for enrollment in enrolled_students:
                student = enrollment.student
                status_val = request.POST.get(f'status_{student.id}', AttendanceRecord.Status.PRESENT)
                remarks_val = request.POST.get(f'remarks_{student.id}', '').strip()

                AttendanceRecord.objects.update_or_create(
                    session=session,
                    student=student,
                    defaults={'status': status_val, 'remarks': remarks_val}
                )

        log_activity(
            request=request,
            action=f"Marked attendance for {selected_course.code} on {selected_date}",
            category=ActivityLog.Category.ATTENDANCE
        )
        messages.success(request, f"Attendance for {selected_course.code} on {selected_date} has been saved successfully!")
        return redirect('attendance_session_detail', pk=session.pk)

    return render(request, 'attendance/take_attendance.html', {
        'courses': courses,
        'selected_course': selected_course,
        'selected_date': selected_date,
        'enrolled_students': enrolled_students,
        'existing_session': existing_session,
        'existing_records': existing_records,
    })


@login_required
def attendance_session_detail_view(request, pk):
    session = get_object_or_404(
        AttendanceSession.objects.select_related('course', 'taken_by__user'),
        pk=pk
    )
    records = session.records.select_related('student__user').order_by('student__roll_number')

    return render(request, 'attendance/session_detail.html', {
        'session': session,
        'records': records,
    })
