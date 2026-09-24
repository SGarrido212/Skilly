from django import forms
from .models import Service, Category

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ('title', 'category', 'description', 'deliverables', 'estimated_duration', 'price', 'is_active')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500', 'placeholder': 'Ej. Desarrollar Landing Page de Alto Impacto con Django'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500', 'rows': 4, 'placeholder': 'Explica detalladamente en qué consiste tu servicio...'}),
            'deliverables': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500', 'rows': 3, 'placeholder': '- Código fuente documentado\n- Despliegue en servidor producción\n- Manual de usuario'}),
            'estimated_duration': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500', 'placeholder': 'Ej. 3 días hábiles (15 horas en total)'}),
            'price': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500', 'placeholder': '250000'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500 border-slate-300'}),
        }
