from django import forms
from .models import Announcement


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'target_audience', 'department', 'priority', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none', 'placeholder': 'e.g. Schedule for Mid-Term Examinations Fall 2026'}),
            'content': forms.Textarea(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none', 'rows': 5, 'placeholder': 'Full announcement details and important dates...'}),
            'target_audience': forms.Select(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
            'department': forms.Select(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
            'priority': forms.Select(attrs={'class': 'app-input w-full px-3 py-2 rounded-md bg-[#131D33] border border-[#1E293B] text-white focus:border-blue-500 focus:outline-none'}),
            'attachment': forms.FileInput(attrs={'class': 'block w-full text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer'}),
        }
