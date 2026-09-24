from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime
from users.models import CustomUser, ProfessionalProfile, OrganizationProfile
from services.models import Category, Service
from availability.models import TimeSlot
from reviews.models import Badge
from benefits.models import Benefit

class Command(BaseCommand):
    help = "Siembra la base de datos con usuarios demo (Admin, Pro Validado, Pro Pendiente, Organización), categorías, insignias y servicios iniciales."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Iniciando sembrado de datos en Skilly MVP..."))

        # 1. Categories
        cat_dev, _ = Category.objects.get_or_create(
            slug='desarrollo-software',
            defaults={'name': 'Desarrollo Software', 'description': 'Desarrollo web, móvil y arquitecturas backend', 'icon': 'fa-code'}
        )
        cat_ux, _ = Category.objects.get_or_create(
            slug='diseno-ux',
            defaults={'name': 'Diseño & UX/UI', 'description': 'Sistemas de diseño, prototipos e interfaces de alto impacto', 'icon': 'fa-paint-brush'}
        )
        cat_legal, _ = Category.objects.get_or_create(
            slug='consultoria-legal',
            defaults={'name': 'Consultoría Legal', 'description': 'Asesoría jurídica corporativa y cumplimiento tributario', 'icon': 'fa-scale-balanced'}
        )
        cat_mkt, _ = Category.objects.get_or_create(
            slug='marketing-digital',
            defaults={'name': 'Marketing Digital', 'description': 'Growth marketing, SEO y estrategia digital', 'icon': 'fa-bullhorn'}
        )

        self.stdout.write(self.style.SUCCESS("[OK] Categorias creadas."))

        # 2. Badges
        badges_data = [
            ("Entrega a tiempo", "fa-clock", "Cumplimiento puntual de plazos"),
            ("Comunicación fluida", "fa-comments", "Excelente claridad y respuesta"),
            ("Resolutivo", "fa-bolt", "Capacidad de resolver problemas complejos"),
            ("Excelente calidad", "fa-star", "Superó las expectativas técnica y visualmente"),
            ("Dominio técnico alto", "fa-laptop-code", "Demostró amplio conocimiento senior"),
        ]
        for name, icon, desc in badges_data:
            Badge.objects.get_or_create(name=name, defaults={'icon': icon, 'description': desc})

        self.stdout.write(self.style.SUCCESS("[OK] Insignias cualitativas creadas."))

        # 3. Benefits
        benefits_data = [
            ("Seguro de Salud Freelance - Coopeuch", "Coopeuch Seguros", "Seguros & Salud", "Cobertura de salud complementaria y urgencias para independientes con tarifa preferencial.", "https://coopeuch.cl", "Membresía Activa"),
            ("Platzi Enterprise 30% OFF", "Platzi", "Formación & Cursos", "Acceso con descuento exclusivo a rutas de aprendizaje en tecnología y liderazgo.", "https://platzi.com", "Descuento Exclusivo"),
            ("AWS Cloud Credits ($1,000 USD)", "Amazon Web Services", "Herramientas Cloud", "Créditos promocionales para infraestructura cloud en proyectos de clientes Skilly.", "https://aws.amazon.com", "Beneficio Premium"),
        ]
        for title, provider, category, desc, url, badge in benefits_data:
            Benefit.objects.get_or_create(title=title, defaults={
                'provider': provider,
                'category': category,
                'description': desc,
                'activation_url': url,
                'badge_text': badge
            })

        self.stdout.write(self.style.SUCCESS("[OK] Beneficios creados."))

        # 4. Users
        # Admin User
        admin_user, created_admin = CustomUser.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@skilly.com',
                'first_name': 'Administrador',
                'last_name': 'Skilly',
                'role': CustomUser.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created_admin:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("[OK] Usuario Admin creado (admin@skilly.com / admin123)."))

        # Validated Professional User
        pro_user, created_pro = CustomUser.objects.get_or_create(
            username='carlos_pro',
            defaults={
                'email': 'carlos@skilly.com',
                'first_name': 'Carlos',
                'last_name': 'Mendoza',
                'phone': '+56 9 8765 4321',
                'role': CustomUser.ROLE_PROFESIONAL
            }
        )
        if created_pro:
            pro_user.set_password('pro123')
            pro_user.save()

        pro_profile, _ = ProfessionalProfile.objects.get_or_create(
            user=pro_user,
            defaults={
                'profession': 'Senior Full Stack & Python Architect',
                'bio': 'Más de 8 años de experiencia diseñando e implementando arquitecturas limpias, Django 5+, PostgreSQL y entornos cloud de alta disponibilidad.',
                'validation_status': ProfessionalProfile.STATUS_VALIDADO,
                'slug': 'carlos-dev',
                'hourly_rate': 60.00
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Profesional Validado creado (carlos_pro / pro123 - /pro/carlos-dev)."))

        # Pending Professional User (for testing validation flow)
        pro_pending_user, created_pending = CustomUser.objects.get_or_create(
            username='ana_pro',
            defaults={
                'email': 'ana@skilly.com',
                'first_name': 'Ana',
                'last_name': 'Silva',
                'phone': '+56 9 1122 3344',
                'role': CustomUser.ROLE_PROFESIONAL
            }
        )
        if created_pending:
            pro_pending_user.set_password('pro123')
            pro_pending_user.save()

        ProfessionalProfile.objects.get_or_create(
            user=pro_pending_user,
            defaults={
                'profession': 'Lead Product Designer UX/UI',
                'bio': 'Especialista en Design Systems y prototipos interactivos en Figma.',
                'validation_status': ProfessionalProfile.STATUS_PENDIENTE,
                'slug': 'ana-ux',
                'hourly_rate': 55.00
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Profesional Pendiente creado (ana_pro / pro123)."))

        # Organization User
        org_user, created_org = CustomUser.objects.get_or_create(
            username='tech_corp',
            defaults={
                'email': 'contacto@techcorp.cl',
                'first_name': 'TechCorp',
                'last_name': 'Chile',
                'phone': '+56 2 2345 6789',
                'role': CustomUser.ROLE_ORGANIZACION
            }
        )
        if created_org:
            org_user.set_password('org123')
            org_user.save()

        OrganizationProfile.objects.get_or_create(
            user=org_user,
            defaults={
                'company_name': 'TechCorp SpA',
                'tax_id': '77.654.321-9',
                'description': 'Empresa referente en innovación tecnológica y aceleración de productos digitales.'
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Organizacion cliente creada (tech_corp / org123)."))

        # 5. Services for Carlos Mendoza
        s1, _ = Service.objects.get_or_create(
            professional=pro_user,
            title='Desarrollo MVP Backend Django 5 & APIs REST',
            defaults={
                'category': cat_dev,
                'description': 'Construcción modular completa de arquitectura backend con Django 5, PostgreSQL y seguridad robusta.',
                'deliverables': '- Código fuente completo con Clean Architecture\n- APIs REST documentadas\n- Panel de administración Django configurado\n- Despliegue en servidor de pruebas',
                'estimated_duration': '3 días hábiles (20 horas efectivas)',
                'price': 350000.00,
                'is_active': True
            }
        )

        s2, _ = Service.objects.get_or_create(
            professional=pro_user,
            title='Auditoría de Código, Rendimiento y Seguridad Python',
            defaults={
                'category': cat_dev,
                'description': 'Revisión exhaustiva de código existente, detección de bottlenecks de rendimiento y optimización de consultas ORM.',
                'deliverables': '- Informe de vulnerabilidades y optimización\n- Propuesta de refactorización\n- Sesión de mediación técnica de 1 hora',
                'estimated_duration': '1 día hábil',
                'price': 180000.00,
                'is_active': True
            }
        )

        self.stdout.write(self.style.SUCCESS("[OK] Servicios demo creados."))

        # 6. Availability TimeSlots for Carlos Mendoza
        today = timezone.now().date()
        for day_offset in range(1, 4):
            slot_date = today + datetime.timedelta(days=day_offset)
            start_times = [datetime.time(9, 0), datetime.time(9, 20), datetime.time(9, 40), datetime.time(10, 0), datetime.time(11, 0), datetime.time(15, 0)]
            for st in start_times:
                et = (datetime.datetime.combine(slot_date, st) + datetime.timedelta(minutes=20)).time()
                TimeSlot.objects.get_or_create(
                    professional=pro_user,
                    date=slot_date,
                    start_time=st,
                    defaults={'end_time': et, 'status': TimeSlot.STATUS_DISPONIBLE}
                )

        self.stdout.write(self.style.SUCCESS("[OK] Bloques de disponibilidad de 20 minutos creados."))
        self.stdout.write(self.style.SUCCESS("--------------------------------------------------"))
        self.stdout.write(self.style.SUCCESS("Sembrado de datos en Skilly completado con exito!"))
        self.stdout.write(self.style.SUCCESS("Credenciales Demo:"))
        self.stdout.write(self.style.SUCCESS("  - ADMIN:         admin / admin123 (Ruta: /backoffice/)"))
        self.stdout.write(self.style.SUCCESS("  - PROFESIONAL:   carlos_pro / pro123 (Perfil: /pro/carlos-dev)"))
        self.stdout.write(self.style.SUCCESS("  - ORGANIZACION:  tech_corp / org123"))
        self.stdout.write(self.style.SUCCESS("--------------------------------------------------"))
