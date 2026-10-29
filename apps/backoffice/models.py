from django.db import models
from django.conf import settings
from decimal import Decimal

class PlatformSetting(models.Model):
    """Configuración global de la plataforma Skilly (Take rate, comisiones y parámetros)."""
    take_rate_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('15.00'),
        verbose_name="Comisión Skilly (Take Rate %)"
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Actualizado por"
    )

    class Meta:
        verbose_name = "Configuración de Plataforma"
        verbose_name_plural = "Configuraciones de Plataforma"

    @classmethod
    def get_take_rate(cls):
        setting = cls.objects.first()
        if not setting:
            setting = cls.objects.create(take_rate_percentage=Decimal('15.00'))
        return setting.take_rate_percentage

    @classmethod
    def get_instance(cls):
        setting = cls.objects.first()
        if not setting:
            setting = cls.objects.create(take_rate_percentage=Decimal('15.00'))
        return setting

    def __str__(self):
        return f"Configuración Global Skilly - Take Rate: {self.take_rate_percentage}%"


class ValidationMessage(models.Model):
    """Mensajes de chat entre Administración y Profesionales para validación documental y coordinación de reuniones."""
    professional = models.ForeignKey(
        'users.ProfessionalProfile',
        on_delete=models.CASCADE,
        related_name='validation_messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_validation_messages'
    )
    message = models.TextField(verbose_name="Mensaje de Coordinación")
    meeting_link = models.URLField(blank=True, null=True, verbose_name="Enlace de Reunión (Google Meet, Zoom, etc.)")
    meeting_scheduled_at = models.DateTimeField(blank=True, null=True, verbose_name="Fecha y Hora Agendada para la Reunión")
    attachment = models.FileField(
        upload_to='validation_chat_files/',
        blank=True,
        null=True,
        verbose_name="Archivo o Documento Adjunto"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Mensaje de {self.sender.username} a {self.professional.user.username} ({self.created_at.strftime('%d/%m %H:%M')})"
