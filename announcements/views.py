from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse

from .models import Announcement, Notification
from .forms import AnnouncementForm
from accounts.models import User
from accounts.decorators import teacher_required
from activity_logs.models import log_activity, ActivityLog


@login_required
def announcement_list_view(request):
    user = request.user
    priority_filter = request.GET.get('priority', '')

    # Filter announcements by audience
    announcements = Announcement.objects.filter(is_active=True)

    if not user.is_admin_role:
        if user.is_student_role:
            user_dept = user.student_profile.department if hasattr(user, 'student_profile') else None
            announcements = announcements.filter(
                Q(target_audience=Announcement.Audience.ALL) |
                Q(target_audience=Announcement.Audience.STUDENTS) |
                Q(target_audience=Announcement.Audience.DEPARTMENT, department=user_dept)
            )
        elif user.is_teacher_role:
            user_dept = user.teacher_profile.department if hasattr(user, 'teacher_profile') else None
            announcements = announcements.filter(
                Q(target_audience=Announcement.Audience.ALL) |
                Q(target_audience=Announcement.Audience.TEACHERS) |
                Q(target_audience=Announcement.Audience.DEPARTMENT, department=user_dept)
            )

    if priority_filter:
        announcements = announcements.filter(priority=priority_filter)

    return render(request, 'announcements/announcement_list.html', {
        'announcements': announcements,
        'selected_priority': priority_filter,
    })


@teacher_required
def announcement_create_view(request):
    form = AnnouncementForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        announcement = form.save(commit=False)
        announcement.author = request.user
        announcement.save()

        # Generate notifications for the audience
        recipients = User.objects.filter(is_active=True).exclude(pk=request.user.pk)
        if announcement.target_audience == Announcement.Audience.STUDENTS:
            recipients = recipients.filter(role=User.Role.STUDENT)
        elif announcement.target_audience == Announcement.Audience.TEACHERS:
            recipients = recipients.filter(role=User.Role.TEACHER)
        elif announcement.target_audience == Announcement.Audience.DEPARTMENT and announcement.department:
            recipients = recipients.filter(
                Q(student_profile__department=announcement.department) |
                Q(teacher_profile__department=announcement.department)
            )

        notifications_to_create = [
            Notification(
                recipient=u,
                title=f"Announcement: {announcement.title}",
                message=announcement.content[:120] + "...",
                link=f"/announcements/{announcement.id}/",
                notification_type=Notification.Type.ANNOUNCEMENT
            )
            for u in recipients[:100]  # cap batch
        ]
        Notification.objects.bulk_create(notifications_to_create)

        log_activity(
            request=request,
            action=f"Published announcement: '{announcement.title}'",
            category=ActivityLog.Category.ANNOUNCEMENT
        )
        messages.success(request, f"Announcement '{announcement.title}' has been broadcast successfully!")
        return redirect('announcement_list')

    return render(request, 'announcements/announcement_form.html', {'form': form, 'title': 'Create Announcement'})


@login_required
def announcement_detail_view(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, is_active=True)
    return render(request, 'announcements/announcement_detail.html', {'announcement': announcement})


@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(recipient=request.user)
    return render(request, 'announcements/notification_list.html', {'notifications': notifications})


@login_required
def notification_mark_read_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    if notification.link:
        return redirect(notification.link)
    return redirect('notification_list')


@login_required
def notification_mark_all_read_view(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notification_list')
