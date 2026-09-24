# -- MODELO DE EVALUACIONES E INSIGNIAS CUALITATIVAS PRIVADAS --
from django.db import models
from django.conf import settings
from django.core.validators import MaxLengthValidator

class Badge(models.Model):
    # -- MODELO DE CUALIDADES / INSIGNIAS CUALITATIVAS DE PROFESIONALES --
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Cualidad")
    icon = models.CharField(max_length=50, default='fa-award', help_text="Icono FontAwesome")
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Review(models.Model):
    # -- REGISTRO CONFIDENCIAL DE EVALUACIÓN CUALITATIVA DE SERVICIO --
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='review')
    professional = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_reviews'
    )
    organization = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_reviews'
    )
    comments = models.TextField(
        blank=True,
        max_length=500,
        validators=[MaxLengthValidator(500)],
        verbose_name="Comentarios de Evaluación (Privados - Solo Admin)"
    )
    rating = models.IntegerField(
        default=5,
        null=True,
        blank=True,
        verbose_name="Calificación Interna"
    )
    badges = models.ManyToManyField(Badge, related_name='reviews', verbose_name="Cualidades Seleccionadas")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Evaluación Privada Reserva #{self.booking.id} - Pro: {self.professional.username}"
