from django import forms
from .models import Assignment, Submission
from academics.models import Course


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['course', 'title', 'description', 'max_marks', 'due_date', 'attachment', 'status']
        widgets = {
            'course': forms.Select(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
            'title': forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none', 'placeholder': 'e.g. Midterm Project: Distributed Systems'}),
            'description': forms.Textarea(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none', 'rows': 4, 'placeholder': 'Detailed instructions, problem description, and submission guidelines...'}),
            'max_marks': forms.NumberInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
            'attachment': forms.FileInput(attrs={'class': 'block w-full text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer'}),
            'status': forms.Select(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher, is_active=True)


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file', 'submission_text']
        widgets = {
            'submission_text': forms.Textarea(attrs={
                'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none',
                'rows': 4,
                'placeholder': 'Add notes, explanations, or links to accompany your submission...'
            }),
            'file': forms.FileInput(attrs={'class': 'block w-full text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer'}),
        }


class GradingForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['marks_obtained', 'feedback', 'status']
        widgets = {
            'marks_obtained': forms.NumberInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none', 'step': '0.5'}),
            'feedback': forms.Textarea(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none', 'rows': 3, 'placeholder': 'Detailed teacher evaluation and feedback...'}),
            'status': forms.Select(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
        }
