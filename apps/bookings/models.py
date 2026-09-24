from django.db import models
from django.conf import settings
from django.utils import timezone
import datetime

class Booking(models.Model):
    STATUS_PENDIENTE = 'PENDIENTE'
    STATUS_PRE_RESERVADA = 'PRE_RESERVADA'
    STATUS_ACEPTADA = 'ACEPTADA'
    STATUS_RECHAZADA = 'RECHAZADA'
    STATUS_PAGADO_EN_CUSTODIA = 'PAGADO_EN_CUSTODIA'
    STATUS_EN_EJECUCION = 'EN_EJECUCION'
    STATUS_ENTREGADO = 'ENTREGADO'
    STATUS_FINALIZADO = 'FINALIZADO'
    STATUS_EN_DISPUTA = 'EN_DISPUTA'
    STATUS_CANCELADO = 'CANCELADO'

    STATUS_CHOICES = [
        (STATUS_PENDIENTE, 'Pendiente de Aprobación'),
        (STATUS_PRE_RESERVADA, 'Pre-reservada (Checkout Pendiente)'),
        (STATUS_ACEPTADA, 'Aceptada por Profesional'),
        (STATUS_RECHAZADA, 'Rechazada'),
        (STATUS_PAGADO_EN_CUSTODIA, 'Pagado en Custodia (Escrow)'),
        (STATUS_EN_EJECUCION, 'En Ejecución'),
        (STATUS_ENTREGADO, 'Entregado por Profesional'),
        (STATUS_FINALIZADO, 'Finalizado'),
        (STATUS_EN_DISPUTA, 'En Disputa'),
        (STATUS_CANCELADO, 'Cancelado'),
    ]

    service = models.ForeignKey('services.Service', on_delete=models.CASCADE, related_name='bookings')
    professional = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_bookings'
    )
    organization = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_bookings'
    )
    timeslot = models.ForeignKey('availability.TimeSlot', on_delete=models.SET_NULL, null=True, blank=True)
    scheduled_date = models.DateField(verbose_name="Fecha Agendada")
    start_time = models.TimeField(verbose_name="Hora Inicio")
    end_time = models.TimeField(verbose_name="Hora Fin")
    project_requirements = models.TextField(verbose_name="Requerimientos / Detalles del Proyecto")
    
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDIENTE)
    
    # Policy tracking & alert calculations
    cancellation_penalty_applies = models.BooleanField(default=False, help_text="True si se canceló con menos de 24h de anticipación")
    
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def hours_until_start(self):
        """Calculates hours left until the scheduled date & time."""
        if not self.scheduled_date or not self.start_time:
            return 999
        scheduled_dt = datetime.datetime.combine(self.scheduled_date, self.start_time)
        if timezone.is_aware(timezone.now()):
            tz = timezone.get_current_timezone()
            scheduled_dt = timezone.make_aware(scheduled_dt, tz)
        delta = scheduled_dt - timezone.now()
        return delta.total_seconds() / 3600.0

    @property
    def is_cancellation_within_24h(self):
        """True if trying to cancel less than 24 hours before event."""
        return self.hours_until_start < 24

    def __str__(self):
        return f"Reserva #{self.id}: {self.service.title} - {self.organization.get_full_name()} ({self.get_status_display()})"


class BookingMessage(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField(verbose_name="Mensaje")
    attachment = models.FileField(upload_to='booking_chats/', blank=True, null=True, verbose_name="Archivo Adjunto")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Mensaje de {self.sender.username} en Reserva #{self.booking.id} - {self.timestamp.strftime('%H:%M %d/%m')}"
