from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count

from .models import Department, AcademicYear, Course, CourseEnrollment
from .forms import DepartmentForm, AcademicYearForm, CourseForm, CourseEnrollmentForm
from accounts.decorators import admin_required, teacher_required
from accounts.models import StudentProfile
from activity_logs.models import log_activity, ActivityLog


@login_required
def department_list_view(request):
    departments = Department.objects.annotate(
        num_courses=Count('courses', distinct=True),
        num_students=Count('students', distinct=True),
        num_teachers=Count('teachers', distinct=True)
    )
    return render(request, 'academics/department_list.html', {'departments': departments})


@admin_required
def department_create_view(request):
    form = DepartmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        dept = form.save()
        log_activity(
            request=request,
            action=f"Created department: {dept.name} ({dept.code})",
            category=ActivityLog.Category.ADMIN
        )
        messages.success(request, f"Department '{dept.name}' created successfully.")
        return redirect('department_list')
    return render(request, 'academics/department_form.html', {'form': form, 'title': 'Create Department'})


@login_required
def department_detail_view(request, pk):
    department = get_object_or_404(Department, pk=pk)
    courses = department.courses.select_related('teacher__user')
    students = department.students.select_related('user')
    teachers = department.teachers.select_related('user')
    return render(request, 'academics/department_detail.html', {
        'department': department,
        'courses': courses,
        'students': students,
        'teachers': teachers
    })


@login_required
def course_list_view(request):
    user = request.user
    search_query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('department', '')

    courses = Course.objects.select_related('department', 'teacher__user', 'academic_year')

    if user.is_student_role and hasattr(user, 'student_profile'):
        enrolled_course_ids = CourseEnrollment.objects.filter(
            student=user.student_profile, is_active=True
        ).values_list('course_id', flat=True)
        # Students see their enrolled courses prioritized
        courses = courses.filter(id__in=enrolled_course_ids)
    elif user.is_teacher_role and hasattr(user, 'teacher_profile') and not user.is_admin_role:
        courses = courses.filter(teacher=user.teacher_profile)

    if dept_id:
        courses = courses.filter(department_id=dept_id)
    if search_query:
        courses = courses.filter(Q(code__icontains=search_query) | Q(name__icontains=search_query))

    departments = Department.objects.all()

    return render(request, 'academics/course_list.html', {
        'courses': courses,
        'departments': departments,
        'selected_dept': dept_id,
        'search_query': search_query
    })


@login_required
def course_detail_view(request, pk):
    course = get_object_or_404(
        Course.objects.select_related('department', 'teacher__user', 'academic_year'),
        pk=pk
    )
    enrollments = course.enrollments.filter(is_active=True).select_related('student__user')
    assignments = course.assignments.all()[:5]
    materials = course.materials.all()[:5]
    sessions = course.attendance_sessions.all()[:5]

    # Check if student is enrolled
    is_enrolled = False
    if request.user.is_student_role and hasattr(request.user, 'student_profile'):
        is_enrolled = course.enrollments.filter(student=request.user.student_profile, is_active=True).exists()

    enrollment_form = CourseEnrollmentForm()

    return render(request, 'academics/course_detail.html', {
        'course': course,
        'enrollments': enrollments,
        'assignments': assignments,
        'materials': materials,
        'sessions': sessions,
        'is_enrolled': is_enrolled,
        'enrollment_form': enrollment_form,
    })


@admin_required
def course_create_view(request):
    form = CourseForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        course = form.save()
        log_activity(
            request=request,
            action=f"Created course: {course.code} - {course.name}",
            category=ActivityLog.Category.ADMIN
        )
        messages.success(request, f"Course '{course.name}' created successfully.")
        return redirect('course_detail', pk=course.pk)
    return render(request, 'academics/course_form.html', {'form': form, 'title': 'Create Course'})


@admin_required
def course_edit_view(request, pk):
    course = get_object_or_404(Course, pk=pk)
    form = CourseForm(request.POST or None, request.FILES or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        course = form.save()
        log_activity(
            request=request,
            action=f"Updated course: {course.code} - {course.name}",
            category=ActivityLog.Category.ADMIN
        )
        messages.success(request, f"Course '{course.name}' updated successfully.")
        return redirect('course_detail', pk=course.pk)
    return render(request, 'academics/course_form.html', {'form': form, 'title': f'Edit Course: {course.code}'})


@teacher_required
def course_enroll_view(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        student_id = request.POST.get('student')
        if student_id:
            student = get_object_or_404(StudentProfile, pk=student_id)
            enrollment, created = CourseEnrollment.objects.get_or_create(
                course=course,
                student=student,
                defaults={'is_active': True}
            )
            if not created and not enrollment.is_active:
                enrollment.is_active = True
                enrollment.save()
                messages.success(request, f"Student {student.user.get_full_name()} re-enrolled in {course.code}.")
            elif created:
                messages.success(request, f"Student {student.user.get_full_name()} successfully enrolled in {course.code}.")
            else:
                messages.info(request, "Student is already enrolled in this course.")
    return redirect('course_detail', pk=course.pk)


@admin_required
def course_unenroll_view(request, course_pk, student_pk):
    enrollment = get_object_or_404(CourseEnrollment, course_id=course_pk, student_id=student_pk)
    enrollment.is_active = False
    enrollment.save()
    messages.success(request, "Student has been removed from this course.")
    return redirect('course_detail', pk=course_pk)
