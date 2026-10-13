from django import forms
from .models import StudyMaterial
from academics.models import Course


class StudyMaterialForm(forms.ModelForm):
    class Meta:
        model = StudyMaterial
        fields = ['course', 'title', 'unit_module', 'description', 'file', 'external_link']
        widgets = {
            'course': forms.Select(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
            'title': forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none', 'placeholder': 'e.g. Lecture Notes: Data Structures'}),
            'unit_module': forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none', 'placeholder': 'e.g. Unit 2: Sorting Algorithms'}),
            'description': forms.Textarea(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none', 'rows': 3, 'placeholder': 'Brief description of these study materials...'}),
            'file': forms.FileInput(attrs={'class': 'block w-full text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer'}),
            'external_link': forms.URLInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none', 'placeholder': 'https://...'}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course'].queryset = Course.objects.filter(teacher=teacher, is_active=True)
