from django import forms
from .models import Dispute

class DisputeForm(forms.ModelForm):
    class Meta:
        model = Dispute
        fields = ('reason', 'evidence')
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-rose-500 focus:border-rose-500',
                'rows': 5,
                'placeholder': 'Describa detalladamente el problema o incumplimiento detectado (Mínimo 50 caracteres)...'
            }),
            'evidence': forms.FileInput(attrs={
                'class': 'w-full text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-rose-50 file:text-rose-700 hover:file:bg-rose-100'
            })
        }
