import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import datetime

from accounts.models import User, StudentProfile
from academics.models import Department, AcademicYear, Course, CourseEnrollment
from compliance.models import DataSubjectRequest, EmailPreference, CookieConsentLog, ParentalConsentRecord


class ComplianceAndPrivacyTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Academic Year & Dept
        self.year = AcademicYear.objects.create(name='2026-2027', start_date=datetime.date(2026, 8, 1), end_date=datetime.date(2027, 5, 31), is_current=True)
        self.dept = Department.objects.create(name='Computer Science', code='CS')

        # Student User
        self.student_user = User.objects.create_user(
            username='student_compliance',
            email='student_compliance@test.com',
            password='password123',
            role=User.Role.STUDENT
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            roll_number='CS2026-TEST',
            department=self.dept,
            academic_year=self.year,
            current_semester=3,
            is_minor=True
        )

    def test_legal_policy_pages_render(self):
        """Verify all mandatory policy pages return 200 OK."""
        pages = [
            'compliance:privacy_policy',
            'compliance:terms_of_service',
            'compliance:cookie_policy',
            'compliance:refund_policy',
            'compliance:accessibility_statement',
        ]
        for page in pages:
            response = self.client.get(reverse(page))
            self.assertEqual(response.status_code, 200, f"Page {page} failed to render")

    def test_cookie_consent_api(self):
        """Verify cookie consent endpoint logs preferences."""
        payload = {'essential': True, 'functional': True, 'analytics': False}
        response = self.client.post(
            reverse('compliance:cookie_consent_api'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CookieConsentLog.objects.filter(functional_accepted=True, analytics_accepted=False).exists())

    def test_data_subject_request_submission(self):
        """User submits GDPR Article 17 Erasure request."""
        self.client.login(username='student_compliance', password='password123')
        post_data = {
            'request_type': DataSubjectRequest.RequestType.ERASURE,
            'reason': 'Withdrawing from institution, request personal profile erasure.'
        }
        response = self.client.post(reverse('compliance:data_portal'), post_data)
        self.assertEqual(response.status_code, 302)

        dsar = DataSubjectRequest.objects.filter(user=self.student_user).first()
        self.assertIsNotNone(dsar)
        self.assertEqual(dsar.request_type, DataSubjectRequest.RequestType.ERASURE)
        self.assertEqual(dsar.status, DataSubjectRequest.Status.PENDING)

    def test_instant_data_export_portability(self):
        """User downloads instant JSON data archive under GDPR Art. 20."""
        self.client.login(username='student_compliance', password='password123')
        response = self.client.get(reverse('compliance:export_data'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        data = json.loads(response.content)
        self.assertEqual(data['export_metadata']['username'], 'student_compliance')
        self.assertEqual(data['student_profile']['roll_number'], 'CS2026-TEST')

    def test_unsubscribe_token_and_email_preferences(self):
        """User can unsubscribe without login via unique UUID token (RFC 8058)."""
        pref, _ = EmailPreference.objects.get_or_create(user=self.student_user)
        token_url = reverse('compliance:unsubscribe_token', kwargs={'token': pref.unsubscribe_token})

        # GET confirmation page
        response = self.client.get(token_url)
        self.assertEqual(response.status_code, 200)

        # POST to unsubscribe
        response = self.client.post(token_url, {'academic_announcements': 'on'})
        self.assertEqual(response.status_code, 200)

        pref.refresh_from_db()
        self.assertTrue(pref.academic_announcements)
        self.assertFalse(pref.assignment_alerts)
        self.assertFalse(pref.marketing_and_surveys)

    def test_parental_consent_portal(self):
        """Guardian can verify parental consent for a minor student under COPPA."""
        post_data = {
            'student_roll': 'CS2026-TEST',
            'guardian_name': 'Jane Doe',
            'guardian_email': 'jane.doe@example.com',
            'guardian_phone': '+1 (555) 302-9900',
            'consent_given': 'on',
        }
        response = self.client.post(reverse('compliance:parental_consent'), post_data)
        self.assertEqual(response.status_code, 302)

        self.student_profile.refresh_from_db()
        self.assertTrue(self.student_profile.parental_consent_verified)
        self.assertEqual(self.student_profile.guardian_name, 'Jane Doe')
