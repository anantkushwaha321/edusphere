import json
import re
import logging
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth import login, logout
from django.utils.text import slugify
from django.db import transaction
from django.urls import reverse

from .models import User, StudentProfile, EmailOTPChallenge
from .otp_service import (
    normalize_email,
    create_otp_challenge,
    verify_otp_code,
    OTPError,
    RESEND_COOLDOWN_SECONDS
)
from academics.models import Department, AcademicYear
from activity_logs.models import log_activity, ActivityLog

logger = logging.getLogger(__name__)


def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def mask_email(email: str) -> str:
    """Mask email for privacy, e.g. j***n@example.com."""
    try:
        user_part, domain_part = email.split('@')
        if len(user_part) <= 2:
            masked_user = user_part[0] + '*'
        else:
            masked_user = user_part[0] + '*' * (len(user_part) - 2) + user_part[-1]
        return f"{masked_user}@{domain_part}"
    except Exception:
        return email


def derive_name_from_email(email: str):
    """
    Derives clean first_name and last_name from an email address.
    e.g. 'vikash.kumar@example.com' -> ('Vikash', 'Kumar')
         'kumarvikash990999@gmail.com' -> ('Kumarvikash', 'Student')
         'anantkushwaha321@gmail.com' -> ('Anantkushwaha', 'Student')
    """
    prefix = email.split('@')[0].strip()
    words = re.findall(r'[A-Za-z]+|\d+', prefix)
    alpha_words = [w.capitalize() for w in words if w.isalpha()]

    if len(alpha_words) >= 2:
        first_name = alpha_words[0]
        last_name = " ".join(alpha_words[1:])
    elif len(alpha_words) == 1:
        first_name = alpha_words[0]
        last_name = "Student"
    else:
        first_name = prefix.capitalize() or "Student"
        last_name = "User"

    return first_name, last_name


def get_dashboard_url_for_user(user: User) -> str:
    """Return appropriate dashboard URL based on user role."""
    if user.is_admin_role:
        return reverse('admin_dashboard')
    elif user.is_teacher_role:
        return reverse('teacher_dashboard')
    elif user.is_student_role:
        return reverse('student_dashboard')
    return reverse('dashboard')


@require_POST
def api_send_otp(request: HttpRequest):
    """
    POST /api/auth/send-otp/
    Payload: { "email": "user@example.com", "terms_accepted": true (optional) }
    """
    try:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST

        raw_email = data.get('email', '')
        terms_accepted = data.get('terms_accepted', True)

        try:
            email = normalize_email(raw_email)
        except OTPError as e:
            return JsonResponse({'success': False, 'message': e.message, 'code': e.code}, status=e.status_code)

        ip_address = get_client_ip(request)

        # Check whether user is already registered
        existing_user = User.objects.filter(email__iexact=email).first()

        if existing_user:
            if not existing_user.is_active:
                return JsonResponse({
                    'success': False,
                    'message': 'This account has been deactivated. Please contact the academic administrator.',
                    'code': 'account_inactive'
                }, status=403)
            purpose = EmailOTPChallenge.Purpose.LOGIN
            is_existing_user = True
        else:
            purpose = EmailOTPChallenge.Purpose.REGISTER
            is_existing_user = False

        try:
            challenge, cooldown = create_otp_challenge(
                email=email,
                purpose=purpose,
                ip_address=ip_address,
                enforce_cooldown=True
            )
        except OTPError as e:
            return JsonResponse({'success': False, 'message': e.message, 'code': e.code}, status=e.status_code)

        return JsonResponse({
            'success': True,
            'message': f"Verification code sent to {mask_email(email)}.",
            'is_existing_user': is_existing_user,
            'purpose': str(purpose),
            'cooldown_seconds': cooldown,
            'email': email,
        })
    except OTPError as e:
        return JsonResponse({'success': False, 'message': e.message, 'code': e.code}, status=e.status_code)
    except Exception as e:
        logger.error("Unhandled exception in api_send_otp: %s", e, exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Failed to process verification request due to an internal server error. Please retry.',
            'code': 'server_error'
        }, status=500)


@require_POST
def api_resend_otp(request: HttpRequest):
    """
    POST /api/auth/resend-otp/
    Payload: { "email": "user@example.com" }
    """
    try:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST

        raw_email = data.get('email', '')
        try:
            email = normalize_email(raw_email)
        except OTPError as e:
            return JsonResponse({'success': False, 'message': e.message, 'code': e.code}, status=e.status_code)

        ip_address = get_client_ip(request)
        existing_user = User.objects.filter(email__iexact=email, is_active=True).first()
        purpose = EmailOTPChallenge.Purpose.LOGIN if existing_user else EmailOTPChallenge.Purpose.REGISTER

        try:
            challenge, cooldown = create_otp_challenge(
                email=email,
                purpose=purpose,
                ip_address=ip_address,
                enforce_cooldown=True
            )
        except OTPError as e:
            return JsonResponse({'success': False, 'message': e.message, 'code': e.code}, status=e.status_code)

        return JsonResponse({
            'success': True,
            'message': f"A new verification code has been dispatched to {mask_email(email)}.",
            'cooldown_seconds': cooldown,
        })
    except OTPError as e:
        return JsonResponse({'success': False, 'message': e.message, 'code': e.code}, status=e.status_code)
    except Exception as e:
        logger.error("Unhandled exception in api_resend_otp: %s", e, exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Failed to resend code due to an internal server error. Please retry.',
            'code': 'server_error'
        }, status=500)


@require_POST
def api_verify_otp(request: HttpRequest):
    """
    POST /api/auth/verify-otp/
    Payload:
    {
        "email": "user@example.com",
        "otp": "123456",
        "registration": {
            "first_name": "Alice",
            "last_name": "Smith",
            "roll_number": "CS2026-099",
            "department_id": 1,
            "guardian_name": "..."
        } (optional)
    }
    """
    try:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST

        raw_email = data.get('email', '')
        plain_otp = data.get('otp', '')
        registration_data = data.get('registration')

        try:
            email = normalize_email(raw_email)
        except OTPError as e:
            return JsonResponse({'success': False, 'message': e.message, 'code': e.code}, status=e.status_code)

        # Always mark challenge as used upon successful OTP verification
        mark_used = True

        try:
            success, challenge, user = verify_otp_code(email=email, plain_otp=plain_otp, mark_used=mark_used)
        except OTPError as e:
            return JsonResponse({'success': False, 'message': e.message, 'code': e.code}, status=e.status_code)

        # Case 1: Existing User - Immediate Authentication & Session Login
        if user is not None:
            if not user.is_active:
                return JsonResponse({
                    'success': False,
                    'message': 'This account has been deactivated.',
                    'code': 'account_inactive'
                }, status=403)

            login(request, user)
            log_activity(
                request=request,
                user=user,
                action=f"User authenticated via Email OTP ({user.get_role_display()})",
                category=ActivityLog.Category.AUTH
            )

            redirect_url = get_dashboard_url_for_user(user)
            next_url = request.GET.get('next') or data.get('next')
            if next_url and next_url.startswith('/'):
                redirect_url = next_url

            return JsonResponse({
                'success': True,
                'authenticated': True,
                'is_existing_user': True,
                'redirect_url': redirect_url,
                'message': f"Welcome back, {user.get_full_name() or user.username}!",
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.get_full_name(),
                    'role': user.role,
                    'role_display': user.get_role_display(),
                }
            })

        # Case 2: First-time Email Login - Automatically provision account & log in directly
        with transaction.atomic():
            derived_first, derived_last = derive_name_from_email(email)
            base_username = slugify(email.split('@')[0]) or 'student'
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            first_name = derived_first
            last_name = derived_last
            roll_number = ''
            department_id = None
            guardian_name = ''
            guardian_phone = ''

            # Respect optional registration payload if provided
            if registration_data and isinstance(registration_data, dict):
                if registration_data.get('first_name'):
                    first_name = str(registration_data['first_name']).strip()
                if registration_data.get('last_name'):
                    last_name = str(registration_data['last_name']).strip()
                if registration_data.get('roll_number'):
                    roll_number = str(registration_data['roll_number']).strip()
                department_id = registration_data.get('department_id')
                guardian_name = str(registration_data.get('guardian_name', '')).strip()
                guardian_phone = str(registration_data.get('guardian_phone', '')).strip()

            new_user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=User.Role.STUDENT,
                is_active=True
            )
            new_user.set_unusable_password()  # No password required - authenticates via OTP
            new_user.save()

            # Handle department & active year
            dept = None
            if department_id:
                dept = Department.objects.filter(pk=department_id).first()
            if not dept:
                dept = Department.objects.first()

            active_year = AcademicYear.objects.filter(is_current=True).first()

            final_roll = roll_number or f"STU-{new_user.id:04d}"
            if StudentProfile.objects.filter(roll_number=final_roll).exists():
                final_roll = f"STU-{new_user.id:04d}"

            StudentProfile.objects.create(
                user=new_user,
                roll_number=final_roll,
                admission_number=f"ADM-{new_user.id:04d}",
                department=dept,
                academic_year=active_year,
                current_semester=1,
                guardian_name=guardian_name,
                guardian_phone=guardian_phone
            )

            challenge.user = new_user
            challenge.is_used = True
            challenge.is_verified = True
            challenge.save(update_fields=['user', 'is_used', 'is_verified'])

            login(request, new_user)
            log_activity(
                request=request,
                user=new_user,
                action=f"New student account provisioned and verified via OTP: {new_user.username}",
                category=ActivityLog.Category.AUTH
            )

        return JsonResponse({
            'success': True,
            'authenticated': True,
            'is_existing_user': False,
            'redirect_url': reverse('student_dashboard'),
            'message': f"Welcome to EduSphere, {new_user.first_name}!",
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email,
                'full_name': new_user.get_full_name(),
                'role': new_user.role,
                'role_display': new_user.get_role_display(),
            }
        })
    except OTPError as e:
        return JsonResponse({'success': False, 'message': e.message, 'code': e.code}, status=e.status_code)
    except Exception as e:
        logger.error("Unhandled exception in api_verify_otp: %s", e, exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Failed to complete verification due to an internal server error. Please retry.',
            'code': 'server_error'
        }, status=500)



@require_POST
def api_logout(request: HttpRequest):
    """
    POST /api/auth/logout/
    """
    if request.user.is_authenticated:
        log_activity(
            request=request,
            user=request.user,
            action="User logged out",
            category=ActivityLog.Category.AUTH
        )
    logout(request)
    return JsonResponse({
        'success': True,
        'message': 'Logged out successfully.',
        'redirect_url': reverse('login')
    })


@require_GET
def api_me(request: HttpRequest):
    """
    GET /api/auth/me/
    """
    if not request.user.is_authenticated:
        return JsonResponse({'authenticated': False}, status=200)

    user = request.user
    return JsonResponse({
        'authenticated': True,
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user.get_full_name(),
        'role': user.role,
        'role_display': user.get_role_display(),
        'dashboard_url': get_dashboard_url_for_user(user),
    })
