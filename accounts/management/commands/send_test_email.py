import sys
import smtplib
import socket
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class Command(BaseCommand):
    help = 'Tests real SMTP email delivery by sending a live verification email to a specified recipient.'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Recipient email address to receive the test verification code.'
        )

    def handle(self, *args, **options):
        recipient = options['email'].strip()

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== IIMT UNIVERSITY — SMTP Email Delivery Test ==="))
        self.stdout.write(f"Recipient:       {recipient}")
        self.stdout.write(f"EMAIL_BACKEND:   {settings.EMAIL_BACKEND}")
        self.stdout.write(f"EMAIL_HOST:      {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        self.stdout.write(f"EMAIL_USE_TLS:   {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"EMAIL_USE_SSL:   {settings.EMAIL_USE_SSL}")
        self.stdout.write(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER or '(Not set)'}")
        has_pwd = bool(settings.EMAIL_HOST_PASSWORD)
        self.stdout.write(f"EMAIL_PASSWORD:  {'[CONFIGURED - ' + str(len(settings.EMAIL_HOST_PASSWORD)) + ' chars]' if has_pwd else '(Not set)'}")
        self.stdout.write(f"DEFAULT_FROM:    {settings.DEFAULT_FROM_EMAIL}\n")

        backend = getattr(settings, 'EMAIL_BACKEND', '')

        # Warn if console backend
        if 'console.EmailBackend' in backend:
            self.stdout.write(self.style.WARNING(
                "[NOTICE] EMAIL_BACKEND is set to console. The email will be printed in this terminal.\n"
                "To deliver to a real inbox over the internet, set:\n"
                "  EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend\n"
                "  EMAIL_HOST_USER=your_email@gmail.com\n"
                "  EMAIL_HOST_PASSWORD=your_16_char_app_password\n"
                "in your .env file.\n"
            ))

        # Check SMTP credentials if SMTP backend
        if 'smtp.EmailBackend' in backend:
            if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
                self.stdout.write(self.style.ERROR(
                    "[ERROR] SMTP backend is active, but EMAIL_HOST_USER or EMAIL_HOST_PASSWORD is missing in .env!\n"
                    "Please edit your .env file and set:\n"
                    "  EMAIL_HOST_USER=your_email@gmail.com\n"
                    "  EMAIL_HOST_PASSWORD=your_app_password\n"
                ))
                sys.exit(1)

        self.stdout.write("Rendering branded email template...")
        test_otp = "842915"
        context = {
            'otp_code': test_otp,
            'purpose': 'LOGIN',
            'expires_minutes': 5,
            'user_name': 'Test Recipient',
        }

        html_content = render_to_string('accounts/otp_email.html', context)
        text_content = (
            f"Your IIMT UNIVERSITY test verification code is: {test_otp}\n\n"
            f"This is a test verification email from EduSphere.\n\n"
            f"IIMT UNIVERSITY Academic Administration"
        )

        msg = EmailMultiAlternatives(
            subject=f"Your IIMT UNIVERSITY Verification Code: {test_otp} [TEST]",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient]
        )
        msg.attach_alternative(html_content, "text/html")

        self.stdout.write("Connecting and dispatching email...")
        try:
            msg.send(fail_silently=False)
            self.stdout.write(self.style.SUCCESS(
                f"\n[SUCCESS] Test verification email successfully sent to {recipient}!\n"
                f"Please check your inbox (and spam/junk folder) for the 6-digit code: {test_otp}."
            ))
        except smtplib.SMTPAuthenticationError as e:
            self.stdout.write(self.style.ERROR(
                f"\n[AUTHENTICATION FAILED] {e}\n"
                "Common Causes:\n"
                "1. If using Gmail: You must generate a 16-character App Password at:\n"
                "   https://myaccount.google.com/apppasswords\n"
                "   (Standard Gmail passwords will be rejected by Google's SMTP servers).\n"
                "2. 2-Step Verification must be turned on in your Google Account before generating an App Password.\n"
                "3. Ensure there are no spaces or quotes around the password in your .env file."
            ))
            sys.exit(1)
        except smtplib.SMTPSenderRefused as e:
            self.stdout.write(self.style.ERROR(
                f"\n[SENDER REFUSED] {e}\n"
                "The SMTP server rejected the sender address.\n"
                f"Make sure DEFAULT_FROM_EMAIL matches EMAIL_HOST_USER ({settings.EMAIL_HOST_USER})."
            ))
            sys.exit(1)
        except (socket.timeout, TimeoutError) as e:
            self.stdout.write(self.style.ERROR(
                f"\n[CONNECTION TIMEOUT] {e}\n"
                f"Could not connect to {settings.EMAIL_HOST}:{settings.EMAIL_PORT}.\n"
                "Check if port 587 or outbound SMTP is blocked by your firewall or ISP."
            ))
            sys.exit(1)
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"\n[ERROR] Delivery failed: {str(e)}"
            ))
            sys.exit(1)
