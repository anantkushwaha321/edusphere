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
            'first_name': forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
            'last_name': forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
            'email': forms.EmailInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
            'phone': forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
            'bio': forms.Textarea(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none', 'rows': 3}),
            'address': forms.Textarea(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none', 'rows': 2}),
            'gender': forms.Select(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
            'avatar': forms.FileInput(attrs={'class': 'block w-full text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer'}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'})


class UserCreationAdminForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
        help_text='At least 6 characters.'
    )
    # Student specific
    roll_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}))
    admission_number = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}))
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False, widget=forms.Select(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}))
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.all(), required=False, widget=forms.Select(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}))
    current_semester = forms.IntegerField(required=False, initial=1, widget=forms.NumberInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}))
    guardian_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}))
    guardian_phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}))
    parent_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}), help_text='Required for minors under 18')
    is_minor = forms.BooleanField(required=False, initial=False, widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 rounded bg-[#131D33] border-[#1E293B]'}), help_text='Check if student is under 18')

    # Teacher specific
    employee_id = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}))
    designation = forms.CharField(required=False, initial='Assistant Professor', widget=forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}))
    qualifications = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}),
            'first_name': forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}),
            'last_name': forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}),
            'email': forms.EmailInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}),
            'role': forms.Select(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white', 'id': 'roleSelect'}),
            'phone': forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white'}),
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
