from django.test import TestCase, Client
from django.urls import reverse
from users.models import CustomUser, ProfessionalProfile, OrganizationProfile, StrikeRecord
from services.models import Category, Service
from bookings.models import Booking
from escrow_payments.models import PaymentTransaction
from benefits.models import Benefit
from reviews.models import Badge
import datetime

class BackofficeTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Admin user
        self.admin_user = CustomUser.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='password123',
            role=CustomUser.ROLE_ADMIN,
            is_staff=True,
            is_superuser=True
        )

        # Pro user
        self.pro_user = CustomUser.objects.create_user(
            username='pro_test',
            email='pro@test.com',
            password='password123',
            role=CustomUser.ROLE_PROFESIONAL
        )
        self.pro_profile = ProfessionalProfile.objects.create(
            user=self.pro_user,
            profession='Desarrollador Django',
            hourly_rate=100.00
        )

        # Org user
        self.org_user = CustomUser.objects.create_user(
            username='org_test',
            email='org@test.com',
            password='password123',
            role=CustomUser.ROLE_ORGANIZACION
        )
        self.org_profile = OrganizationProfile.objects.create(
            user=self.org_user,
            company_name='Empresa Test',
            tax_id='12345678-9'
        )

        # Category and Service
        self.category = Category.objects.create(
            name='Desarrollo Web',
            slug='desarrollo-web',
            icon='fa-code'
        )
        self.service = Service.objects.create(
            professional=self.pro_user,
            category=self.category,
            title='Landing Page Django',
            description='Servicio de prueba',
            deliverables='Código fuente',
            estimated_duration='3 días',
            price=150000.00,
            status=Service.STATUS_EN_REVISION
        )

    def test_security_redirect_non_admin(self):
        self.client.login(username='pro_test', password='password123')
        response = self.client.get(reverse('backoffice:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_view(self):
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('backoffice:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Panel Administrativo Skilly")
        self.assertContains(response, "Landing Page Django")

    def test_users_management_view(self):
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('backoffice:users_management'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "pro_test")
        self.assertContains(response, "org_test")

    def test_user_detail_view(self):
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(reverse('backoffice:user_detail', kwargs={'user_id': self.pro_user.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Desarrollador Django")

    def test_apply_and_revoke_strike(self):
        self.client.login(username='admin_test', password='password123')
        # Apply strike
        response = self.client.post(
            reverse('backoffice:apply_strike', kwargs={'user_id': self.pro_user.id}),
            {'reason': 'Falta de respuesta reiterada a requerimientos de cliente'}
        )
        self.assertEqual(response.status_code, 302)
        self.pro_profile.refresh_from_db()
        self.assertEqual(self.pro_profile.strikes_count, 1)

        strike = self.pro_profile.strike_records.first()
        self.assertIsNotNone(strike)
        self.assertTrue(strike.is_active)

        # Revoke strike
        response = self.client.get(reverse('backoffice:revoke_strike', kwargs={'strike_id': strike.id}))
        self.assertEqual(response.status_code, 302)
        self.pro_profile.refresh_from_db()
        self.assertEqual(self.pro_profile.strikes_count, 0)

    def test_service_moderation_actions(self):
        self.client.login(username='admin_test', password='password123')
        # Approve service
        response = self.client.post(
            reverse('backoffice:service_moderation_action', kwargs={'pk': self.service.pk}),
            {'action': 'approve', 'admin_feedback': 'Excelente servicio'}
        )
        self.assertEqual(response.status_code, 302)
        self.service.refresh_from_db()
        self.assertEqual(self.service.status, Service.STATUS_PUBLICADO)
        self.assertTrue(self.service.is_active)

    def test_benefits_and_categories_views(self):
        self.client.login(username='admin_test', password='password123')
        
        # Test benefits
        response = self.client.get(reverse('backoffice:benefits_management'))
        self.assertEqual(response.status_code, 200)

        # Create benefit
        post_response = self.client.post(
            reverse('backoffice:benefits_management'),
            {
                'title': 'Seguro Mutual',
                'provider': 'Mutual',
                'category': 'Salud',
                'badge_text': 'Descuento',
                'activation_url': 'https://mutual.cl',
                'description': 'Cobertura completa',
                'is_active': True
            }
        )
        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(Benefit.objects.filter(title='Seguro Mutual').exists())

        # Test categories
        cat_response = self.client.get(reverse('backoffice:categories_management'))
        self.assertEqual(cat_response.status_code, 200)

    def test_escrow_ledger_and_bookings_monitor(self):
        self.client.login(username='admin_test', password='password123')

        # Create a booking
        booking = Booking.objects.create(
            service=self.service,
            professional=self.pro_user,
            organization=self.org_user,
            scheduled_date=datetime.date.today(),
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0),
            project_requirements='Test reqs',
            status=Booking.STATUS_PAGADO_EN_CUSTODIA,
            skilly_staff_supervision_requested=True
        )

        from decimal import Decimal
        tx = PaymentTransaction.objects.create(
            booking=booking,
            total_amount=Decimal('150000.00'),
            escrow_status=PaymentTransaction.STATUS_RETENIDO
        )

        # Render Escrow Ledger
        ledger_response = self.client.get(reverse('backoffice:escrow_ledger'))
        self.assertEqual(ledger_response.status_code, 200)
        self.assertContains(ledger_response, tx.transaction_id)
        self.assertContains(ledger_response, f"Reserva #{booking.id}")

        # Render Bookings Monitor
        monitor_response = self.client.get(reverse('backoffice:bookings_monitor'))
        self.assertEqual(monitor_response.status_code, 200)
        self.assertContains(monitor_response, f"Reserva #{booking.id}")

    def test_update_take_rate_action(self):
        self.client.login(username='admin_test', password='password123')
        from decimal import Decimal
        from backoffice.models import PlatformSetting

        # Update take rate to 18.50%
        response = self.client.post(
            reverse('backoffice:update_take_rate'),
            {'take_rate_percentage': '18.50'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PlatformSetting.get_take_rate(), Decimal('18.50'))

        # Verify dashboard displays new take rate
        dash_response = self.client.get(reverse('backoffice:dashboard'))
        self.assertEqual(dash_response.status_code, 200)
        self.assertContains(dash_response, "18.5")

    def test_validation_chat_and_meeting_coordination(self):
        self.client.login(username='admin_test', password='password123')
        from backoffice.models import ValidationMessage

        # Admin posts a coordination message with meeting link and date
        response = self.client.post(
            reverse('backoffice:validation_chat', kwargs={'pro_id': self.pro_profile.id}),
            {
                'message': 'Hola Carlos, coordinemos una reunión de validación por Google Meet.',
                'meeting_scheduled_at': '2026-10-25T15:30',
                'meeting_link': 'https://meet.google.com/abc-defg-hij'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ValidationMessage.objects.filter(professional=self.pro_profile).count(), 1)

        msg = ValidationMessage.objects.first()
        self.assertEqual(msg.meeting_link, 'https://meet.google.com/abc-defg-hij')

        # Admin views the chat
        chat_admin_response = self.client.get(reverse('backoffice:validation_chat', kwargs={'pro_id': self.pro_profile.id}))
        self.assertEqual(chat_admin_response.status_code, 200)
        self.assertContains(chat_admin_response, "https://meet.google.com/abc-defg-hij")

        # Professional logs in and views their own validation chat
        self.client.login(username='pro_test', password='password123')
        pro_chat_response = self.client.get(reverse('backoffice:pro_own_validation_chat'))
        self.assertEqual(pro_chat_response.status_code, 200)
        self.assertContains(pro_chat_response, "Google Meet")

        # Professional replies
        pro_reply = self.client.post(
            reverse('backoffice:pro_own_validation_chat'),
            {'message': 'Perfecto, confirmado el día 25 a las 15:30.'}
        )
        self.assertEqual(pro_reply.status_code, 302)
        self.assertEqual(ValidationMessage.objects.filter(professional=self.pro_profile).count(), 2)


