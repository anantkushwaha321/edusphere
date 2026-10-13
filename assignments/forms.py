from django import forms
from .models import Assignment, Submission
from academics.models import Course


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['course', 'title', 'description', 'max_marks', 'due_date', 'attachment', 'status']
        widgets = {
            'course': forms.Select(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'title': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'rows': 4}),
            'max_marks': forms.NumberInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'attachment': forms.FileInput(attrs={'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
            'status': forms.Select(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
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
                'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none',
                'rows': 4,
                'placeholder': 'Add notes, explanations, or links to accompany your submission...'
            }),
            'file': forms.FileInput(attrs={'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
        }


class GradingForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['marks_obtained', 'feedback', 'status']
        widgets = {
            'marks_obtained': forms.NumberInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'step': '0.5'}),
            'feedback': forms.Textarea(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'rows': 3, 'placeholder': 'Detailed teacher evaluation and feedback...'}),
            'status': forms.Select(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
        }
