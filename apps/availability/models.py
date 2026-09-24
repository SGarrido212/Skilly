from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class TimeSlot(models.Model):
    STATUS_DISPONIBLE = 'DISPONIBLE'
    STATUS_PRE_RESERVADO = 'PRE_RESERVADO'
    STATUS_OCUPADO = 'OCUPADO'

    STATUS_CHOICES = [
        (STATUS_DISPONIBLE, 'Disponible'),
        (STATUS_PRE_RESERVADO, 'Pre-reservado (Bloqueo 20m)'),
        (STATUS_OCUPADO, 'Ocupado'),
    ]

    professional = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='timeslots',
        limit_choices_to={'role': 'PROFESIONAL'}
    )
    date = models.DateField(verbose_name="Fecha")
    start_time = models.TimeField(verbose_name="Hora Inicio")
    end_time = models.TimeField(verbose_name="Hora Fin")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DISPONIBLE)
    reserved_until = models.DateTimeField(blank=True, null=True, help_text="Expiración del bloqueo temporal de 20 minutos")

    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['professional', 'date', 'start_time']

    @property
    def is_available(self):
        """Checks if slot is truly available (considering lock expiration)."""
        if self.status == self.STATUS_DISPONIBLE:
            return True
        if self.status == self.STATUS_PRE_RESERVADO and self.reserved_until:
            if timezone.now() > self.reserved_until:
                # Lock has expired!
                return True
        return False

    def lock_for_checkout(self):
        """Locks the timeslot for 20 minutes to prevent concurrent bookings."""
        if not self.is_available:
            return False
        self.status = self.STATUS_PRE_RESERVADO
        self.reserved_until = timezone.now() + timedelta(minutes=20)
        self.save()
        return True

    def mark_booked(self):
        self.status = self.STATUS_OCUPADO
        self.reserved_until = None
        self.save()

    def release_lock(self):
        self.status = self.STATUS_DISPONIBLE
        self.reserved_until = None
        self.save()

    def __str__(self):
        return f"{self.professional.get_full_name()} | {self.date} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')} ({self.get_status_display()})"
