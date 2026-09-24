from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.core.exceptions import ValidationError

def validate_file_size(value):
    filesize = value.size
    if filesize > 5 * 1024 * 1024:  # 5MB limit
        raise ValidationError("El archivo no puede exceder los 5MB de tamaño.")

class CustomUser(AbstractUser):
    ROLE_PROFESIONAL = 'PROFESIONAL'
    ROLE_ORGANIZACION = 'ORGANIZACION'
    ROLE_ADMIN = 'ADMIN'

    ROLE_CHOICES = [
        (ROLE_PROFESIONAL, 'Profesional Independiente'),
        (ROLE_ORGANIZACION, 'Empresa / Organización'),
        (ROLE_ADMIN, 'Administrador Skilly'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_ORGANIZACION)
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono de Contacto")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_professional(self):
        return self.role == self.ROLE_PROFESIONAL

    @property
    def is_organization(self):
        return self.role == self.ROLE_ORGANIZACION

    @property
    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


class ProfessionalProfile(models.Model):
    STATUS_PENDIENTE = 'PENDIENTE'
    STATUS_VALIDADO = 'VALIDADO'
    STATUS_RECHAZADO = 'RECHAZADO'

    VALIDATION_CHOICES = [
        (STATUS_PENDIENTE, 'Pendiente de Validación'),
        (STATUS_VALIDADO, 'Validado'),
        (STATUS_RECHAZADO, 'Rechazado'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='professional_profile')
    profession = models.CharField(max_length=150, verbose_name="Profesión / Título Principal")
    bio = models.TextField(blank=True, verbose_name="Biografía / Presentación")
    slug = models.SlugField(unique=True, max_length=150, verbose_name="URL del Perfil público")
    validation_status = models.CharField(max_length=20, choices=VALIDATION_CHOICES, default=STATUS_PENDIENTE)
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="Motivo de Rechazo")
    support_document = models.FileField(
        upload_to='pro_documents/',
        blank=True,
        null=True,
        validators=[validate_file_size],
        verbose_name="Documentos de Respaldo (PDF/Imagen, Máx 5MB)"
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Foto de Perfil")
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Tarifa por Hora Promedio ($)")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.user.first_name}-{self.user.last_name}") or slugify(self.user.username)
            slug = base_slug
            count = 1
            while ProfessionalProfile.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Perfil Pro: {self.profession} - {self.user.get_full_name() or self.user.username}"


class OrganizationProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='organization_profile')
    company_name = models.CharField(max_length=150, verbose_name="Nombre de la Empresa")
    tax_id = models.CharField(max_length=50, verbose_name="RUT / Razón Social")
    description = models.TextField(blank=True, verbose_name="Descripción de la Organización")
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True, verbose_name="Logo de la Empresa")

    def __str__(self):
        return f"{self.company_name} ({self.tax_id})"
