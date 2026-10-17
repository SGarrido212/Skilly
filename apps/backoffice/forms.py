from django import forms
from users.models import StrikeRecord, ProfessionalProfile
from services.models import Service, Category
from benefits.models import Benefit
from reviews.models import Badge
from .models import PlatformSetting, ValidationMessage

class TakeRateForm(forms.ModelForm):
    class Meta:
        model = PlatformSetting
        fields = ('take_rate_percentage',)
        widgets = {
            'take_rate_percentage': forms.NumberInput(attrs={
                'class': 'w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm font-black text-purple-700 bg-white focus:ring-2 focus:ring-purple-500',
                'step': '0.50',
                'min': '0.00',
                'max': '100.00',
                'placeholder': '15.00'
            })
        }

class ValidationMessageForm(forms.ModelForm):
    meeting_scheduled_at = forms.DateTimeField(
        required=False,
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'],
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs'
        })
    )

    class Meta:
        model = ValidationMessage
        fields = ('message', 'meeting_scheduled_at', 'meeting_link')
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'rows': 3,
                'placeholder': 'Escriba un mensaje para coordinar la reunión o solicitar aclaraciones...'
            }),
            'meeting_link': forms.URLInput(attrs={
                'class': 'w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs',
                'placeholder': 'https://meet.google.com/xxx-xxxx-xxx o Zoom'
            }),
        }


class StrikeForm(forms.ModelForm):
    class Meta:
        model = StrikeRecord
        fields = ('reason',)
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-rose-500 focus:border-rose-500',
                'rows': 3,
                'placeholder': 'Describa el motivo de la amonestación (incumplimiento de plazos, falta de respuesta, comportamiento indebido, etc.)...'
            })
        }

class AdminProNotesForm(forms.ModelForm):
    class Meta:
        model = ProfessionalProfile
        fields = ('admin_notes',)
        widgets = {
            'admin_notes': forms.Textarea(attrs={
                'class': 'w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-purple-500 focus:border-purple-500',
                'rows': 4,
                'placeholder': 'Anotaciones internas exclusivas para el equipo de administración (seguimiento, antecedentes, llamadas de atención, etc.)...'
            })
        }

class ServiceModerationForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ('title', 'category', 'price', 'status', 'admin_feedback', 'is_active')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 text-xs'}),
            'category': forms.Select(attrs={'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 text-xs'}),
            'price': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 text-xs'}),
            'status': forms.Select(attrs={'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 text-xs font-bold'}),
            'admin_feedback': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-slate-300 text-xs',
                'rows': 3,
                'placeholder': 'Observaciones para el profesional si se rechaza o se pide cambios...'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-purple-600 rounded border-slate-300'}),
        }

class BenefitForm(forms.ModelForm):
    class Meta:
        model = Benefit
        fields = ('title', 'provider', 'category', 'badge_text', 'activation_url', 'description', 'is_active')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 text-xs', 'placeholder': 'Ej. 30% Descuento Platzi Enterprise'}),
            'provider': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 text-xs', 'placeholder': 'Ej. Platzi / AWS / Coopeuch'}),
            'category': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 text-xs', 'placeholder': 'Ej. Formación & Cursos, Seguros, Cloud'}),
            'badge_text': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 text-xs', 'placeholder': 'Ej. Descuento Exclusivo'}),
            'activation_url': forms.URLInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 text-xs', 'placeholder': 'https://...'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 text-xs', 'rows': 3, 'placeholder': 'Detalles y términos de la alianza...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-purple-600 rounded border-slate-300'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'icon', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 text-xs', 'placeholder': 'Nombre de la categoría'}),
            'icon': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 text-xs', 'placeholder': 'fa-code, fa-laptop, fa-chart-line...'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 text-xs', 'rows': 2, 'placeholder': 'Breve descripción de los servicios englobados...'}),
        }

class BadgeForm(forms.ModelForm):
    class Meta:
        model = Badge
        fields = ('name', 'icon', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 text-xs', 'placeholder': 'Ej. Entrega Impecable'}),
            'icon': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 text-xs', 'placeholder': 'fa-medal, fa-award, fa-star...'}),
            'description': forms.TextInput(attrs={'class': 'w-full px-3 py-2 rounded-xl border border-slate-300 text-xs', 'placeholder': 'Criterio para asignación...'}),
        }
