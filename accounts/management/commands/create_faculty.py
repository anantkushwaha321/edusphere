from django.core.management.base import BaseCommand
from django.utils.text import slugify
from accounts.models import User, TeacherProfile
from academics.models import Department


class Command(BaseCommand):
    help = 'Creates a new Faculty / Teacher account with a registered email.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Faculty institutional email address.')
        parser.add_argument('--first-name', type=str, default='Faculty', help='First name.')
        parser.add_argument('--last-name', type=str, default='Member', help='Last name.')
        parser.add_argument('--designation', type=str, default='Assistant Professor', help='Academic designation.')
        parser.add_argument('--employee-id', type=str, default='', help='Unique Employee ID.')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        first_name = options['first_name'].strip()
        last_name = options['last_name'].strip()
        designation = options['designation'].strip()

        existing = User.objects.filter(email__iexact=email).first()
        if existing:
            self.stdout.write(self.style.WARNING(f"User with email '{email}' already exists. Updating to Faculty..."))
            existing.role = User.Role.TEACHER
            existing.first_name = first_name
            existing.last_name = last_name
            existing.save()

            dept = Department.objects.first()
            tp, _ = TeacherProfile.objects.get_or_create(
                user=existing,
                defaults={
                    'employee_id': options['employee_id'] or f"EMP-{existing.id:04d}",
                    'department': dept,
                    'designation': designation
                }
            )
            self.stdout.write(self.style.SUCCESS(f"User '{email}' updated to Faculty!"))
            return

        base_username = slugify(email.split('@')[0]) or 'faculty'
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=User.Role.TEACHER,
            is_active=True
        )
        user.set_unusable_password()
        user.save()

        dept = Department.objects.first()
        emp_id = options['employee_id'] or f"EMP-{user.id:04d}"
        TeacherProfile.objects.create(
            user=user,
            employee_id=emp_id,
            department=dept,
            designation=designation
        )

        self.stdout.write(self.style.SUCCESS(
            f"\n[CREATED] New Faculty account created:\n"
            f"  Name:        {first_name} {last_name}\n"
            f"  Email:       {email}\n"
            f"  Role:        Faculty / Teacher\n"
            f"  Employee ID: {emp_id}\n\n"
            f"They can now sign in at /login/ using their email: {email}!"
        ))
