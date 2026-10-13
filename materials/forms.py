from django import forms
from .models import StudyMaterial
from academics.models import Course


class StudyMaterialForm(forms.ModelForm):
    class Meta:
        model = StudyMaterial
        fields = ['course', 'title', 'unit_module', 'description', 'file', 'external_link']
        widgets = {
            'course': forms.Select(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'title': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none'}),
            'unit_module': forms.TextInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'placeholder': 'e.g. Unit 2: Sorting Algorithms'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'rows': 3}),
            'file': forms.FileInput(attrs={'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
            'external_link': forms.URLInput(attrs={'class': 'w-full px-3.5 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:outline-none', 'placeholder': 'https://...'}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher, is_active=True)
