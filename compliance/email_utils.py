import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse
from .models import EmailPreference

logger = logging.getLogger(__name__)


def send_compliance_email(
    user,
    subject,
    text_content,
    html_content=None,
    category='academic_announcements'
):
    """
    Sends an email with strict compliance guarantees:
    1. Checks user's opt-out preferences for the given category
    2. Appends RFC 2369 / RFC 8058 List-Unsubscribe headers
    3. Adds a clear 1-click unsubscribe footer link
    4. Includes official institutional business entity details
    """
    # Check user preferences
    pref, _ = EmailPreference.objects.get_or_create(user=user)
    if category != 'essential':
        allowed = getattr(pref, category, True)
        if not allowed:
            logger.info(f"Skipping email to {user.email} due to user opt-out on category {category}")
            return False

    base_url = getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000')
    unsub_url = f"{base_url}{reverse('compliance:unsubscribe_token', kwargs={'token': pref.unsubscribe_token})}"

    # Build compliant footer
    compliance_footer_text = f"""
---
You are receiving this communication as a registered member of IIMT UNIVERSITY.
Entity: IIMT UNIVERSITY, 'O' Pocket, Ganga Nagar, Meerut, Uttar Pradesh 250001, India
Contact: privacy@iimtindia.net | +91 121 279 3500

To manage your email preferences or unsubscribe from non-essential messages at any time:
{unsub_url}
"""

    compliance_footer_html = f"""
<hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0 20px 0;" />
<div style="font-size: 11px; color: #64748b; line-height: 1.5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <p style="margin: 0 0 6px 0;"><strong>IIMT UNIVERSITY</strong> &bull; Official Institutional Notification</p>
    <p style="margin: 0 0 8px 0;">'O' Pocket, Ganga Nagar, Meerut, UP 250001 &bull; Privacy Officer: <a href="mailto:privacy@iimtindia.net" style="color: #4f46e5;">privacy@iimtindia.net</a></p>
    <p style="margin: 0;">
        You can <a href="{unsub_url}" style="color: #4f46e5; text-decoration: underline;">unsubscribe from these notifications</a> or update your <a href="{base_url}{reverse('compliance:email_preferences')}" style="color: #4f46e5; text-decoration: underline;">email delivery preferences</a>.
    </p>
</div>
"""

    full_text = text_content + "\n\n" + compliance_footer_text

    msg = EmailMultiAlternatives(
        subject=subject,
        body=full_text,
        from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'notifications@iimtindia.net',
        to=[user.email]
    )

    if html_content:
        full_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px;">
            {html_content}
            {compliance_footer_html}
        </div>
        """
        msg.attach_alternative(full_html, "text/html")

    # Add RFC List-Unsubscribe headers
    msg.extra_headers['List-Unsubscribe'] = f"<{unsub_url}>"
    msg.extra_headers['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'

    try:
        msg.send(fail_silently=False)
        return True
    except Exception as e:
        logger.warning(f"Failed to send email to {user.email}: {e}")
        return False
