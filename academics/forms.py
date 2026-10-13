from django import forms
from .models import Department, AcademicYear, Course, CourseEnrollment
from accounts.models import TeacherProfile, StudentProfile


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'head_of_department']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'code': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'rows': 3}),
            'head_of_department': forms.Select(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
        }


class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['name', 'start_date', 'end_date', 'is_current']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'placeholder': 'e.g. 2026-2027'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-slate-300 rounded'}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['code', 'name', 'department', 'teacher', 'academic_year', 'semester', 'credits', 'description', 'syllabus_file', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'department': forms.Select(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'teacher': forms.Select(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'academic_year': forms.Select(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'semester': forms.NumberInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'credits': forms.NumberInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'rows': 3}),
            'syllabus_file': forms.FileInput(attrs={'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-slate-300 rounded'}),
        }


class CourseEnrollmentForm(forms.ModelForm):
    class Meta:
        model = CourseEnrollment
        fields = ['student']
        widgets = {
            'student': forms.Select(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
        }
