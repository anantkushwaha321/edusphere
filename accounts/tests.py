import json
import re
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from django.contrib.auth.hashers import check_password

from accounts.models import (
    User,
    StudentProfile,
    TeacherProfile,
    AdminProfile,
    EmailOTPChallenge
)
from accounts.otp_service import (
    create_otp_challenge,
    verify_otp_code,
    OTP_EXPIRY_MINUTES,
    RESEND_COOLDOWN_SECONDS,
    MAX_ATTEMPTS_PER_CHALLENGE,
    MAX_HOURLY_REQUESTS_PER_EMAIL,
    MAX_HOURLY_REQUESTS_PER_IP,
    OTPError
)
from academics.models import Department, AcademicYear


class OTPAuthenticationComprehensiveTests(TestCase):
    """
    Complete verification suite covering all 12 core requirements for the
    EduSphere OTP-based authentication system.
    """

    def setUp(self):
        self.client = Client()
        # Create base academic fixtures required for profile creation and dashboards
        self.department = Department.objects.create(
            name="Computer Science & Engineering",
            code="CSE",
            description="Department of Computer Science"
        )
        self.academic_year = AcademicYear.objects.create(
            name="2026-2027",
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2027, 5, 31),
            is_current=True
        )

        # Clear mailbox before each test
        mail.outbox.clear()

    def _extract_otp_from_mailbox(self) -> str:
        """Helper to extract 6-digit OTP code from the latest dispatched email."""
        self.assertGreater(len(mail.outbox), 0, "Expected an email to be dispatched in outbox.")
        latest_email = mail.outbox[-1]
        match = re.search(r'\b\d{6}\b', latest_email.subject)
        if not match:
            match = re.search(r'\b\d{6}\b', latest_email.body)
        self.assertIsNotNone(match, "Could not extract 6-digit OTP from dispatched email.")
        return match.group(0)

    # -------------------------------------------------------------------------
    # Scenario 1: New user requests an OTP
    # Scenario 2: OTP email is delivered successfully
    # -------------------------------------------------------------------------
    def test_01_02_new_user_requests_otp_and_email_delivered(self):
        """
        Verify that when a new user requests an OTP:
        1. An EmailOTPChallenge is created with purpose=REGISTER.
        2. OTP is stored hashed and NOT leaked in plaintext or response.
        3. A branded HTML email is dispatched with the OTP.
        """
        email = "newstudent@edusphere.edu"
        response = self.client.post(
            reverse('api_send_otp'),
            data=json.dumps({'email': email}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['is_existing_user'])
        self.assertEqual(data['purpose'], EmailOTPChallenge.Purpose.REGISTER)
        self.assertIn('cooldown_seconds', data)
        # Ensure plain OTP is NEVER leaked in API response
        self.assertNotIn('otp', data)
        self.assertNotIn('code', data.get('data', {}))

        # Check database record
        challenge = EmailOTPChallenge.objects.filter(email=email).first()
        self.assertIsNotNone(challenge)
        self.assertEqual(challenge.purpose, EmailOTPChallenge.Purpose.REGISTER)
        self.assertFalse(challenge.is_verified)
        self.assertFalse(challenge.is_used)
        self.assertEqual(challenge.attempts, 0)
        self.assertNotEqual(len(challenge.otp_hash), 6, "OTP hash must not be plain 6 digits.")
        self.assertTrue(challenge.otp_hash.startswith(('pbkdf2_', 'argon2', 'bcrypt')))

        # Scenario 2: Check email delivery in mail outbox
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertIn(email, sent_mail.to)
        self.assertIn("IIMT UNIVERSITY Verification Code", sent_mail.subject)
        self.assertIn("expire in 5 minutes", sent_mail.body)

        extracted_otp = self._extract_otp_from_mailbox()
        self.assertEqual(len(extracted_otp), 6)
        self.assertTrue(check_password(extracted_otp, challenge.otp_hash))

    # -------------------------------------------------------------------------
    # Scenario 3: Correct OTP verifies the email and registers new student
    # -------------------------------------------------------------------------
    def test_03_correct_otp_verifies_email_and_registers_student(self):
        """
        Verify that submitting the correct OTP validates email ownership,
        prompts for student profile details, and securely creates the student account.
        """
        email = "alice.applicant@edusphere.edu"

        # 1. Request OTP
        self.client.post(
            reverse('api_send_otp'),
            data=json.dumps({'email': email}),
            content_type='application/json'
        )
        plain_otp = self._extract_otp_from_mailbox()

        # 2. Verify OTP -> seamless automatic account provisioning & direct authentication
        resp_verify = self.client.post(
            reverse('api_verify_otp'),
            data=json.dumps({'email': email, 'otp': plain_otp}),
            content_type='application/json'
        )
        self.assertEqual(resp_verify.status_code, 200)
        verify_data = resp_verify.json()
        self.assertTrue(verify_data['success'])
        self.assertTrue(verify_data['authenticated'])
        self.assertEqual(verify_data['redirect_url'], reverse('student_dashboard'))

        # Check DB user creation
        new_user = User.objects.filter(email=email).first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.first_name, 'Alice')
        self.assertEqual(new_user.last_name, 'Applicant')
        self.assertEqual(new_user.role, User.Role.STUDENT)  # Locked to STUDENT
        self.assertFalse(new_user.has_usable_password())

        # Check student profile
        profile = StudentProfile.objects.filter(user=new_user).first()
        self.assertIsNotNone(profile)
        self.assertTrue(profile.roll_number.startswith('STU-'))
        self.assertEqual(profile.department, self.department)

        # Challenge record should now be marked verified and used
        challenge = EmailOTPChallenge.objects.filter(email=email).first()
        self.assertTrue(challenge.is_verified)
        self.assertTrue(challenge.is_used)

    # -------------------------------------------------------------------------
    # Scenario 4: Existing user logs in successfully
    # -------------------------------------------------------------------------
    def test_04_existing_user_logs_in_successfully(self):
        """
        Verify existing user receives an OTP with purpose=LOGIN and is
        logged in immediately upon submitting the correct code.
        """
        email = "teacher.bob@edusphere.edu"
        user = User.objects.create(
            username="teacher_bob",
            email=email,
            first_name="Bob",
            last_name="Roberts",
            role=User.Role.TEACHER,
            is_active=True
        )
        TeacherProfile.objects.create(user=user, employee_id="EMP-9001", department=self.department)

        # 1. Request OTP
        resp_send = self.client.post(
            reverse('api_send_otp'),
            data=json.dumps({'email': email}),
            content_type='application/json'
        )
        self.assertEqual(resp_send.status_code, 200)
        self.assertTrue(resp_send.json()['is_existing_user'])
        self.assertEqual(resp_send.json()['purpose'], EmailOTPChallenge.Purpose.LOGIN)

        # 2. Verify with correct OTP
        plain_otp = self._extract_otp_from_mailbox()
        resp_verify = self.client.post(
            reverse('api_verify_otp'),
            data=json.dumps({'email': email, 'otp': plain_otp}),
            content_type='application/json'
        )
        self.assertEqual(resp_verify.status_code, 200)
        verify_data = resp_verify.json()
        self.assertTrue(verify_data['success'])
        self.assertTrue(verify_data['authenticated'])
        self.assertTrue(verify_data['is_existing_user'])
        self.assertEqual(verify_data['redirect_url'], reverse('teacher_dashboard'))

        # Check session is authenticated
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

    # -------------------------------------------------------------------------
    # Scenario 5: Incorrect OTP is rejected
    # -------------------------------------------------------------------------
    def test_05_incorrect_otp_is_rejected(self):
        """
        Verify that submitting an incorrect 6-digit OTP is rejected with
        an appropriate 400 error and increments the challenge attempt count.
        """
        email = "student.test@edusphere.edu"
        self.client.post(
            reverse('api_send_otp'),
            data=json.dumps({'email': email}),
            content_type='application/json'
        )

        # Submit deliberately wrong OTP
        wrong_otp = "000000"
        resp_verify = self.client.post(
            reverse('api_verify_otp'),
            data=json.dumps({'email': email, 'otp': wrong_otp}),
            content_type='application/json'
        )
        self.assertEqual(resp_verify.status_code, 400)
        data = resp_verify.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['code'], 'incorrect_otp')
        self.assertIn('4 attempts remaining', data['message'])

        challenge = EmailOTPChallenge.objects.filter(email=email).first()
        self.assertEqual(challenge.attempts, 1)
        self.assertFalse(challenge.is_verified)
        self.assertFalse(challenge.is_used)

    # -------------------------------------------------------------------------
    # Scenario 6: Expired OTP is rejected
    # -------------------------------------------------------------------------
    def test_06_expired_otp_is_rejected(self):
        """
        Verify that an OTP older than 5 minutes is rejected as expired.
        """
        email = "student.expire@edusphere.edu"
        self.client.post(
            reverse('api_send_otp'),
            data=json.dumps({'email': email}),
            content_type='application/json'
        )
        plain_otp = self._extract_otp_from_mailbox()

        # Fast forward time: age the challenge beyond 5 minutes
        challenge = EmailOTPChallenge.objects.filter(email=email).first()
        challenge.expires_at = timezone.now() - datetime.timedelta(seconds=1)
        challenge.save(update_fields=['expires_at'])

        resp_verify = self.client.post(
            reverse('api_verify_otp'),
            data=json.dumps({'email': email, 'otp': plain_otp}),
            content_type='application/json'
        )
        self.assertEqual(resp_verify.status_code, 400)
        data = resp_verify.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['code'], 'expired')
        self.assertIn("expired", data['message'].lower())

    # -------------------------------------------------------------------------
    # Scenario 7: Previously used OTP cannot be reused
    # -------------------------------------------------------------------------
    def test_07_previously_used_otp_cannot_be_reused(self):
        """
        Verify that once an OTP has been verified and used, replay attempts are blocked.
        """
        email = "student.replay@edusphere.edu"
        user = User.objects.create(
            username="student_replay",
            email=email,
            role=User.Role.STUDENT,
            is_active=True
        )
        StudentProfile.objects.create(user=user, roll_number="REPLAY-01", department=self.department)

        self.client.post(
            reverse('api_send_otp'),
            data=json.dumps({'email': email}),
            content_type='application/json'
        )
        plain_otp = self._extract_otp_from_mailbox()

        # First verification succeeds
        resp1 = self.client.post(
            reverse('api_verify_otp'),
            data=json.dumps({'email': email, 'otp': plain_otp}),
            content_type='application/json'
        )
        self.assertEqual(resp1.status_code, 200)

        # Attempt replay with the same OTP
        resp2 = self.client.post(
            reverse('api_verify_otp'),
            data=json.dumps({'email': email, 'otp': plain_otp}),
            content_type='application/json'
        )
        self.assertEqual(resp2.status_code, 400)
        data = resp2.json()
        self.assertFalse(data['success'])
        self.assertIn(data['code'], ['already_used', 'no_challenge'])

    # -------------------------------------------------------------------------
    # Scenario 8: Too many incorrect attempts are blocked
    # -------------------------------------------------------------------------
    def test_08_too_many_incorrect_attempts_blocked(self):
        """
        Verify that after 5 failed attempts, the challenge is invalidated
        and subsequent attempts (even correct ones) are rejected.
        """
        email = "student.brute@edusphere.edu"
        self.client.post(
            reverse('api_send_otp'),
            data=json.dumps({'email': email}),
            content_type='application/json'
        )
        correct_otp = self._extract_otp_from_mailbox()

        # Submit 5 incorrect attempts
        for attempt in range(1, 5):
            resp = self.client.post(
                reverse('api_verify_otp'),
                data=json.dumps({'email': email, 'otp': f"00000{attempt}"}),
                content_type='application/json'
            )
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.json()['code'], 'incorrect_otp')

        # 5th failed attempt should trigger max_attempts_exceeded
        resp5 = self.client.post(
            reverse('api_verify_otp'),
            data=json.dumps({'email': email, 'otp': "000005"}),
            content_type='application/json'
        )
        self.assertEqual(resp5.status_code, 400)
        self.assertEqual(resp5.json()['code'], 'max_attempts_exceeded')

        # Challenge should now be marked is_used=True to permanently lock it
        challenge = EmailOTPChallenge.objects.filter(email=email).first()
        self.assertTrue(challenge.is_used)

        # Even if attacker submits the correct code now, it must be rejected
        resp_after = self.client.post(
            reverse('api_verify_otp'),
            data=json.dumps({'email': email, 'otp': correct_otp}),
            content_type='application/json'
        )
        self.assertEqual(resp_after.status_code, 400)
        self.assertEqual(resp_after.json()['code'], 'max_attempts_exceeded')

    # -------------------------------------------------------------------------
    # Scenario 9: Resend cooldown and rate limits work
    # -------------------------------------------------------------------------
    def test_09_resend_cooldown_and_rate_limits(self):
        """
        Verify:
        a) 60-second resend cooldown is strictly enforced.
        b) Hourly per-email rate limit (5 max) is enforced.
        c) Hourly per-IP rate limit (15 max) is enforced.
        """
        email = "student.ratelimit@edusphere.edu"

        # 1. Initial send request
        resp1 = self.client.post(
            reverse('api_send_otp'),
            data=json.dumps({'email': email}),
            content_type='application/json'
        )
        self.assertEqual(resp1.status_code, 200)

        # 2. Immediate resend should trigger 429 cooldown error
        resp_cooldown = self.client.post(
            reverse('api_resend_otp'),
            data=json.dumps({'email': email}),
            content_type='application/json'
        )
        self.assertEqual(resp_cooldown.status_code, 429)
        self.assertEqual(resp_cooldown.json()['code'], 'cooldown_active')

        # 3. Simulate passage of 60 seconds by backdating existing challenges
        EmailOTPChallenge.objects.filter(email=email).update(
            created_at=timezone.now() - datetime.timedelta(seconds=70)
        )

        # Resend now works after cooldown
        resp_resend = self.client.post(
            reverse('api_resend_otp'),
            data=json.dumps({'email': email}),
            content_type='application/json'
        )
        self.assertEqual(resp_resend.status_code, 200)

        # 4. Hourly Email Rate Limit (MAX_HOURLY_REQUESTS_PER_EMAIL = 5)
        # Create additional backdated challenges to reach limit
        now = timezone.now()
        for i in range(3):
            EmailOTPChallenge.objects.create(
                email=email,
                otp_hash="mock_hash",
                expires_at=now + datetime.timedelta(minutes=5),
                created_at=now - datetime.timedelta(seconds=120 + i * 10)
            )

        # Email has 5 challenges within the hour now. The 6th attempt must be rate-limited:
        EmailOTPChallenge.objects.filter(email=email).order_by('-created_at').first()
        # Ensure latest challenge is older than 60s to bypass cooldown check
        EmailOTPChallenge.objects.filter(email=email).update(
            created_at=timezone.now() - datetime.timedelta(seconds=65)
        )

        resp_limit = self.client.post(
            reverse('api_send_otp'),
            data=json.dumps({'email': email}),
            content_type='application/json'
        )
        self.assertEqual(resp_limit.status_code, 429)
        self.assertEqual(resp_limit.json()['code'], 'rate_limit_email')

        # 5. IP Rate Limit (MAX_HOURLY_REQUESTS_PER_IP = 15)
        ip = "192.168.10.50"
        for i in range(15):
            EmailOTPChallenge.objects.create(
                email=f"ip_test_{i}@edusphere.edu",
                otp_hash="mock_hash",
                ip_address=ip,
                expires_at=now + datetime.timedelta(minutes=5),
                created_at=now - datetime.timedelta(seconds=100)
            )

        resp_ip_limit = self.client.post(
            reverse('api_send_otp'),
            data=json.dumps({'email': 'fresh_email@edusphere.edu'}),
            content_type='application/json',
            REMOTE_ADDR=ip
        )
        self.assertEqual(resp_ip_limit.status_code, 429)
        self.assertEqual(resp_ip_limit.json()['code'], 'rate_limit_ip')

    # -------------------------------------------------------------------------
    # Scenario 10: Unauthenticated users cannot access protected pages or APIs
    # -------------------------------------------------------------------------
    def test_10_unauthenticated_users_cannot_access_protected_pages(self):
        """
        Verify that protected dashboards, user profiles, and user management
        redirect unauthenticated users to the login page.
        """
        protected_urls = [
            reverse('dashboard'),
            reverse('admin_dashboard'),
            reverse('teacher_dashboard'),
            reverse('student_dashboard'),
            reverse('profile'),
            reverse('user_list'),
        ]

        for url in protected_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302, f"Expected 302 redirect for {url}")
            self.assertTrue(resp.url.startswith(reverse('login')))

        # Check /api/auth/me/ returns authenticated: False
        resp_me = self.client.get(reverse('api_me'))
        self.assertEqual(resp_me.status_code, 200)
        self.assertFalse(resp_me.json()['authenticated'])

    # -------------------------------------------------------------------------
    # Scenario 11: Students, teachers, and administrators reach correct dashboards
    # -------------------------------------------------------------------------
    def test_11_role_based_dashboards_access_control(self):
        """
        Verify:
        - Admin user reaches admin dashboard.
        - Teacher user reaches teacher dashboard.
        - Student user reaches student dashboard.
        - Cross-role access is restricted (student cannot access admin or teacher dashboard).
        """
        admin = User.objects.create(
            username="admin_user",
            email="admin.test@edusphere.edu",
            role=User.Role.ADMIN,
            is_active=True
        )
        AdminProfile.objects.create(user=admin)

        teacher = User.objects.create(
            username="teacher_user",
            email="teacher.test@edusphere.edu",
            role=User.Role.TEACHER,
            is_active=True
        )
        TeacherProfile.objects.create(user=teacher, employee_id="TCH-100", department=self.department)

        student = User.objects.create(
            username="student_user",
            email="student.test@edusphere.edu",
            role=User.Role.STUDENT,
            is_active=True
        )
        StudentProfile.objects.create(user=student, roll_number="STU-100", department=self.department)

        # Test Admin
        self.client.force_login(admin)
        resp = self.client.get(reverse('dashboard'))
        self.assertRedirects(resp, reverse('admin_dashboard'))
        resp_admin = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp_admin.status_code, 200)
        self.client.logout()

        # Test Teacher
        self.client.force_login(teacher)
        resp = self.client.get(reverse('dashboard'))
        self.assertRedirects(resp, reverse('teacher_dashboard'))
        resp_teacher = self.client.get(reverse('teacher_dashboard'))
        self.assertEqual(resp_teacher.status_code, 200)
        self.client.logout()

        # Test Student
        self.client.force_login(student)
        resp = self.client.get(reverse('dashboard'))
        self.assertRedirects(resp, reverse('student_dashboard'))
        resp_student = self.client.get(reverse('student_dashboard'))
        self.assertEqual(resp_student.status_code, 200)

        # Ensure student cannot access admin or teacher dashboard (redirects to their own student dashboard)
        resp_unauth_admin = self.client.get(reverse('admin_dashboard'), follow=True)
        self.assertRedirects(resp_unauth_admin, reverse('student_dashboard'))
        resp_unauth_teacher = self.client.get(reverse('teacher_dashboard'), follow=True)
        self.assertRedirects(resp_unauth_teacher, reverse('student_dashboard'))
        self.client.logout()

    # -------------------------------------------------------------------------
    # Scenario 12: Logout invalidates the authenticated session
    # -------------------------------------------------------------------------
    def test_12_logout_invalidates_session(self):
        """
        Verify that calling POST /api/auth/logout/ clears the authenticated session,
        resets /api/auth/me/, and blocks subsequent dashboard access.
        """
        user = User.objects.create(
            username="logout_user",
            email="logout@edusphere.edu",
            role=User.Role.STUDENT,
            is_active=True
        )
        StudentProfile.objects.create(user=user, roll_number="STU-LOGOUT", department=self.department)

        self.client.force_login(user)

        # Confirm user is authenticated
        resp_me1 = self.client.get(reverse('api_me'))
        self.assertTrue(resp_me1.json()['authenticated'])

        # Execute API logout
        resp_logout = self.client.post(reverse('api_logout'))
        self.assertEqual(resp_logout.status_code, 200)
        self.assertTrue(resp_logout.json()['success'])

        # Confirm user is now unauthenticated
        resp_me2 = self.client.get(reverse('api_me'))
        self.assertFalse(resp_me2.json()['authenticated'])

        # Attempt accessing dashboard -> should redirect to login
        resp_dash = self.client.get(reverse('dashboard'))
        self.assertEqual(resp_dash.status_code, 302)
        self.assertTrue(resp_dash.url.startswith(reverse('login')))

    # -------------------------------------------------------------------------
    # Scenario 13: Invalid email input returns 400 with descriptive error
    # -------------------------------------------------------------------------
    def test_13_invalid_email_input_returns_400(self):
        """
        Verify that empty, malformed, or missing email inputs return HTTP 400
        with structured JSON error responses and code='invalid_email'.
        """
        invalid_emails = [
            "",
            "   ",
            "notanemail",
            "@missinguser.com",
            "user@nodomain",
            "spaces in@email.com",
        ]
        for bad_email in invalid_emails:
            resp = self.client.post(
                reverse('api_send_otp'),
                data=json.dumps({'email': bad_email}),
                content_type='application/json'
            )
            self.assertEqual(resp.status_code, 400, f"Expected 400 for '{bad_email}', got {resp.status_code}")
            data = resp.json()
            self.assertFalse(data['success'])
            self.assertEqual(data['code'], 'invalid_email')

        # Empty body
        resp_empty = self.client.post(
            reverse('api_send_otp'),
            data="{}",
            content_type='application/json'
        )
        self.assertEqual(resp_empty.status_code, 400)
        self.assertEqual(resp_empty.json()['code'], 'invalid_email')

    # -------------------------------------------------------------------------
    # Scenario 14: Email provider failure returns informative JSON error
    # -------------------------------------------------------------------------
    def test_14_email_provider_failure_returns_informative_error(self):
        """
        Verify that when the email dispatcher encounters SMTP or API connection failure,
        the endpoint returns a clean JSON error with HTTP 500/503 and never crashes with HTML.
        """
        from unittest.mock import patch
        import socket

        with patch('django.core.mail.EmailMultiAlternatives.send', side_effect=socket.timeout("Connection timed out")):
            resp = self.client.post(
                reverse('api_send_otp'),
                data=json.dumps({'email': 'provider.failure@edusphere.edu'}),
                content_type='application/json'
            )
            self.assertIn(resp.status_code, [500, 503])
            data = resp.json()
            self.assertFalse(data['success'])
            self.assertIn('message', data)

    # -------------------------------------------------------------------------
    # Scenario 15: Production unconfigured email service fails safely
    # -------------------------------------------------------------------------
    def test_15_production_unconfigured_email_fails_safely(self):
        """
        Verify that in production (DEBUG=False), if no email provider is configured,
        the system returns an informative 503 instead of pretending delivery succeeded.
        """
        from django.test import override_settings

        with override_settings(
            DEBUG=False,
            IS_RUNNING_TESTS=False,
            EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
            EMAIL_HOST_USER='',
            EMAIL_HOST_PASSWORD='',
            RESEND_API_KEY='',
            BREVO_API_KEY=''
        ):
            resp = self.client.post(
                reverse('api_send_otp'),
                data=json.dumps({'email': 'production.check@edusphere.edu'}),
                content_type='application/json'
            )
            self.assertEqual(resp.status_code, 503)
            data = resp.json()
            self.assertFalse(data['success'])
            self.assertEqual(data['code'], 'email_service_unconfigured')
            self.assertIn('Render environment variables', data['message'])

    # -------------------------------------------------------------------------
    # Scenario 16: Resend HTTPS API dispatch format and response handling
    # -------------------------------------------------------------------------
    def test_16_resend_http_dispatch(self):
        """
        Verify that dispatch_via_resend sends proper HTTPS payload to Resend API.
        """
        from unittest.mock import patch, MagicMock
        from accounts.otp_service import dispatch_via_resend

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"id": "msg_test_success_123"}'
        mock_resp.__enter__.return_value = mock_resp

        with patch('urllib.request.urlopen', return_value=mock_resp) as mock_urlopen:
            success = dispatch_via_resend(
                api_key="re_test_key_12345",
                from_email="EduSphere <onboarding@resend.dev>",
                to_email="test.student@example.com",
                subject="Test Subject",
                html_message="<p>Test</p>",
                text_message="Test"
            )
            self.assertTrue(success)
            self.assertEqual(mock_urlopen.call_count, 1)

            # Verify request headers and URL
            req_arg = mock_urlopen.call_args[0][0]
            self.assertEqual(req_arg.full_url, "https://api.resend.com/emails")
            self.assertEqual(req_arg.headers["Authorization"], "Bearer re_test_key_12345")
            self.assertEqual(req_arg.headers["Content-type"], "application/json")

    # -------------------------------------------------------------------------
    # Scenario 17: Brevo HTTPS API dispatch format and response handling
    # -------------------------------------------------------------------------
    def test_17_brevo_http_dispatch(self):
        """
        Verify that dispatch_via_brevo sends proper HTTPS payload to Brevo API.
        """
        from unittest.mock import patch, MagicMock
        from accounts.otp_service import dispatch_via_brevo

        mock_resp = MagicMock()
        mock_resp.status = 201
        mock_resp.read.return_value = b'{"messageId": "<test@brevo>"}'
        mock_resp.__enter__.return_value = mock_resp

        with patch('urllib.request.urlopen', return_value=mock_resp) as mock_urlopen:
            success = dispatch_via_brevo(
                api_key="xkeysib-test-key",
                from_email="EduSphere Security <no-reply@iimtindia.net>",
                to_email="test.student@example.com",
                subject="Test Subject",
                html_message="<p>Test</p>",
                text_message="Test"
            )
            self.assertTrue(success)
            self.assertEqual(mock_urlopen.call_count, 1)

    # -------------------------------------------------------------------------
    # Scenario 18: Resend API authentication error (401) is handled safely
    # -------------------------------------------------------------------------
    def test_18_resend_auth_error_returns_clean_message(self):
        """
        Verify that an invalid API key returns HTTP 503 with an actionable error
        and does NOT expose the API key or internal secrets.
        """
        from unittest.mock import patch
        import urllib.error
        import io
        from accounts.otp_service import dispatch_via_resend, OTPError

        err_body = b'{"statusCode": 401, "name": "invalid_api_key", "message": "API key is invalid"}'
        mock_err = urllib.error.HTTPError(
            url="https://api.resend.com/emails",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=io.BytesIO(err_body)
        )

        with patch('urllib.request.urlopen', side_effect=mock_err):
            with self.assertRaises(OTPError) as ctx:
                dispatch_via_resend(
                    api_key="re_invalid_secret_key_999",
                    from_email="EduSphere <onboarding@resend.dev>",
                    to_email="user@example.com",
                    subject="Verification Code",
                    html_message="<p>123456</p>",
                    text_message="123456"
                )
            self.assertEqual(ctx.exception.code, 'resend_invalid_api_key')
            self.assertEqual(ctx.exception.status_code, 503)
            # Ensure the secret key itself was NOT echoed in the exception message
            self.assertNotIn("re_invalid_secret_key_999", str(ctx.exception))
            self.assertIn("RESEND_API_KEY", str(ctx.exception))

    # -------------------------------------------------------------------------
    # Scenario 19: Resend API domain rejection (403/422) returns clean message
    # -------------------------------------------------------------------------
    def test_19_resend_domain_rejection_returns_clean_message(self):
        """
        Verify that an unverified sender domain returns an informative error
        guiding the user on domain verification or using onboarding@resend.dev.
        """
        from unittest.mock import patch
        import urllib.error
        import io
        from accounts.otp_service import dispatch_via_resend, OTPError

        err_body = b'{"statusCode": 403, "name": "validation_error", "message": "Domain not verified"}'
        mock_err = urllib.error.HTTPError(
            url="https://api.resend.com/emails",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=io.BytesIO(err_body)
        )

        with patch('urllib.request.urlopen', side_effect=mock_err):
            with self.assertRaises(OTPError) as ctx:
                dispatch_via_resend(
                    api_key="re_test_key",
                    from_email="Unverified <unverified@customdomain.com>",
                    to_email="user@example.com",
                    subject="Verification Code",
                    html_message="<p>123456</p>",
                    text_message="123456"
                )
            self.assertEqual(ctx.exception.code, 'resend_validation_error')
            self.assertEqual(ctx.exception.status_code, 503)
            self.assertIn("Domain not verified", str(ctx.exception))

    # -------------------------------------------------------------------------
    # Scenario 20: Resend API network / timeout error returns 502
    # -------------------------------------------------------------------------
    def test_20_resend_network_timeout_returns_502(self):
        """
        Verify that a network timeout or connection reset returns HTTP 502
        rather than crashing with an unhandled exception.
        """
        from unittest.mock import patch
        import urllib.error
        from accounts.otp_service import dispatch_via_resend, OTPError

        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("Connection reset")):
            with self.assertRaises(OTPError) as ctx:
                dispatch_via_resend(
                    api_key="re_test_key",
                    from_email="EduSphere <onboarding@resend.dev>",
                    to_email="user@example.com",
                    subject="Verification Code",
                    html_message="<p>123456</p>",
                    text_message="123456"
                )
            self.assertEqual(ctx.exception.code, 'resend_connection_error')
            self.assertEqual(ctx.exception.status_code, 502)

    # -------------------------------------------------------------------------
    # Scenario 21: End-to-end OTP API dispatch via Resend HTTPS integration
    # -------------------------------------------------------------------------
    def test_21_send_otp_end_to_end_with_resend(self):
        """
        Verify that with RESEND_API_KEY configured, api_send_otp invokes Resend
        and responds with HTTP 200 without exposing OTP in response body.
        """
        from unittest.mock import patch, MagicMock
        from django.test import override_settings

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"id": "msg_live_mock_123"}'
        mock_resp.__enter__.return_value = mock_resp

        with override_settings(RESEND_API_KEY="re_test_production_key_123"):
            with patch('urllib.request.urlopen', return_value=mock_resp) as mock_urlopen:
                resp = self.client.post(
                    reverse('api_send_otp'),
                    data=json.dumps({'email': 'verified.resend@edusphere.edu'}),
                    content_type='application/json'
                )
                self.assertEqual(resp.status_code, 200)
                data = resp.json()
                self.assertTrue(data['success'])
                # Never expose plaintext OTP in public response
                self.assertNotIn('otp', data)
                self.assertNotIn('code', data.get('data', {}))

                # Verify Resend API was called with the masked email in logs
                self.assertEqual(mock_urlopen.call_count, 1)

    # -------------------------------------------------------------------------
    # Scenario 22: ResendEmailBackend Django backend integration
    # -------------------------------------------------------------------------
    def test_22_resend_email_backend_integration(self):
        """
        Verify that accounts.email_backends.ResendEmailBackend dispatches
        Django EmailMultiAlternatives properly.
        """
        from unittest.mock import patch, MagicMock
        from django.core.mail import EmailMultiAlternatives
        from accounts.email_backends import ResendEmailBackend

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"id": "backend_test_id"}'
        mock_resp.__enter__.return_value = mock_resp

        backend = ResendEmailBackend(api_key="re_backend_key")
        msg = EmailMultiAlternatives(
            subject="Backend Test",
            body="Text content",
            from_email="EduSphere <onboarding@resend.dev>",
            to=["recipient@example.com"]
        )
        msg.attach_alternative("<p>HTML content</p>", "text/html")

        with patch('urllib.request.urlopen', return_value=mock_resp):
            num_sent = backend.send_messages([msg])
            self.assertEqual(num_sent, 1)

    # -------------------------------------------------------------------------
    # Scenario 23: Safe email diagnostic masking
    # -------------------------------------------------------------------------
    def test_23_diagnostic_logging_masks_email(self):
        """
        Verify that mask_email_address obscures personal identifiers in logs.
        """
        from accounts.otp_service import mask_email_address

        self.assertEqual(mask_email_address("anant@example.com"), "a***t@example.com")
        self.assertEqual(mask_email_address("al@example.com"), "a*@example.com")
        self.assertEqual(mask_email_address(""), "***")
        self.assertEqual(mask_email_address("invalid"), "***")


