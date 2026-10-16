from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import User, StudentProfile, TeacherProfile, AdminProfile
from .forms import LoginForm, UserProfileUpdateForm, CustomPasswordChangeForm, UserCreationAdminForm
from .decorators import admin_required, role_required
from academics.models import Department
from activity_logs.models import log_activity, ActivityLog


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    try:
        departments = Department.objects.all()
    except Exception as e:
        import logging
        logging.getLogger('django.request').error("Database query failed in login_view: %s", e, exc_info=True)
        departments = []
    return render(request, 'accounts/login.html', {'departments': departments})


@login_required
def logout_view(request):
    log_activity(
        request=request,
        user=request.user,
        action="User logged out",
        category=ActivityLog.Category.AUTH
    )
    logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('login')


@login_required
def dashboard_redirect(request):
    """Routes the user to their appropriate role dashboard."""
    if request.user.is_admin_role:
        return redirect('admin_dashboard')
    elif request.user.is_teacher_role:
        return redirect('teacher_dashboard')
    elif request.user.is_student_role:
        return redirect('student_dashboard')
    return redirect('login')


@login_required
def profile_view(request):
    user = request.user
    profile_form = UserProfileUpdateForm(request.POST or None, request.FILES or None, instance=user)
    password_form = CustomPasswordChangeForm(user, request.POST or None)

    if request.method == 'POST':
        action = request.POST.get('form_action')
        if action == 'update_profile' and profile_form.is_valid():
            profile_form.save()
            log_activity(
                request=request,
                user=user,
                action="Updated personal profile details",
                category=ActivityLog.Category.AUTH
            )
            messages.success(request, "Your profile details have been updated successfully.")
            return redirect('profile')

        elif action == 'change_password' and password_form.is_valid():
            updated_user = password_form.save()
            update_session_auth_hash(request, updated_user)
            log_activity(
                request=request,
                user=user,
                action="Changed account password",
                category=ActivityLog.Category.AUTH
            )
            messages.success(request, "Your password was changed successfully.")
            return redirect('profile')

    return render(request, 'accounts/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'user_obj': user,
    })


@admin_required
def user_list_view(request):
    role_filter = request.GET.get('role', '')
    search_query = request.GET.get('q', '').strip()

    users_qs = User.objects.all().order_by('-date_joined')
    if role_filter:
        users_qs = users_qs.filter(role=role_filter)
    if search_query:
        users_qs = users_qs.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    paginator = Paginator(users_qs, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'accounts/user_list.html', {
        'page_obj': page_obj,
        'role_filter': role_filter,
        'search_query': search_query,
        'total_count': users_qs.count(),
    })


@admin_required
def user_create_view(request):
    form = UserCreationAdminForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        new_user = form.save()
        log_activity(
            request=request,
            user=request.user,
            action=f"Created new user account: {new_user.username} ({new_user.get_role_display()})",
            category=ActivityLog.Category.ADMIN
        )
        messages.success(request, f"User '{new_user.username}' created successfully!")
        return redirect('user_list')

    return render(request, 'accounts/user_create.html', {'form': form})


@admin_required
def user_detail_view(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    enrollments = []
    assignments_created = []
    attendance_records = []

    if target_user.is_student_role and hasattr(target_user, 'student_profile'):
        enrollments = target_user.student_profile.enrollments.select_related('course')
        attendance_records = target_user.student_profile.attendance_records.select_related('session__course')[:10]
    elif target_user.is_teacher_role and hasattr(target_user, 'teacher_profile'):
        assignments_created = target_user.teacher_profile.assignments.select_related('course')[:10]

    return render(request, 'accounts/user_detail.html', {
        'target_user': target_user,
        'enrollments': enrollments,
        'assignments_created': assignments_created,
        'attendance_records': attendance_records,
    })


@admin_required
def user_toggle_status_view(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, "You cannot deactivate your own administrative account.")
        return redirect('user_list')

    target_user.is_active = not target_user.is_active
    target_user.save()
    status_str = "activated" if target_user.is_active else "deactivated"
    log_activity(
        request=request,
        user=request.user,
        action=f"{status_str.capitalize()} user account: {target_user.username}",
        category=ActivityLog.Category.ADMIN
    )
    messages.success(request, f"User '{target_user.username}' has been {status_str}.")
    return redirect('user_list')
