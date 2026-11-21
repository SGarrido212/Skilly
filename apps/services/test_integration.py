from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from services.models import Category, Service
from users.models import ProfessionalProfile

User = get_user_model()


class ServicesIntegrationTests(TestCase):
    def setUp(self):
        self.password = "SkillyTestPass2026!"
        self.pro_user = User.objects.create_user(
            username="pro_test",
            email="pro@example.com",
            password=self.password,
            role="PROFESIONAL",
        )
        self.other_pro = User.objects.create_user(
            username="pro_otro",
            email="otro@example.com",
            password=self.password,
            role="PROFESIONAL",
        )
        self.client_user = User.objects.create_user(
            username="cliente_test",
            email="cliente@example.com",
            password=self.password,
            role="CLIENTE",
        )
        ProfessionalProfile.objects.create(
            user=self.pro_user,
            profession="Desarrollador Backend",
        )
        ProfessionalProfile.objects.create(
            user=self.other_pro,
            profession="Diseñador UI/UX",
        )

        self.cat_dev = Category.objects.create(name="Desarrollo Web")
        self.cat_design = Category.objects.create(name="Diseño UX")

        self.active_service = Service.objects.create(
            professional=self.pro_user,
            category=self.cat_dev,
            title="API en Django",
            description="Backend completo con pruebas",
            deliverables="Código fuente y documentación",
            estimated_duration="3 días hábiles",
            price=Decimal("45000.00"),
            is_active=True,
        )
        self.inactive_service = Service.objects.create(
            professional=self.pro_user,
            category=self.cat_design,
            title="Auditoría oculta",
            description="No visible en catálogo",
            deliverables="Informe",
            estimated_duration="1 día",
            price=Decimal("20000.00"),
            is_active=False,
        )

    def test_marketplace_filtra_activos_categoria_y_precio(self):
        url = reverse("services:marketplace")
        response = self.client.get(
            url,
            {"category": self.cat_dev.slug, "q": "Django", "max_price": "50000"},
        )

        self.assertEqual(response.status_code, 200)
        services_in_ctx = list(response.context["services"])
        self.assertIn(self.active_service, services_in_ctx)
        self.assertNotIn(self.inactive_service, services_in_ctx)

    def test_detalle_servicio_inactivo_retorna_404(self):
        url = reverse("services:service_detail", kwargs={"pk": self.inactive_service.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_cliente_no_puede_crear_servicio(self):
        self.client.force_login(self.client_user)
        url = reverse("services:service_create")
        payload = {
            "category": self.cat_dev.pk,
            "title": "Servicio no autorizado",
            "description": "Intento de creación por cliente",
            "deliverables": "Nada",
            "estimated_duration": "1 hora",
            "price": "10000.00",
        }

        response = self.client.post(url, data=payload)
        self.assertRedirects(response, reverse("services:marketplace"))
        self.assertFalse(Service.objects.filter(title="Servicio no autorizado").exists())

    def test_profesional_crea_servicio_y_redirige_a_dashboard(self):
        self.client.force_login(self.pro_user)
        url = reverse("services:service_create")
        payload = {
            "category": self.cat_dev.pk,
            "title": "Configuración de PostgreSQL",
            "description": "Optimización e índices",
            "deliverables": "Script y guía",
            "estimated_duration": "2 horas",
            "price": "30000.00",
        }

        response = self.client.post(url, data=payload)
        self.assertRedirects(response, reverse("users:pro_dashboard"))

        created = Service.objects.get(title="Configuración de PostgreSQL")
        self.assertEqual(created.professional, self.pro_user)
        self.assertFalse(created.is_active)

    def test_otro_profesional_no_puede_editar_servicio_ajeno(self):
        self.client.force_login(self.other_pro)
        url = reverse("services:service_edit", kwargs={"pk": self.active_service.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)