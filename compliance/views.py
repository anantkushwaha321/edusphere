import json
import uuid
from datetime import datetime, timezone as dt_timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder

from .models import DataSubjectRequest, EmailPreference, CookieConsentLog, ParentalConsentRecord
from accounts.models import User, StudentProfile
from activity_logs.models import log_activity, ActivityLog
from academics.models import CourseEnrollment
from assignments.models import Submission
from attendance.models import AttendanceRecord


def privacy_policy_view(request):
    return render(request, 'compliance/privacy_policy.html', {
        'last_updated': 'October 13, 2026',
        'dpo_email': 'privacy@iimtindia.net',
        'institution_name': 'IIMT UNIVERSITY',
    })


def terms_of_service_view(request):
    return render(request, 'compliance/terms_of_service.html', {
        'last_updated': 'October 13, 2026',
        'institution_name': 'IIMT UNIVERSITY',
    })


def cookie_policy_view(request):
    return render(request, 'compliance/cookie_policy.html', {
        'last_updated': 'October 13, 2026',
    })


def refund_policy_view(request):
    return render(request, 'compliance/refund_policy.html', {
        'last_updated': 'October 13, 2026',
    })


def accessibility_statement_view(request):
    return render(request, 'compliance/accessibility_statement.html', {
        'last_updated': 'October 13, 2026',
    })


@csrf_exempt
def cookie_consent_api(request):
    """Logs cookie preference from consent banner via AJAX."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception:
            data = request.POST

        functional = str(data.get('functional', False)).lower() in ('true', '1')
        analytics = str(data.get('analytics', False)).lower() in ('true', '1')

        session_key = request.session.session_key or str(uuid.uuid4())
        ip = request.META.get('REMOTE_ADDR', '')
        # Anonymize IP (GDPR compliance)
        anonymized_ip = '.'.join(ip.split('.')[:2]) + '.0.0' if '.' in ip else ip

        CookieConsentLog.objects.create(
            session_id=session_key,
            user=request.user if request.user.is_authenticated else None,
            essential_accepted=True,
            functional_accepted=functional,
            analytics_accepted=analytics,
            ip_anonymized=anonymized_ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:250]
        )
        return JsonResponse({'status': 'ok', 'saved': True})
    return JsonResponse({'error': 'POST required'}, status=405)


@login_required
def data_subject_portal_view(request):
    """Self-service GDPR/CCPA privacy rights portal."""
    my_requests = DataSubjectRequest.objects.filter(user=request.user)

    if request.method == 'POST':
        req_type = request.POST.get('request_type')
        reason = request.POST.get('reason', '').strip()

        if req_type in dict(DataSubjectRequest.RequestType.choices):
            dsar = DataSubjectRequest.objects.create(
                user=request.user,
                request_type=req_type,
                reason=reason,
                status=DataSubjectRequest.Status.PENDING
            )
            log_activity(
                request=request,
                user=request.user,
                action=f"Submitted Data Privacy Request: {dsar.get_request_type_display()}",
                category=ActivityLog.Category.ADMIN,
                details=reason
            )
            messages.success(
                request,
                f"Your {dsar.get_request_type_display()} has been registered. Our Data Protection Officer will review and fulfill it within statutory timelines (max 30 days)."
            )
            return redirect('compliance:data_portal')

    return render(request, 'compliance/data_portal.html', {
        'my_requests': my_requests,
        'user_obj': request.user,
    })


@login_required
def export_my_data_instant(request):
    """GDPR Article 20 Right to Data Portability - Instant JSON export."""
    user = request.user

    export_payload = {
        'export_metadata': {
            'system': 'IIMT UNIVERSITY Smart Academic Management System',
            'exported_at': timezone.now().isoformat(),
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
        },
        'personal_profile': {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.get_role_display(),
            'phone': user.phone,
            'bio': user.bio,
            'address': user.address,
            'gender': user.gender,
            'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
            'date_joined': user.date_joined.isoformat(),
        },
        'academic_records': [],
        'submissions': [],
        'attendance': [],
        'activity_audit_logs': [],
    }

    # Student specific records
    if hasattr(user, 'student_profile'):
        sp = user.student_profile
        export_payload['student_profile'] = {
            'roll_number': sp.roll_number,
            'admission_number': sp.admission_number,
            'department': sp.department.name if sp.department else None,
            'current_semester': sp.current_semester,
            'academic_year': sp.academic_year.name if sp.academic_year else None,
            'guardian_name': sp.guardian_name,
            'guardian_phone': sp.guardian_phone,
            'is_minor': sp.is_minor,
            'parental_consent_verified': sp.parental_consent_verified,
        }

        # Enrollments
        for enr in sp.enrollments.select_related('course'):
            export_payload['academic_records'].append({
                'course_code': enr.course.code,
                'course_name': enr.course.name,
                'credits': enr.course.credits,
                'enrolled_at': enr.enrolled_at.isoformat(),
            })

        # Submissions
        for sub in sp.submissions.select_related('assignment__course'):
            export_payload['submissions'].append({
                'assignment': sub.assignment.title,
                'course': sub.assignment.course.code,
                'submitted_at': sub.submitted_at.isoformat(),
                'status': sub.get_status_display(),
                'marks_obtained': float(sub.marks_obtained) if sub.marks_obtained is not None else None,
                'max_marks': sub.assignment.max_marks,
                'feedback': sub.feedback,
            })

        # Attendance
        for att in sp.attendance_records.select_related('session__course'):
            export_payload['attendance'].append({
                'date': att.session.date.isoformat(),
                'course': att.session.course.code,
                'topic': att.session.topic_covered,
                'status': att.get_status_display(),
                'remarks': att.remarks,
            })

    # Activity logs
    for act in user.activity_logs.all()[:50]:
        export_payload['activity_audit_logs'].append({
            'timestamp': act.timestamp.isoformat(),
            'action': act.action,
            'category': act.get_category_display(),
            'details': act.details,
        })

    log_activity(
        request=request,
        user=user,
        action="Exported personal data archive (GDPR Art. 20)",
        category=ActivityLog.Category.AUTH
    )

    response = HttpResponse(
        json.dumps(export_payload, indent=2, cls=DjangoJSONEncoder),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="IIMT_University_UserData_{user.username}_{timezone.now():%Y%m%d}.json"'
    return response


@login_required
def email_preferences_view(request):
    pref, _ = EmailPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        pref.academic_announcements = 'academic_announcements' in request.POST
        pref.assignment_alerts = 'assignment_alerts' in request.POST
        pref.grade_notifications = 'grade_notifications' in request.POST
        pref.marketing_and_surveys = 'marketing_and_surveys' in request.POST
        pref.save()

        log_activity(
            request=request,
            user=request.user,
            action="Updated email communication preferences",
            category=ActivityLog.Category.AUTH
        )
        messages.success(request, "Your email communication preferences have been updated.")
        return redirect('compliance:email_preferences')

    return render(request, 'compliance/email_preferences.html', {'pref': pref})


def unsubscribe_token_view(request, token):
    """1-Click Unsubscribe endpoint without login requirement (RFC 8058 compliant)."""
    pref = get_object_or_404(EmailPreference, unsubscribe_token=token)

    if request.method == 'POST':
        pref.academic_announcements = 'academic_announcements' in request.POST
        pref.assignment_alerts = 'assignment_alerts' in request.POST
        pref.grade_notifications = 'grade_notifications' in request.POST
        pref.marketing_and_surveys = False  # immediately unsubscribe marketing
        pref.save()

        messages.success(request, "You have been successfully unsubscribed from optional email categories.")
        return render(request, 'compliance/unsubscribe_success.html', {'pref': pref})

    return render(request, 'compliance/unsubscribe_confirm.html', {'pref': pref})


def parental_consent_view(request):
    """Verifiable Parental Consent portal for parents/guardians under COPPA / GDPR Article 8."""
    if request.method == 'POST':
        student_roll = request.POST.get('student_roll', '').strip()
        guardian_name = request.POST.get('guardian_name', '').strip()
        guardian_email = request.POST.get('guardian_email', '').strip()
        guardian_phone = request.POST.get('guardian_phone', '').strip()
        consent_given = request.POST.get('consent_given') == 'on'

        student_profile = StudentProfile.objects.filter(roll_number__iexact=student_roll).first()

        if not student_profile:
            messages.error(request, "No student found matching the provided Roll Number. Please verify and retry.")
        elif not consent_given:
            messages.error(request, "You must check the consent acknowledgement checkbox to confirm authorization.")
        else:
            student_profile.parental_consent_verified = True
            student_profile.parental_consent_date = timezone.now()
            student_profile.guardian_name = guardian_name
            student_profile.parent_email = guardian_email
            student_profile.guardian_phone = guardian_phone
            student_profile.save()

            ParentalConsentRecord.objects.create(
                student=student_profile,
                guardian_name=guardian_name,
                guardian_email=guardian_email,
                guardian_phone=guardian_phone,
                consent_given=True,
                consent_method='ELECTRONIC_SIGNATURE',
                ip_address=request.META.get('REMOTE_ADDR', '')
            )

            messages.success(
                request,
                f"Parental consent for student {student_profile.user.get_full_name()} ({student_roll}) has been successfully verified and filed."
            )
            return redirect('compliance:parental_consent')

    return render(request, 'compliance/parental_consent.html')
