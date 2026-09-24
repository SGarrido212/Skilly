from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

def validate_min_length_50(value):
    if len(value.strip()) < 50:
        raise ValidationError("El motivo de la disputa debe contener al menos 50 caracteres para un análisis objetivo.")

class Dispute(models.Model):
    STATUS_ABIERTA = 'ABIERTA'
    STATUS_RESUELTA_PROFESIONAL = 'RESUELTA_PROFESIONAL'
    STATUS_RESUELTA_ORGANIZACION = 'RESUELTA_ORGANIZACION'
    STATUS_RESUELTA_MIXTA = 'RESUELTA_MIXTA'

    STATUS_CHOICES = [
        (STATUS_ABIERTA, 'Abierta / En Mediación'),
        (STATUS_RESUELTA_PROFESIONAL, 'Resuelta a Favor del Profesional'),
        (STATUS_RESUELTA_ORGANIZACION, 'Resuelta a Favor de la Organización'),
        (STATUS_RESUELTA_MIXTA, 'Resuelta con Acuerdo Mixto'),
    ]

    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='dispute')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='filed_disputes')
    reason = models.TextField(
        validators=[validate_min_length_50],
        verbose_name="Motivo Detallado de la Disputa",
        help_text="Explique la controversia con claridad (Mínimo 50 caracteres)."
    )
    evidence = models.FileField(
        upload_to='dispute_evidences/',
        blank=True,
        null=True,
        verbose_name="Evidencia Adjunta (Capturas/Documentos PDF)"
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_ABIERTA)
    resolution_notes = models.TextField(blank=True, null=True, verbose_name="Notas de Resolución del Administrador")
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_disputes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Disputa en Reserva #{self.booking.id} - Estado: {self.get_status_display()}"
