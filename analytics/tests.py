from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import datetime

from accounts.models import User, StudentProfile, TeacherProfile, AdminProfile
from academics.models import Department, AcademicYear, Course, CourseEnrollment
from assignments.models import Assignment, Submission
from attendance.models import AttendanceSession, AttendanceRecord


class EduSphereTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Academic Year
        self.year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2027, 5, 31),
            is_current=True
        )

        # Department
        self.dept = Department.objects.create(name='Computer Science', code='CS')

        # Admin
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='password123',
            role=User.Role.ADMIN
        )
        AdminProfile.objects.create(user=self.admin_user, staff_id='ADM-TEST')

        # Teacher
        self.teacher_user = User.objects.create_user(
            username='teacher_test',
            email='teacher@test.com',
            password='password123',
            role=User.Role.TEACHER
        )
        self.teacher_profile = TeacherProfile.objects.create(
            user=self.teacher_user,
            employee_id='EMP-TEST',
            department=self.dept
        )

        # Student
        self.student_user = User.objects.create_user(
            username='student_test',
            email='student@test.com',
            password='password123',
            role=User.Role.STUDENT
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            roll_number='STU-TEST',
            department=self.dept,
            academic_year=self.year,
            current_semester=3
        )

        # Course
        self.course = Course.objects.create(
            code='CS101',
            name='Introduction to Programming',
            department=self.dept,
            teacher=self.teacher_profile,
            academic_year=self.year,
            semester=1,
            credits=3
        )
        CourseEnrollment.objects.create(course=self.course, student=self.student_profile)

        # Assignment
        self.assignment = Assignment.objects.create(
            course=self.course,
            teacher=self.teacher_profile,
            title='Test Assignment',
            description='Test description',
            max_marks=100,
            due_date=timezone.now() + datetime.timedelta(days=7),
            status=Assignment.Status.PUBLISHED
        )

    def test_login_and_role_redirect(self):
        """Test login routes to appropriate role dashboard."""
        # Student login
        login_success = self.client.login(username='student_test', password='password123')
        self.assertTrue(login_success)
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('student_dashboard'))
        self.client.logout()

        # Teacher login
        self.client.login(username='teacher_test', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('teacher_dashboard'))
        self.client.logout()

        # Admin login
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('admin_dashboard'))

    def test_role_access_control(self):
        """Student cannot access admin-only or teacher-only views."""
        self.client.login(username='student_test', password='password123')
        # Student tries to open user management
        response = self.client.get(reverse('user_list'))
        self.assertRedirects(response, reverse('dashboard'), target_status_code=302)

        # Student tries to access take attendance
        response = self.client.get(reverse('take_attendance'))
        self.assertRedirects(response, reverse('dashboard'), target_status_code=302)

    def test_assignment_submission_and_grading(self):
        """Student can submit assignment, and teacher can grade it."""
        self.client.login(username='student_test', password='password123')

        # Student submits work
        submit_url = reverse('submission_submit', kwargs={'assignment_pk': self.assignment.id})
        response = self.client.post(submit_url, {'submission_text': 'Here is my solution code.'})
        self.assertEqual(response.status_code, 302)

        submission = Submission.objects.get(assignment=self.assignment, student=self.student_profile)
        self.assertEqual(submission.status, Submission.Status.SUBMITTED)
        self.client.logout()

        # Teacher grades submission
        self.client.login(username='teacher_test', password='password123')
        grade_url = reverse('submission_grade', kwargs={'submission_pk': submission.id})
        response = self.client.post(grade_url, {
            'marks_obtained': 92.0,
            'feedback': 'Great logic and structure!',
            'status': Submission.Status.GRADED
        })
        self.assertEqual(response.status_code, 302)

        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.Status.GRADED)
        self.assertEqual(submission.letter_grade, 'A+')
        self.assertEqual(submission.percentage, 92.0)

    def test_attendance_and_compliance(self):
        """Teacher records attendance session, and student compliance updates."""
        self.client.login(username='teacher_test', password='password123')
        post_data = {
            'course': self.course.id,
            'date': timezone.now().date().isoformat(),
            'topic_covered': 'Introductory Concepts',
            f'status_{self.student_profile.id}': AttendanceRecord.Status.PRESENT,
            f'remarks_{self.student_profile.id}': 'Attentive',
        }
        response = self.client.post(reverse('take_attendance'), post_data)
        self.assertEqual(response.status_code, 302)

        # Check records
        session = AttendanceSession.objects.filter(course=self.course).first()
        self.assertIsNotNone(session)
        record = AttendanceRecord.objects.get(session=session, student=self.student_profile)
        self.assertEqual(record.status, AttendanceRecord.Status.PRESENT)

        # Student checks attendance
        self.client.logout()
        self.client.login(username='student_test', password='password123')
        response = self.client.get(reverse('attendance_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '100.0%')
