import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User, StudentProfile, TeacherProfile, AdminProfile
from academics.models import Department, AcademicYear, Course, CourseEnrollment
from assignments.models import Assignment, Submission
from attendance.models import AttendanceSession, AttendanceRecord
from materials.models import StudyMaterial
from announcements.models import Announcement, Notification
from activity_logs.models import ActivityLog


class Command(BaseCommand):
    help = 'Seeds initial realistic data for IIMT UNIVERSITY (Admins, Faculty, Students, Courses, Assignments, Attendance)'

    def handle(self, *args, **options):
        self.stdout.write("Starting IIMT UNIVERSITY data seeding...")

        # 1. Academic Year
        year, _ = AcademicYear.objects.get_or_create(
            name='2026-2027',
            defaults={
                'start_date': datetime.date(2026, 8, 1),
                'end_date': datetime.date(2027, 5, 31),
                'is_current': True
            }
        )

        # 2. Administrator
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Sarah',
                'last_name': 'Jenkins',
                'email': 'admin@iimtindia.net',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'phone': '+1 (555) 019-2834',
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            AdminProfile.objects.get_or_create(user=admin_user, staff_id='ADM-001', designation='Chief Academic Dean')
            self.stdout.write(self.style.SUCCESS("Created Admin: admin / admin123"))

        # 3. Faculty / Teachers
        faculty_data = [
            {
                'username': 'prof.alan',
                'first_name': 'Alan',
                'last_name': 'Turing',
                'email': 'alan.turing@iimtindia.net',
                'emp_id': 'EMP-101',
                'designation': 'Professor & Dept Head',
                'qualifications': 'Ph.D. in Computer Science (Cambridge)',
                'dept_name': 'Computer Science',
                'dept_code': 'CS'
            },
            {
                'username': 'prof.ada',
                'first_name': 'Ada',
                'last_name': 'Lovelace',
                'email': 'ada.lovelace@iimtindia.net',
                'emp_id': 'EMP-102',
                'designation': 'Associate Professor',
                'qualifications': 'Ph.D. in Applied Mathematics',
                'dept_name': 'Mathematics',
                'dept_code': 'MATH'
            },
            {
                'username': 'prof.clarke',
                'first_name': 'Arthur',
                'last_name': 'Clarke',
                'email': 'arthur.clarke@iimtindia.net',
                'emp_id': 'EMP-103',
                'designation': 'Assistant Professor',
                'qualifications': 'Ph.D. in Physics & Electronics',
                'dept_name': 'Electrical Engineering',
                'dept_code': 'EE'
            },
        ]

        departments_map = {}
        teachers_map = {}

        for f in faculty_data:
            dept, _ = Department.objects.get_or_create(
                code=f['dept_code'],
                defaults={'name': f['dept_name'], 'description': f"Department of {f['dept_name']}"}
            )
            departments_map[f['dept_code']] = dept

            u, created = User.objects.get_or_create(
                username=f['username'],
                defaults={
                    'first_name': f['first_name'],
                    'last_name': f['last_name'],
                    'email': f['email'],
                    'role': User.Role.TEACHER,
                    'phone': '+1 (555) 482-1940',
                }
            )
            if created:
                u.set_password('teacher123')
                u.save()

            t_profile, _ = TeacherProfile.objects.get_or_create(
                user=u,
                defaults={
                    'employee_id': f['emp_id'],
                    'department': dept,
                    'designation': f['designation'],
                    'qualifications': f['qualifications'],
                    'joining_date': datetime.date(2022, 1, 15)
                }
            )
            teachers_map[f['dept_code']] = t_profile
            dept.head_of_department = t_profile
            dept.save()

        # 4. Students
        students_data = [
            {'username': 'student.alice', 'first_name': 'Alice', 'last_name': 'Smith', 'roll': 'CS2026-001', 'dept': 'CS', 'sem': 3},
            {'username': 'student.bob', 'first_name': 'Bob', 'last_name': 'Jones', 'roll': 'CS2026-002', 'dept': 'CS', 'sem': 3},
            {'username': 'student.charlie', 'first_name': 'Charlie', 'last_name': 'Davis', 'roll': 'CS2026-003', 'dept': 'CS', 'sem': 3},
            {'username': 'student.diana', 'first_name': 'Diana', 'last_name': 'Prince', 'roll': 'EE2026-001', 'dept': 'EE', 'sem': 3},
            {'username': 'student.edward', 'first_name': 'Edward', 'last_name': 'Norton', 'roll': 'EE2026-002', 'dept': 'EE', 'sem': 3},
            {'username': 'student.fiona', 'first_name': 'Fiona', 'last_name': 'Gallagher', 'roll': 'MA2026-001', 'dept': 'MATH', 'sem': 3},
        ]

        students_map = {}
        for s in students_data:
            u, created = User.objects.get_or_create(
                username=s['username'],
                defaults={
                    'first_name': s['first_name'],
                    'last_name': s['last_name'],
                    'email': f"{s['username']}@iimtindia.net",
                    'role': User.Role.STUDENT,
                    'phone': '+1 (555) 302-8821',
                }
            )
            if created:
                u.set_password('student123')
                u.save()

            sp, _ = StudentProfile.objects.get_or_create(
                user=u,
                defaults={
                    'roll_number': s['roll'],
                    'admission_number': f"ADM-{s['roll']}",
                    'department': departments_map[s['dept']],
                    'academic_year': year,
                    'current_semester': s['sem'],
                    'guardian_name': f"Parent of {s['first_name']}",
                    'guardian_phone': '+1 (555) 901-2211',
                    'parent_email': f"parent.{s['first_name'].lower()}@example.com",
                    'is_minor': (s['roll'] == 'CS2026-003'),  # Charlie is minor
                    'parental_consent_verified': True,
                    'parental_consent_date': timezone.now()
                }
            )
            students_map[s['username']] = sp

        # 5. Courses
        courses_data = [
            {
                'code': 'CS201',
                'name': 'Data Structures & Algorithms',
                'dept': 'CS',
                'teacher': teachers_map['CS'],
                'credits': 4,
                'desc': 'Core algorithmic techniques, trees, balanced graphs, asymptotic bounds, and computational efficiency.'
            },
            {
                'code': 'CS301',
                'name': 'Relational Database Systems',
                'dept': 'CS',
                'teacher': teachers_map['CS'],
                'credits': 3,
                'desc': 'Relational model, PostgreSQL, ACID transactions, normalization, and indexing.'
            },
            {
                'code': 'MATH101',
                'name': 'Linear Algebra & Matrix Calculus',
                'dept': 'MATH',
                'teacher': teachers_map['MATH'],
                'credits': 4,
                'desc': 'Vector spaces, eigenvalues, matrix decompositions, and continuous optimization.'
            },
            {
                'code': 'PHY102',
                'name': 'Modern Physics & Electromagnetism',
                'dept': 'EE',
                'teacher': teachers_map['EE'],
                'credits': 3,
                'desc': 'Maxwell equations, quantum foundations, electromagnetic wave transmission.'
            },
        ]

        courses_map = {}
        for c in courses_data:
            course, _ = Course.objects.get_or_create(
                code=c['code'],
                defaults={
                    'name': c['name'],
                    'department': departments_map[c['dept']],
                    'teacher': c['teacher'],
                    'academic_year': year,
                    'semester': 3,
                    'credits': c['credits'],
                    'description': c['desc'],
                    'is_active': True
                }
            )
            courses_map[c['code']] = course

        # 6. Course Enrollments
        # CS students enroll in CS201, CS301, MATH101
        for user_key in ['student.alice', 'student.bob', 'student.charlie']:
            sp = students_map[user_key]
            for c_code in ['CS201', 'CS301', 'MATH101']:
                CourseEnrollment.objects.get_or_create(course=courses_map[c_code], student=sp)

        # EE students enroll in PHY102, MATH101
        for user_key in ['student.diana', 'student.edward']:
            sp = students_map[user_key]
            for c_code in ['PHY102', 'MATH101']:
                CourseEnrollment.objects.get_or_create(course=courses_map[c_code], student=sp)

        # Fiona enrolls in MATH101 and CS201
        for c_code in ['MATH101', 'CS201']:
            CourseEnrollment.objects.get_or_create(course=courses_map[c_code], student=students_map['student.fiona'])

        # 7. Assignments
        now = timezone.now()
        due_future = now + datetime.timedelta(days=7)
        due_past = now - datetime.timedelta(days=3)

        a1, _ = Assignment.objects.get_or_create(
            course=courses_map['CS201'],
            title='Assignment 1: Balanced Binary Search Trees & AVL Rotations',
            defaults={
                'teacher': teachers_map['CS'],
                'description': 'Implement an AVL Tree class with insert, delete, and balancing rotations. Include time complexity analysis.',
                'max_marks': 100,
                'due_date': due_past,
                'status': Assignment.Status.PUBLISHED
            }
        )

        a2, _ = Assignment.objects.get_or_create(
            course=courses_map['CS201'],
            title='Assignment 2: Graph Shortest Path (Dijkstra vs A*)',
            defaults={
                'teacher': teachers_map['CS'],
                'description': 'Compare Dijkstra and A* heuristics on road network datasets. Provide benchmark charts and test suite.',
                'max_marks': 100,
                'due_date': due_future,
                'status': Assignment.Status.PUBLISHED
            }
        )

        a3, _ = Assignment.objects.get_or_create(
            course=courses_map['CS301'],
            title='Project 1: PostgreSQL Relational Schema Design & 3NF',
            defaults={
                'teacher': teachers_map['CS'],
                'description': 'Design a normalized 3NF schema for an e-commerce platform with integrity constraints and indexing strategy.',
                'max_marks': 100,
                'due_date': due_future,
                'status': Assignment.Status.PUBLISHED
            }
        )

        a4, _ = Assignment.objects.get_or_create(
            course=courses_map['MATH101'],
            title='Problem Set 1: Vector Subspaces & Eigenvalue Proofs',
            defaults={
                'teacher': teachers_map['MATH'],
                'description': 'Complete mathematical proofs for Gram-Schmidt orthogonalization and symmetric matrix diagonalization.',
                'max_marks': 50,
                'due_date': due_past,
                'status': Assignment.Status.PUBLISHED
            }
        )

        # 8. Submissions & Grading
        # Alice on a1
        s_alice_a1, _ = Submission.objects.get_or_create(
            assignment=a1,
            student=students_map['student.alice'],
            defaults={
                'submission_text': 'Completed AVL Tree with double-rotation balancing tests and O(log N) verification.',
                'marks_obtained': 96.0,
                'feedback': 'Exemplary implementation! Code style, edge test cases, and time complexity proof are spot on.',
                'status': Submission.Status.GRADED,
                'graded_at': now - datetime.timedelta(days=1),
                'graded_by': teachers_map['CS']
            }
        )

        # Bob on a1
        s_bob_a1, _ = Submission.objects.get_or_create(
            assignment=a1,
            student=students_map['student.bob'],
            defaults={
                'submission_text': 'AVL Tree implementation with unit tests.',
                'marks_obtained': 85.0,
                'feedback': 'Good overall work. Minor edge case with delete rebalancing needed clarification.',
                'status': Submission.Status.GRADED,
                'graded_at': now - datetime.timedelta(days=1),
                'graded_by': teachers_map['CS']
            }
        )

        # Charlie on a1 (Pending grading)
        Submission.objects.get_or_create(
            assignment=a1,
            student=students_map['student.charlie'],
            defaults={
                'submission_text': 'Here is my complete AVL tree code and documentation report.',
                'status': Submission.Status.SUBMITTED
            }
        )

        # Alice on a3 (Submitted early)
        Submission.objects.get_or_create(
            assignment=a3,
            student=students_map['student.alice'],
            defaults={
                'submission_text': 'Attached PostgreSQL schema SQL script and entity-relationship diagrams.',
                'status': Submission.Status.SUBMITTED
            }
        )

        # Diana on a4 (Graded)
        Submission.objects.get_or_create(
            assignment=a4,
            student=students_map['student.diana'],
            defaults={
                'submission_text': 'Proof sheet for problems 1 to 6.',
                'marks_obtained': 48.0,
                'feedback': 'Brilliant mathematical precision and clear notation.',
                'status': Submission.Status.GRADED,
                'graded_at': now - datetime.timedelta(days=1),
                'graded_by': teachers_map['MATH']
            }
        )

        # 9. Attendance Sessions & Records
        dates = [
            datetime.date(2026, 10, 6),
            datetime.date(2026, 10, 8),
            datetime.date(2026, 10, 10),
            datetime.date(2026, 10, 12),
        ]

        # CS201 attendance sessions
        cs201 = courses_map['CS201']
        cs_students = [students_map['student.alice'], students_map['student.bob'], students_map['student.charlie'], students_map['student.fiona']]

        for i, dt in enumerate(dates):
            sess, _ = AttendanceSession.objects.get_or_create(
                course=cs201,
                date=dt,
                defaults={'taken_by': teachers_map['CS'], 'topic_covered': f'Lecture {i+1}: Advanced Data Structures'}
            )
            for j, st in enumerate(cs_students):
                # Bob was absent on day 2, charlie was late on day 3
                st_status = AttendanceRecord.Status.PRESENT
                if j == 1 and i == 1:
                    st_status = AttendanceRecord.Status.ABSENT
                elif j == 2 and i == 2:
                    st_status = AttendanceRecord.Status.LATE

                AttendanceRecord.objects.get_or_create(
                    session=sess,
                    student=st,
                    defaults={'status': st_status}
                )

        # 10. Study Materials
        StudyMaterial.objects.get_or_create(
            course=courses_map['CS201'],
            title='Lecture 01 - Asymptotic Analysis & Recurrence Relations',
            defaults={
                'unit_module': 'Module 1: Foundations',
                'description': 'Master Theorem, Big-O, Big-Omega proofs and recursion trees.',
                'uploaded_by': teachers_map['CS'],
                'external_link': 'https://en.wikipedia.org/wiki/Master_theorem_(analysis_of_algorithms)'
            }
        )
        StudyMaterial.objects.get_or_create(
            course=courses_map['CS201'],
            title='Lecture 03 - AVL Trees & Rotation Rules Reference Card',
            defaults={
                'unit_module': 'Module 2: Balanced Trees',
                'description': 'Single and double rotation diagrams with invariant definitions.',
                'uploaded_by': teachers_map['CS']
            }
        )
        StudyMaterial.objects.get_or_create(
            course=courses_map['CS301'],
            title='PostgreSQL Relational Normalization & Indexing Best Practices',
            defaults={
                'unit_module': 'Unit 3: Schema Normalization',
                'description': '1NF through BCNF guide with functional dependency diagrams.',
                'uploaded_by': teachers_map['CS']
            }
        )

        # 11. Announcements
        Announcement.objects.get_or_create(
            title='Mid-Semester Examination Schedule for Fall 2026',
            defaults={
                'content': 'The mid-semester examination timetable has been finalized. Exams commence next Monday. Students are advised to verify seat allocations and hall tickets in their respective dashboards.',
                'author': admin_user,
                'target_audience': Announcement.Audience.ALL,
                'priority': Announcement.Priority.URGENT,
            }
        )
        Announcement.objects.get_or_create(
            title='Annual Institution Hackathon & Tech Innovation Summit',
            defaults={
                'content': 'Teams of 3 to 4 students from Computer Science and Electrical Engineering are invited to pitch innovative solutions. Cash prizes and industry mentoring opportunities will be awarded.',
                'author': admin_user,
                'target_audience': Announcement.Audience.STUDENTS,
                'priority': Announcement.Priority.IMPORTANT,
            }
        )
        Announcement.objects.get_or_create(
            title='Faculty Curriculum Review & Board of Studies Meeting',
            defaults={
                'content': 'All department heads and faculty members are requested to join the quarterly syllabus review session this Friday at 3:00 PM in Conference Room A.',
                'author': admin_user,
                'target_audience': Announcement.Audience.TEACHERS,
                'priority': Announcement.Priority.NORMAL,
            }
        )

        # 12. Notifications for student.alice
        Notification.objects.get_or_create(
            recipient=students_map['student.alice'].user,
            title='Grade Posted: Assignment 1 (CS201)',
            defaults={
                'message': 'Your submission for Balanced Binary Search Trees has been graded: 96/100.',
                'link': f'/assignments/{a1.id}/',
                'notification_type': Notification.Type.GRADE,
                'is_read': False
            }
        )
        Notification.objects.get_or_create(
            recipient=students_map['student.alice'].user,
            title='New Assignment: Graph Shortest Path',
            defaults={
                'message': 'Assignment 2 for CS201 is now live and due in 7 days.',
                'link': f'/assignments/{a2.id}/',
                'notification_type': Notification.Type.ASSIGNMENT,
                'is_read': False
            }
        )

        # 13. Activity Logs
        ActivityLog.objects.create(
            user=admin_user,
            action="System initialized with departmental structure and initial course catalog",
            category=ActivityLog.Category.ADMIN,
            ip_address="127.0.0.1",
            details="Initial institutional setup performed successfully."
        )

        self.stdout.write(self.style.SUCCESS("IIMT UNIVERSITY sample database successfully seeded!"))
        self.stdout.write("""
=== Available User Credentials ===
1. Admin:
   Username: admin
   Password: admin123

2. Teachers:
   - prof.alan / teacher123 (CS HOD, Teaches CS201 & CS301)
   - prof.ada / teacher123 (Math, Teaches MATH101)
   - prof.clarke / teacher123 (Physics, Teaches PHY102)

3. Students:
   - student.alice / student123 (Roll: CS2026-001)
   - student.bob / student123 (Roll: CS2026-002)
   - student.charlie / student123 (Roll: CS2026-003)
   - student.diana / student123 (Roll: EE2026-001)
   - student.edward / student123 (Roll: EE2026-002)
   - student.fiona / student123 (Roll: MA2026-001)
==================================
""")
