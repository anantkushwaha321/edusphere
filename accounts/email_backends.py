"""
EduSphere - Custom Django Email Backend for Resend HTTPS REST API.
Dispatches emails via https://api.resend.com/emails over port 443.
Immune to cloud SMTP port blocking (Render free tier blocks ports 25, 465, 587).
Requires no external dependencies (uses Python standard library urllib.request).
"""
import io
import json
import logging
import urllib.request
import urllib.error
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def mask_email_address(email: str) -> str:
    """Mask email for safe diagnostic logging without exposing PII (e.g. j***e@example.com)."""
    if not email or '@' not in email:
        return '***'
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[:1] + '*'
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


class ResendEmailBackend(BaseEmailBackend):
    """
    Production-ready Django email backend sending through Resend's REST API.
    Reads RESEND_API_KEY and DEFAULT_FROM_EMAIL from settings / environment.
    """

    RESEND_API_URL = "https://api.resend.com/emails"

    def __init__(self, api_key: str = None, fail_silently: bool = False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = (api_key or getattr(settings, 'RESEND_API_KEY', '')).strip()

    def send_messages(self, email_messages):
        """Sends one or more EmailMessage objects via Resend HTTPS API."""
        if not email_messages:
            return 0

        if not self.api_key:
            if self.fail_silently:
                return 0
            raise ValueError(
                "RESEND_API_KEY is not configured in environment variables."
            )

        num_sent = 0
        for message in email_messages:
            sent = self._send_single_message(message)
            if sent:
                num_sent += 1
        return num_sent

    def _send_single_message(self, message) -> bool:
        """Sends a single message to Resend."""
        # Extract HTML alternative if present
        html_content = None
        if isinstance(message, EmailMultiAlternatives) and getattr(message, 'alternatives', None):
            for alt_content, alt_mimetype in message.alternatives:
                if alt_mimetype == "text/html":
                    html_content = alt_content
                    break

        sender = (
            message.from_email.strip()
            if getattr(message, 'from_email', None) and message.from_email.strip()
            else getattr(settings, 'DEFAULT_FROM_EMAIL', 'EduSphere <onboarding@resend.dev>')
        )

        payload = {
            "from": sender,
            "to": list(message.to),
            "subject": message.subject,
            "text": message.body,
        }
        if html_content:
            payload["html"] = html_content
        if getattr(message, 'cc', None):
            payload["cc"] = list(message.cc)
        if getattr(message, 'bcc', None):
            payload["bcc"] = list(message.bcc)
        if getattr(message, 'reply_to', None):
            payload["reply_to"] = message.reply_to[0] if len(message.reply_to) == 1 else list(message.reply_to)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "EduSphere-Academic-PaaS/1.0",
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.RESEND_API_URL,
            data=data,
            headers=headers,
            method="POST"
        )

        timeout = int(getattr(settings, 'EMAIL_TIMEOUT', 10))

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_body = resp.read().decode('utf-8', errors='ignore')
                resp_json = {}
                if resp_body:
                    try:
                        resp_json = json.loads(resp_body)
                    except Exception:
                        pass

                email_id = resp_json.get('id', 'accepted')
                if resp.status in (200, 201):
                    recipients = ", ".join(mask_email_address(r) for r in message.to)
                    logger.info("Resend successfully queued email (id=%s) for %s", email_id, recipients)
                    return True
                else:
                    logger.error("Resend returned unexpected status %s", resp.status)
                    if not self.fail_silently:
                        raise RuntimeError(f"Resend returned unexpected status {resp.status}")
                    return False
        except urllib.error.HTTPError as err:
            err_body = err.read().decode('utf-8', errors='ignore')
            err_msg = 'Unknown error'
            err_name = 'api_error'
            try:
                parsed = json.loads(err_body)
                err_msg = parsed.get('message', err_body)
                err_name = parsed.get('name', 'api_error')
            except Exception:
                err_msg = err_body[:200]

            logger.error("Resend API rejected message (HTTP %s, type=%s): %s", err.code, err_name, err_msg)
            if not self.fail_silently:
                raise
            return False
        except Exception as err:
            logger.error("Failed to dispatch email via Resend API: %s", err)
            if not self.fail_silently:
                raise
            return False
