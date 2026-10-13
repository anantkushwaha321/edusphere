import os
import sys
import smtplib
import re
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class Command(BaseCommand):
    help = 'Interactive wizard to configure and test Gmail SMTP for Real Mailbox Delivery in EduSphere.'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Your Gmail address (e.g. admin@gmail.com)')
        parser.add_argument('--password', type=str, help='Your 16-character Google App Password')
        parser.add_argument('--test-recipient', type=str, help='Email address to receive a live test verification code')

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== IIMT UNIVERSITY — Gmail SMTP Real Delivery Setup ==="))
        self.stdout.write("This tool configures live email delivery so OTP verification codes are sent")
        self.stdout.write("directly to users' real inboxes via Gmail SMTP.\n")

        email = (options.get('email') or '').strip()
        password = (options.get('password') or '').strip()
        test_recipient = (options.get('test_recipient') or '').strip()

        # Step 1: Prompt for Gmail Address if not provided
        if not email:
            try:
                email = input("1. Enter your Gmail address: ").strip()
            except (KeyboardInterrupt, EOFError):
                self.stdout.write(self.style.WARNING("\nSetup cancelled."))
                return

        if not email or '@' not in email:
            self.stdout.write(self.style.ERROR("Invalid email address format. Setup aborted."))
            return

        # Step 2: Prompt for 16-character App Password if not provided
        if not password:
            self.stdout.write("\nGoogle requires a 16-character 'App Password' for SMTP access.")
            self.stdout.write("If you do not have one yet:")
            self.stdout.write("  1. Go to: https://myaccount.google.com/apppasswords")
            self.stdout.write("  2. Ensure 2-Step Verification is turned on in your Google Account.")
            self.stdout.write("  3. Create an app named 'EduSphere' and copy the 16-letter password.\n")
            try:
                password = input("2. Enter your 16-character Google App Password: ").strip()
            except (KeyboardInterrupt, EOFError):
                self.stdout.write(self.style.WARNING("\nSetup cancelled."))
                return

        # Clean spaces in app password (Google displays it like 'abcd efgh ijkl mnop')
        clean_password = password.replace(" ", "").strip()

        if len(clean_password) < 8:
            self.stdout.write(self.style.ERROR("App password appears too short. Google App Passwords are 16 characters."))
            return

        # Step 3: Test SMTP handshake and authentication
        self.stdout.write(f"\nTesting connection to smtp.gmail.com:587 for {email}...")
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(email, clean_password)
            server.quit()
            self.stdout.write(self.style.SUCCESS("[SUCCESS] Gmail SMTP authentication successful!"))
        except smtplib.SMTPAuthenticationError as e:
            self.stdout.write(self.style.ERROR(f"\n[AUTHENTICATION FAILED] {e}"))
            self.stdout.write("Possible causes:")
            self.stdout.write("1. You entered your normal Google Account password instead of an App Password.")
            self.stdout.write("2. 2-Step Verification is not enabled on your Google Account.")
            self.stdout.write("3. The App Password was typed incorrectly.")
            self.stdout.write("Generate a fresh 16-character App Password at: https://myaccount.google.com/apppasswords")
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n[CONNECTION ERROR] {e}"))
            return

        # Step 4: Update .env file
        env_path = Path(settings.BASE_DIR) / '.env'
        if env_path.exists():
            env_content = env_path.read_text(encoding='utf-8')
        else:
            env_content = ""

        # Update or set variables
        def set_or_replace_env(content: str, key: str, value: str) -> str:
            pattern = rf'^{key}=.*$'
            if re.search(pattern, content, flags=re.MULTILINE):
                return re.sub(pattern, f"{key}={value}", content, flags=re.MULTILINE)
            else:
                return content.rstrip() + f"\n{key}={value}\n"

        sender_from = f"IIMT UNIVERSITY Security <{email}>"
        env_content = set_or_replace_env(env_content, 'EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
        env_content = set_or_replace_env(env_content, 'EMAIL_HOST', 'smtp.gmail.com')
        env_content = set_or_replace_env(env_content, 'EMAIL_PORT', '587')
        env_content = set_or_replace_env(env_content, 'EMAIL_HOST_USER', email)
        env_content = set_or_replace_env(env_content, 'EMAIL_HOST_PASSWORD', clean_password)
        env_content = set_or_replace_env(env_content, 'EMAIL_USE_TLS', 'True')
        env_content = set_or_replace_env(env_content, 'EMAIL_USE_SSL', 'False')
        env_content = set_or_replace_env(env_content, 'DEFAULT_FROM_EMAIL', sender_from)

        env_path.write_text(env_content, encoding='utf-8')
        self.stdout.write(self.style.SUCCESS("[UPDATED] .env configuration file saved with Gmail SMTP settings."))

        # Step 5: Send live test email
        target_to = test_recipient or email
        self.stdout.write(f"\nSending live test verification email to {target_to}...")

        test_otp = "739201"
        context = {
            'otp_code': test_otp,
            'purpose': 'LOGIN',
            'expires_minutes': 5,
            'user_name': 'EduSphere Administrator',
        }
        html_msg = render_to_string('accounts/otp_email.html', context)
        text_msg = (
            f"Your IIMT UNIVERSITY test verification code is: {test_otp}\n\n"
            f"This email confirms that Real Mailbox Delivery via Gmail SMTP is fully operational.\n\n"
            f"IIMT UNIVERSITY Academic Administration"
        )

        try:
            # Create fresh SMTP backend with new credentials
            from django.core.mail.backends.smtp import EmailBackend
            backend = EmailBackend(
                host='smtp.gmail.com',
                port=587,
                username=email,
                password=clean_password,
                use_tls=True,
                fail_silently=False,
                timeout=15
            )
            msg = EmailMultiAlternatives(
                subject=f"Your IIMT UNIVERSITY Verification Code: {test_otp} [REAL SMTP TEST]",
                body=text_msg,
                from_email=sender_from,
                to=[target_to],
                connection=backend
            )
            msg.attach_alternative(html_msg, "text/html")
            msg.send(fail_silently=False)

            self.stdout.write(self.style.SUCCESS(
                f"\n[LIVE EMAIL DELIVERED] A verification email has been delivered to {target_to}!\n"
                f"Check your inbox to verify receipt of OTP code: {test_otp}."
            ))
            self.stdout.write("\nReal Mailbox Delivery is now 100% active on EduSphere!\n")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[FAILED TO SEND TEST EMAIL] {e}"))
