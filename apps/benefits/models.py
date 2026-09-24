from django.db import models

class Benefit(models.Model):
    title = models.CharField(max_length=150, verbose_name="Título del Beneficio")
    provider = models.CharField(max_length=100, verbose_name="Proveedor / Alianza")
    category = models.CharField(max_length=100, verbose_name="Categoría", help_text="Ej: Seguros & Salud, Formación, Herramientas Work")
    description = models.TextField(verbose_name="Descripción")
    logo = models.ImageField(upload_to='benefit_logos/', blank=True, null=True, verbose_name="Logo / Imagen")
    activation_url = models.URLField(blank=True, default='#', verbose_name="Enlace de Activación")
    badge_text = models.CharField(max_length=50, default='Descuento Exclusivo', verbose_name="Etiqueta Promocional")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.provider})"
