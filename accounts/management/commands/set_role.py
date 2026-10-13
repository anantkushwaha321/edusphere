from django.core.management.base import BaseCommand
from accounts.models import User, StudentProfile, TeacherProfile, AdminProfile
from academics.models import Department, AcademicYear


class Command(BaseCommand):
    help = 'Sets or switches a user account role between student, teacher (faculty), and admin.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address of the user.')
        parser.add_argument('role', type=str, choices=['student', 'teacher', 'admin'], help='Target role.')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        role_choice = options['role'].strip().lower()

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            self.stdout.write(self.style.ERROR(f"No user found with email: {email}"))
            return

        dept = Department.objects.first()
        active_year = AcademicYear.objects.filter(is_current=True).first()

        if role_choice == 'teacher':
            user.role = User.Role.TEACHER
            user.save()
            tp, created = TeacherProfile.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': f"EMP-{user.id:04d}",
                    'department': dept,
                    'designation': 'Assistant Professor'
                }
            )
            self.stdout.write(self.style.SUCCESS(
                f"\n[UPDATED] User '{user.email}' is now a FACULTY MEMBER (TEACHER).\n"
                f"When logging in, they will automatically be routed to the Teacher Dashboard: /dashboard/teacher/"
            ))

        elif role_choice == 'admin':
            user.role = User.Role.ADMIN
            user.is_staff = True
            user.is_superuser = True
            user.save()
            ap, created = AdminProfile.objects.get_or_create(
                user=user,
                defaults={
                    'staff_id': f"ADM-{user.id:04d}",
                    'designation': 'Academic Administrator'
                }
            )
            self.stdout.write(self.style.SUCCESS(
                f"\n[UPDATED] User '{user.email}' is now an ADMINISTRATOR.\n"
                f"When logging in, they will automatically be routed to the Admin Dashboard: /dashboard/admin/"
            ))

        elif role_choice == 'student':
            user.role = User.Role.STUDENT
            user.save()
            sp, created = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    'roll_number': f"STU-{user.id:04d}",
                    'admission_number': f"ADM-{user.id:04d}",
                    'department': dept,
                    'academic_year': active_year,
                    'current_semester': 1
                }
            )
            self.stdout.write(self.style.SUCCESS(
                f"\n[UPDATED] User '{user.email}' is now a STUDENT.\n"
                f"When logging in, they will automatically be routed to the Student Dashboard: /dashboard/student/"
            ))
