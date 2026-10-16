import os
import secrets
import logging
import datetime
import smtplib
import socket
from typing import Optional, Tuple
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .models import EmailOTPChallenge, User

logger = logging.getLogger(__name__)

OTP_EXPIRY_MINUTES = 5
RESEND_COOLDOWN_SECONDS = 60
MAX_ATTEMPTS_PER_CHALLENGE = 5
MAX_HOURLY_REQUESTS_PER_EMAIL = 5
MAX_HOURLY_REQUESTS_PER_IP = 15


class OTPError(Exception):
    """Custom exception for OTP domain errors."""
    def __init__(self, message: str, code: str = 'invalid', status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def mask_email_address(email: str) -> str:
    """Mask email for safe diagnostic logging without exposing PII (e.g. a***a@gmail.com)."""
    if not email or '@' not in email:
        return '***'
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[:1] + '*'
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def normalize_email(email: str) -> str:
    """Normalize and validate email address."""
    if not email or not isinstance(email, str):
        raise OTPError("Please provide a valid email address.", code="invalid_email")
    normalized = email.strip().lower()
    try:
        validate_email(normalized)
    except ValidationError:
        raise OTPError("Invalid email address format.", code="invalid_email")
    return normalized


def generate_cryptographic_otp(length: int = 6) -> str:
    """Generate a cryptographically secure random numeric OTP."""
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def check_rate_limits(email: str, ip_address: Optional[str] = None):
    """Enforce rate limits on OTP generation to prevent abuse."""
    one_hour_ago = timezone.now() - datetime.timedelta(hours=1)

    # Hourly limit per email
    email_requests_count = EmailOTPChallenge.objects.filter(
        email=email,
        created_at__gte=one_hour_ago
    ).count()
    if email_requests_count >= MAX_HOURLY_REQUESTS_PER_EMAIL:
        raise OTPError(
            "Too many OTP requests for this email address. Please try again in an hour.",
            code="rate_limit_email",
            status_code=429
        )

    # Hourly limit per IP
    if ip_address:
        ip_requests_count = EmailOTPChallenge.objects.filter(
            ip_address=ip_address,
            created_at__gte=one_hour_ago
        ).count()
        if ip_requests_count >= MAX_HOURLY_REQUESTS_PER_IP:
            raise OTPError(
                "Too many verification requests from this network. Please try again later.",
                code="rate_limit_ip",
                status_code=429
            )


def check_resend_cooldown(email: str):
    """Verify that user has respected the 60-second cooldown."""
    latest = EmailOTPChallenge.objects.filter(email=email).order_by('-created_at').first()
    if latest:
        seconds_since_last = (timezone.now() - latest.created_at).total_seconds()
        if seconds_since_last < RESEND_COOLDOWN_SECONDS:
            remaining = int(RESEND_COOLDOWN_SECONDS - seconds_since_last)
            raise OTPError(
                f"Please wait {remaining} seconds before requesting a new verification code.",
                code="cooldown_active",
                status_code=429
            )


def dispatch_via_resend(
    api_key: str,
    from_email: str,
    to_email: str,
    subject: str,
    html_message: str,
    text_message: str
) -> bool:
    """
    Dispatches email via the official Resend HTTPS REST API (Port 443).
    Immune to cloud SMTP port blocking (Render free tier blocks ports 25, 465, 587).
    Safely handles provider errors without exposing API keys, OTP codes, or private email content.
    """
    import json
    import urllib.request
    import urllib.error

    clean_key = (api_key or '').strip()
    if not clean_key:
        raise OTPError(
            "RESEND_API_KEY is not configured.",
            code="resend_missing_key",
            status_code=503
        )

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {clean_key}",
        "Content-Type": "application/json",
        "User-Agent": "EduSphere-Academic-PaaS/1.0",
    }

    # Respect DEFAULT_FROM_EMAIL from settings / env, defaulting to Resend sandbox if omitted
    sender = (from_email or '').strip()
    if not sender:
        sender = getattr(settings, 'DEFAULT_FROM_EMAIL', 'EduSphere <onboarding@resend.dev>')

    payload = {
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "html": html_message,
        "text": text_message,
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')

    timeout_seconds = int(getattr(settings, 'EMAIL_TIMEOUT', 10))

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            resp_body = resp.read().decode('utf-8', errors='ignore')
            resp_data = {}
            if resp_body:
                try:
                    resp_data = json.loads(resp_body)
                except Exception:
                    pass

            email_id = resp_data.get('id', 'accepted')
            if resp.status in (200, 201):
                logger.info(
                    "OTP email successfully queued via Resend API (id=%s) to %s",
                    email_id,
                    mask_email_address(to_email)
                )
                return True
            else:
                logger.error(
                    "Resend API returned unexpected status %s for %s",
                    resp.status,
                    mask_email_address(to_email)
                )
                raise OTPError(
                    f"Resend API returned unexpected response status ({resp.status}).",
                    code="resend_unexpected_status",
                    status_code=502
                )
    except urllib.error.HTTPError as err:
        err_body = err.read().decode('utf-8', errors='ignore')
        err_name = 'api_error'
        err_msg = 'Unknown error'
        try:
            parsed = json.loads(err_body)
            err_msg = parsed.get('message', err_body)
            err_name = parsed.get('name', 'api_error')
        except Exception:
            err_msg = err_body[:200] if err_body else f"HTTP {err.code}"

        logger.error(
            "Resend API rejected dispatch (HTTP %s, type=%s) for %s: %s",
            err.code,
            err_name,
            mask_email_address(to_email),
            err_msg
        )

        if err.code == 401:
            raise OTPError(
                "Resend API authentication failed. Please verify that RESEND_API_KEY in your Render environment variables is valid.",
                code="resend_invalid_api_key",
                status_code=503
            )
        elif err.code in (400, 403, 422):
            raise OTPError(
                f"Resend rejected email delivery ({err_name}): {err_msg}",
                code=f"resend_{err_name}",
                status_code=400 if err.code == 400 else 503
            )
        elif err.code >= 500:
            raise OTPError(
                "Resend email service is temporarily unavailable. Please retry in a moment.",
                code="resend_server_error",
                status_code=502
            )
        else:
            raise OTPError(
                f"Email delivery via Resend API failed ({err.code}): {err_msg}",
                code="resend_api_failed",
                status_code=502
            )
    except (urllib.error.URLError, TimeoutError, socket.timeout) as err:
        logger.error("Resend connection failed for %s: %s", mask_email_address(to_email), err)
        raise OTPError(
            "Failed to communicate with Resend email API. Please check network connectivity.",
            code="resend_connection_error",
            status_code=502
        )
    except OTPError:
        raise
    except Exception as err:
        logger.error("Unexpected error during Resend dispatch: %s", err)
        raise OTPError(
            "An unexpected error occurred while communicating with the email delivery service.",
            code="resend_unexpected_error",
            status_code=500
        )



def dispatch_via_brevo(api_key: str, from_email: str, to_email: str, subject: str, html_message: str, text_message: str) -> bool:
    """Dispatches email via Brevo HTTPS REST API (Port 443). Safe on Render free tier."""
    import json
    import urllib.request
    import urllib.error

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "EduSphere-Academic-PaaS/1.0",
    }
    # Parse sender email
    sender_email = from_email
    sender_name = "EduSphere Security"
    if '<' in from_email and '>' in from_email:
        parts = from_email.split('<')
        sender_name = parts[0].strip() or sender_name
        sender_email = parts[1].split('>')[0].strip()

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_message,
        "textContent": text_message,
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201, 202):
                logger.info(f"OTP successfully delivered via Brevo HTTPS API to {to_email}")
                return True
    except urllib.error.HTTPError as err:
        err_msg = err.read().decode('utf-8', errors='ignore')
        logger.error(f"Brevo HTTP error ({err.code}): {err_msg}")
        raise OTPError(
            f"Email delivery via Brevo API failed ({err.code}): {err_msg}",
            code="brevo_api_failed",
            status_code=502
        )
    except Exception as err:
        logger.error(f"Brevo dispatch error: {err}")
        raise OTPError(
            f"Failed to communicate with Brevo email API: {err}",
            code="brevo_connection_error",
            status_code=502
        )
    return False


def dispatch_otp_email(email: str, otp_code: str, purpose: str, user_name: Optional[str] = None) -> bool:
    """Send formatted branded OTP email via Resend HTTPS API, Brevo HTTPS API, or Django's configured email backend."""
    subject = f"Your IIMT UNIVERSITY Verification Code: {otp_code}"
    from_email = (
        getattr(settings, 'DEFAULT_FROM_EMAIL', '').strip() or
        os.getenv('DEFAULT_FROM_EMAIL', '').strip() or
        'EduSphere <onboarding@resend.dev>'
    )

    host_user = getattr(settings, 'EMAIL_HOST_USER', '').strip()
    if host_user and ('@gmail.com' in host_user) and not os.getenv('DEFAULT_FROM_EMAIL'):
        from_email = f"EduSphere Security <{host_user}>"

    context = {
        'otp_code': otp_code,
        'purpose': purpose,
        'expires_minutes': OTP_EXPIRY_MINUTES,
        'user_name': user_name,
    }

    html_message = render_to_string('accounts/otp_email.html', context)
    text_message = (
        f"Your IIMT UNIVERSITY verification code is: {otp_code}\n\n"
        f"This code will expire in {OTP_EXPIRY_MINUTES} minutes.\n"
        f"Do not share this code with anyone.\n\n"
        f"IIMT UNIVERSITY Academic Administration"
    )

    # 1. First priority: Resend HTTPS REST API (Port 443 - works everywhere including Render Free Tier)
    resend_api_key = (
        getattr(settings, 'RESEND_API_KEY', '').strip() or
        os.getenv('RESEND_API_KEY', '').strip()
    )
    if resend_api_key:
        return dispatch_via_resend(
            api_key=resend_api_key,
            from_email=from_email,
            to_email=email,
            subject=subject,
            html_message=html_message,
            text_message=text_message
        )

    # 2. Second priority: Brevo HTTPS REST API (Port 443 - works everywhere including Render Free Tier)
    brevo_api_key = (
        getattr(settings, 'BREVO_API_KEY', '').strip() or
        os.getenv('BREVO_API_KEY', '').strip()
    )
    if brevo_api_key:
        brevo_from = getattr(settings, 'BREVO_FROM_EMAIL', '').strip() or from_email
        return dispatch_via_brevo(
            api_key=brevo_api_key,
            from_email=brevo_from,
            to_email=email,
            subject=subject,
            html_message=html_message,
            text_message=text_message
        )

    # 3. Third priority: Standard Django email backend (SMTP or Console)
    # In production without email credentials, do NOT pretend email was sent via console
    is_testing = getattr(settings, 'IS_RUNNING_TESTS', False) or 'locmem.EmailBackend' in getattr(settings, 'EMAIL_BACKEND', '')
    if not settings.DEBUG and not is_testing:
        if not host_user or not getattr(settings, 'EMAIL_HOST_PASSWORD', '').strip():
            logger.error("No production email credentials configured in environment.")
            raise OTPError(
                "Email delivery service is unconfigured. Please configure RESEND_API_KEY (recommended for Render) or EMAIL_HOST_USER and EMAIL_HOST_PASSWORD (for Gmail SMTP) in your Render environment variables.",
                code="email_service_unconfigured",
                status_code=503
            )

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=from_email,
        to=[email]
    )
    msg.attach_alternative(html_message, "text/html")

    # If SMTP backend is selected, check that credentials have been configured
    backend = getattr(settings, 'EMAIL_BACKEND', '')
    if 'smtp.EmailBackend' in backend:
        if not host_user or not getattr(settings, 'EMAIL_HOST_PASSWORD', '').strip():
            logger.error("SMTP backend is active but EMAIL_HOST_USER or EMAIL_HOST_PASSWORD is missing in .env.")
            raise OTPError(
                "SMTP email delivery is active, but EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are not configured. Please add your credentials in Render environment variables, or provide a RESEND_API_KEY or BREVO_API_KEY.",
                code="smtp_credentials_missing",
                status_code=503
            )

    try:
        msg.send(fail_silently=False)
        logger.info(f"Verification OTP email dispatched successfully to {email}")
        if 'smtp.EmailBackend' in backend:
            print(f"\n[REAL MAILBOX DELIVERY - SMTP] ==============================")
            print(f" Recipient Email : {email}")
            print(f" Dispatched Via  : {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
            print(f" Sender Address  : {from_email}")
            print(f" Status          : Sent to user inbox successfully")
            print(f"==============================================================\n")
        elif 'console.EmailBackend' in backend or (settings.DEBUG and not getattr(settings, 'IS_RUNNING_TESTS', False)):
            # Print console banner for developer testing
            print(f"\n[DEV MODE - CONSOLE BACKEND] ========================================")
            print(f" Target User Email : {email}")
            print(f" 6-Digit OTP Code  : {otp_code}")
            print(f" Expires In        : {OTP_EXPIRY_MINUTES} minutes")
            print(f" Purpose           : {purpose}")
            print(f"====================================================================\n")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failure sending to {email}: {e}")
        raise OTPError(
            "SMTP authentication failed. If you are using Gmail, please use a 16-character Google App Password (not your normal Gmail account password) from https://myaccount.google.com/apppasswords.",
            code="smtp_auth_failed",
            status_code=500
        )
    except smtplib.SMTPSenderRefused as e:
        logger.error(f"SMTP Sender refused sending to {email}: {e}")
        raise OTPError(
            f"SMTP sender was rejected: {e.smtp_error.decode() if hasattr(e.smtp_error, 'decode') else str(e)}.",
            code="smtp_sender_refused",
            status_code=500
        )
    except (socket.timeout, TimeoutError, ConnectionRefusedError, OSError) as e:
        logger.error(f"SMTP connection failure dispatching to {email}: {e}")
        raise OTPError(
            "SMTP email connection failed or timed out. Note: Render free tier blocks outbound SMTP ports (587, 465, 25). To deliver emails on Render free tier, add RESEND_API_KEY in your Render dashboard environment variables, or upgrade your Render instance to allow outbound SMTP.",
            code="smtp_blocked_or_timeout",
            status_code=503
        )
    except Exception as e:
        logger.error(f"Failed to dispatch OTP email to {email}: {e}")
        raise OTPError(
            f"Unable to deliver verification email: {str(e)}",
            code="delivery_failed",
            status_code=500
        )


def create_otp_challenge(
    email: str,
    purpose: str = EmailOTPChallenge.Purpose.LOGIN,
    ip_address: Optional[str] = None,
    enforce_cooldown: bool = True
) -> Tuple[EmailOTPChallenge, int]:
    """
    Creates a new secure OTP challenge, stores hashed OTP, and dispatches email.
    Returns (challenge_object, remaining_cooldown_seconds).
    """
    normalized_email = normalize_email(email)

    # Enforce rate limits & cooldown
    if enforce_cooldown:
        check_resend_cooldown(normalized_email)
    check_rate_limits(normalized_email, ip_address)

    # Invalidate previous unverified challenges for this email
    EmailOTPChallenge.objects.filter(
        email=normalized_email,
        is_used=False
    ).update(is_used=True)

    # Locate user if existing
    user = User.objects.filter(email__iexact=normalized_email, is_active=True).first()
    user_name = user.get_full_name() or user.username if user else None

    # Generate cryptographically secure OTP & hash
    plain_otp = generate_cryptographic_otp(length=6)
    hashed_otp = make_password(plain_otp)

    now = timezone.now()
    expires_at = now + datetime.timedelta(minutes=OTP_EXPIRY_MINUTES)

    challenge = EmailOTPChallenge.objects.create(
        email=normalized_email,
        otp_hash=hashed_otp,
        purpose=purpose,
        user=user,
        expires_at=expires_at,
        attempts=0,
        max_attempts=MAX_ATTEMPTS_PER_CHALLENGE,
        is_verified=False,
        is_used=False,
        ip_address=ip_address
    )

    # Dispatch email (plain_otp is strictly used here and not saved)
    dispatch_otp_email(
        email=normalized_email,
        otp_code=plain_otp,
        purpose=purpose,
        user_name=user_name
    )

    return challenge, RESEND_COOLDOWN_SECONDS


def verify_otp_code(
    email: str,
    plain_otp: str,
    purpose: Optional[str] = None,
    mark_used: bool = True
) -> Tuple[bool, EmailOTPChallenge, Optional[User]]:
    """
    Verifies an OTP against the latest valid challenge.
    Returns (is_success, challenge, user).
    Raises OTPError if expired, max attempts reached, or invalid.
    """
    normalized_email = normalize_email(email)
    clean_otp = str(plain_otp).strip()

    if not clean_otp or len(clean_otp) != 6 or not clean_otp.isdigit():
        raise OTPError("Please enter a valid 6-digit verification code.", code="invalid_format")

    # Look up the latest challenge for this email
    qs = EmailOTPChallenge.objects.filter(email=normalized_email).order_by('-created_at')
    if purpose:
        qs = qs.filter(purpose=purpose)

    challenge = qs.first()
    if not challenge:
        raise OTPError("No active verification code found for this email. Please request a new code.", code="no_challenge")

    if challenge.is_used and challenge.is_verified:
        raise OTPError("This verification code has already been used. Please request a new code.", code="already_used")

    if challenge.is_expired:
        raise OTPError("This verification code has expired. Please request a new code.", code="expired")

    if challenge.attempts >= challenge.max_attempts:
        challenge.is_used = True
        challenge.save(update_fields=['is_used'])
        raise OTPError("Too many incorrect attempts. This code is now invalid. Please request a new code.", code="max_attempts_exceeded")

    # If already verified in step 1 and awaiting profile completion
    if challenge.is_verified and not challenge.is_used:
        from django.contrib.auth.hashers import check_password
        if not check_password(clean_otp, challenge.otp_hash):
            raise OTPError("Incorrect verification code.", code="incorrect_otp")
        if mark_used:
            challenge.is_used = True
            challenge.save(update_fields=['is_used'])
        user = challenge.user or User.objects.filter(email__iexact=normalized_email, is_active=True).first()
        return True, challenge, user

    # Perform verification
    success = challenge.verify(clean_otp, mark_used=mark_used)
    if not success:
        remaining_attempts = max(0, challenge.max_attempts - challenge.attempts)
        if remaining_attempts == 0:
            challenge.is_used = True
            challenge.save(update_fields=['is_used'])
            raise OTPError("Maximum attempts reached. This verification code has been invalidated.", code="max_attempts_exceeded")
        raise OTPError(
            f"Incorrect verification code. {remaining_attempts} attempt{'s' if remaining_attempts != 1 else ''} remaining.",
            code="incorrect_otp"
        )

    # Look up matching user
    user = challenge.user
    if not user:
        user = User.objects.filter(email__iexact=normalized_email, is_active=True).first()

    return True, challenge, user
