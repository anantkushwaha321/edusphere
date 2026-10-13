from django import forms
from .models import AttendanceSession
from academics.models import Course


class AttendanceSessionForm(forms.ModelForm):
    class Meta:
        model = AttendanceSession
        fields = ['course', 'date', 'topic_covered']
        widgets = {
            'course': forms.Select(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'topic_covered': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'placeholder': 'e.g. Chapter 4: Binary Search Trees'}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher, is_active=True)
