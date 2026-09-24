# -- FORMULARIO DE EVALUACIÓN PRIVADA DE CUALIDADES Y RETROALIMENTACIÓN --
from django import forms
from .models import Review, Badge
from django.core.exceptions import ValidationError

class ReviewForm(forms.ModelForm):
    badges = forms.ModelMultipleChoiceField(
        queryset=Badge.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'space-y-2'}),
        required=False,
        label="Cualidades Destacadas del Profesional"
    )

    custom_badge = forms.CharField(
        max_length=100,
        required=False,
        label="Agregar Cualidad Extra",
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 font-medium text-slate-800',
            'placeholder': 'Ej. Excelente adaptabilidad, Orientación al detalle, Puntualidad'
        })
    )

    class Meta:
        model = Review
        fields = ('comments', 'badges')
        widgets = {
            'comments': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'rows': 4,
                'placeholder': 'Comentarios confidenciales sobre el desempeño (Visibilidad exclusiva para Back-Office)...'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        badges = cleaned_data.get('badges')
        custom_badge = cleaned_data.get('custom_badge', '').strip()

        # -- VALIDACIÓN: AL MENOS 1 CUALIDAD SELECCIONADA O INGRESADA --
        if not badges and not custom_badge:
            raise ValidationError("Debes seleccionar al menos una cualidad o ingresar una cualidad extra.")

        return cleaned_data
