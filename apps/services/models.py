from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre de la Categoría")
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, verbose_name="Descripción")
    icon = models.CharField(max_length=50, default='fa-briefcase', help_text="Clase de FontAwesome (ej. fa-code, fa-paint-brush)")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Service(models.Model):
    professional = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='services',
        limit_choices_to={'role': 'PROFESIONAL'}
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(max_length=200, verbose_name="Título del Servicio")
    description = models.TextField(verbose_name="Descripción Detallada")
    deliverables = models.TextField(verbose_name="Entregables Incluidos", help_text="Listado de lo que recibirá el cliente")
    estimated_duration = models.CharField(max_length=100, verbose_name="Duración Estimada", help_text="Ej: 2 horas, 3 días hábiles")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(1.00)],
        verbose_name="Tarifa ($ USD / CLP)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Servicio Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - ${self.price:,.0f}"
