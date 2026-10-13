from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import User, StudentProfile, TeacherProfile, AdminProfile
from academics.models import Department, AcademicYear


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Enter your username or email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500',
            'placeholder': 'Enter your password'
        })
    )


class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar', 'bio', 'address', 'gender', 'date_of_birth']
        help_texts = {
            'phone': 'Optional: Used only for urgent campus SMS emergency alerts.',
            'avatar': 'Optional: Used only for institutional identification badge.',
            'bio': 'Optional: Academic interests and research summary.',
            'address': 'Optional: Mailing address for official transcripts.',
            'date_of_birth': 'Optional: Used for verifying age and minor parental protections.',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'bio': forms.Textarea(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'rows': 3}),
            'address': forms.Textarea(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'rows': 2}),
            'gender': forms.Select(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'avatar': forms.FileInput(attrs={'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none'})


class UserCreationAdminForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
        help_text='At least 6 characters.'
    )
    # Student specific
    roll_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}))
    admission_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}))
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False, widget=forms.Select(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}))
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.all(), required=False, widget=forms.Select(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}))
    current_semester = forms.IntegerField(required=False, initial=1, widget=forms.NumberInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}))
    guardian_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}))
    guardian_phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}))
    parent_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}), help_text='Required for minors under 18')
    is_minor = forms.BooleanField(required=False, initial=False, widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 rounded border-slate-300'}), help_text='Check if student is under 18')

    # Teacher specific
    employee_id = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}))
    designation = forms.CharField(required=False, initial='Assistant Professor', widget=forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}))
    qualifications = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}),
            'role': forms.Select(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300', 'id': 'roleSelect'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            role = self.cleaned_data['role']
            if role == User.Role.STUDENT:
                StudentProfile.objects.create(
                    user=user,
                    roll_number=self.cleaned_data.get('roll_number') or f"STU-{user.id:04d}",
                    admission_number=self.cleaned_data.get('admission_number') or f"ADM-{user.id:04d}",
                    department=self.cleaned_data.get('department'),
                    academic_year=self.cleaned_data.get('academic_year'),
                    current_semester=self.cleaned_data.get('current_semester') or 1,
                    guardian_name=self.cleaned_data.get('guardian_name'),
                    guardian_phone=self.cleaned_data.get('guardian_phone'),
                    parent_email=self.cleaned_data.get('parent_email'),
                    is_minor=self.cleaned_data.get('is_minor', False),
                )
            elif role == User.Role.TEACHER:
                TeacherProfile.objects.create(
                    user=user,
                    employee_id=self.cleaned_data.get('employee_id') or f"EMP-{user.id:04d}",
                    department=self.cleaned_data.get('department'),
                    designation=self.cleaned_data.get('designation') or 'Faculty Member',
                    qualifications=self.cleaned_data.get('qualifications')
                )
            elif role == User.Role.ADMIN:
                AdminProfile.objects.create(
                    user=user,
                    staff_id=f"ADM-{user.id:04d}",
                    designation='Academic Administrator'
                )
        return user
