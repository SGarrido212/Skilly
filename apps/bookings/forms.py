from django import forms
from .models import Booking, BookingMessage

class BookingCreateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        label="Nombre *",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-medium text-slate-800',
            'placeholder': 'Juan'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        label="Apellido *",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-medium text-slate-800',
            'placeholder': 'Pérez'
        })
    )
    email = forms.EmailField(
        required=True,
        label="Correo Electrónico *",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-medium text-slate-800',
            'placeholder': 'juan@empresa.com'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Teléfono de Contacto",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-medium text-slate-800',
            'placeholder': '+56 9 1234 5678'
        })
    )
    company_name = forms.CharField(
        max_length=150,
        required=True,
        label="Nombre de la Empresa *",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-medium text-slate-800',
            'placeholder': 'TechCorp SpA'
        })
    )
    company_rut = forms.CharField(
        max_length=50,
        required=False,
        label="RUT / Identificación Fiscal de la Empresa",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-medium text-slate-800',
            'placeholder': '76.123.456-7'
        })
    )

    class Meta:
        model = Booking
        fields = ('project_requirements',)
        labels = {
            'project_requirements': 'Información Adicional / Detalle del Proyecto *'
        }
        widgets = {
            'project_requirements': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-medium text-slate-800',
                'rows': 4,
                'placeholder': 'Detalla los requerimientos específicos, objetivos y contexto del proyecto para el profesional...'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            self.fields['phone'].initial = user.phone
            org_profile = getattr(user, 'organization_profile', None)
            if org_profile:
                self.fields['company_name'].initial = org_profile.company_name
                self.fields['company_rut'].initial = org_profile.tax_id


class BookingMessageForm(forms.ModelForm):
    class Meta:
        model = BookingMessage
        fields = ('message', 'attachment')
        widgets = {
            'message': forms.TextInput(attrs={
                'class': 'flex-1 px-4 py-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 font-medium text-slate-800',
                'placeholder': 'Escribe un mensaje...'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'file-upload'
            })
        }
