from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime
from users.models import CustomUser, ProfessionalProfile, OrganizationProfile
from services.models import Category, Service
from availability.models import TimeSlot
from reviews.models import Badge
from benefits.models import Benefit

class Command(BaseCommand):
    help = "Siembra la base de datos con un catálogo completo de profesionales, servicios, categorías, insignias y disponibilidad."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Iniciando sembrado masivo de datos para Skilly Marketplace..."))

        # -. 1. Categorías
        categories_data = [
            {
                'slug': 'desarrollo-software',
                'name': 'Desarrollo Software',
                'description': 'Desarrollo web, móvil, APIs REST y arquitecturas backend escalables.',
                'icon': 'fa-code'
            },
            {
                'slug': 'diseno-ux',
                'name': 'Diseño & UX/UI',
                'description': 'Sistemas de diseño, prototipado interactivo e interfaces de alto impacto.',
                'icon': 'fa-paint-brush'
            },
            {
                'slug': 'ciberseguridad-devsecops',
                'name': 'Ciberseguridad & DevSecOps',
                'description': 'Pentesting, auditoría de vulnerabilidades, CI/CD y despliegue en la nube.',
                'icon': 'fa-shield-halved'
            },
            {
                'slug': 'ia-data-science',
                'name': 'IA & Data Science',
                'description': 'Integración de LLMs, agentes IA, RAG y analítica predictiva de datos.',
                'icon': 'fa-brain'
            },
            {
                'slug': 'consultoria-legal',
                'name': 'Consultoría Legal',
                'description': 'Asesoría jurídica corporativa, contratos IT, términos y protección de datos.',
                'icon': 'fa-scale-balanced'
            },
            {
                'slug': 'marketing-digital',
                'name': 'Marketing Digital',
                'description': 'Growth marketing, SEO técnico, estrategia de contenidos y performance.',
                'icon': 'fa-bullhorn'
            },
            {
                'slug': 'finanzas-contabilidad',
                'name': 'Finanzas & Tributaria',
                'description': 'Modelamiento financiero para startups, valoración y planificación tributaria.',
                'icon': 'fa-chart-pie'
            },
            {
                'slug': 'product-agile',
                'name': 'Product & Agile',
                'description': 'Product Management, agile coaching, roadmaps y discovery de productos.',
                'icon': 'fa-diagram-project'
            },
        ]

        categories_map = {}
        for cdata in categories_data:
            cat, _ = Category.objects.get_or_create(
                slug=cdata['slug'],
                defaults={
                    'name': cdata['name'],
                    'description': cdata['description'],
                    'icon': cdata['icon']
                }
            )
            categories_map[cdata['slug']] = cat

        self.stdout.write(self.style.SUCCESS(f"[OK] {len(categories_map)} categorías verificadas."))

        # -. 2. Insignias
        badges_data = [
            ("Entrega a tiempo", "fa-clock", "Cumplimiento puntual de plazos pactados"),
            ("Comunicación fluida", "fa-comments", "Excelente claridad y respuesta rápida"),
            ("Resolutivo", "fa-bolt", "Capacidad de resolver problemas técnicos complejos"),
            ("Excelente calidad", "fa-star", "Superó las expectativas técnica y visualmente"),
            ("Dominio técnico alto", "fa-laptop-code", "Demostró amplio conocimiento senior"),
            ("Especialista Cloud", "fa-cloud", "Dominio experto de AWS, GCP y arquitecturas Cloud"),
            ("Clean Code", "fa-feather", "Código limpio, mantenible y altamente documentado"),
        ]
        for name, icon, desc in badges_data:
            Badge.objects.get_or_create(name=name, defaults={'icon': icon, 'description': desc})

        self.stdout.write(self.style.SUCCESS("[OK] Insignias cualitativas preparadas."))

        # -. 3. Beneficios
        benefits_data = [
            ("Seguro de Salud Freelance - Coopeuch", "Coopeuch Seguros", "Seguros & Salud", "Cobertura de salud complementaria y urgencias para independientes con tarifa preferencial.", "https://coopeuch.cl", "Membresía Activa"),
            ("Platzi Enterprise 30% OFF", "Platzi", "Formación & Cursos", "Acceso con descuento exclusivo a rutas de aprendizaje en tecnología y liderazgo.", "https://platzi.com", "Descuento Exclusivo"),
            ("AWS Cloud Credits ($1,000 USD)", "Amazon Web Services", "Herramientas Cloud", "Créditos promocionales para infraestructura cloud en proyectos de clientes Skilly.", "https://aws.amazon.com", "Beneficio Premium"),
            ("Firma Digital Avanzada - E-Sign", "E-Sign Chile", "Herramientas Legales", "50% de descuento en certificado de firma digital avanzada para contratos de prestación de servicios.", "https://e-sign.cl", "Convenio Pro"),
        ]
        for title, provider, category, desc, url, badge in benefits_data:
            Benefit.objects.get_or_create(title=title, defaults={
                'provider': provider,
                'category': category,
                'description': desc,
                'activation_url': url,
                'badge_text': badge
            })

        self.stdout.write(self.style.SUCCESS("[OK] Beneficios configurados."))

        # -. 4. Usuarios base; configura manualmente la contraseña del admin en producción.
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
            import secrets
            admin_user.set_password(secrets.token_urlsafe(24))
            admin_user.save()
            self.stdout.write(self.style.WARNING(
                "IMPORTANTE: El usuario 'admin' fue creado con una contraseña aleatoria. "
                "Cambia la contraseña con: python manage.py changepassword admin"
            ))

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
            import secrets
            org_user.set_password(secrets.token_urlsafe(24))
            org_user.save()
            OrganizationProfile.objects.get_or_create(
                user=org_user,
                defaults={
                    'company_name': 'TechCorp SpA',
                    'tax_id': '77.654.321-9',
                    'description': 'Empresa referente en innovación tecnológica y aceleración de productos digitales.'
                }
            )

        # -. 5. Profesionales y servicios
        professionals_data = [
            {
                'username': 'carlos_pro',
                'email': 'carlos@skilly.com',
                'first_name': 'Carlos',
                'last_name': 'Mendoza',
                'phone': '+56 9 8765 4321',
                'profession': 'Senior Full Stack & Python Architect',
                'bio': 'Más de 8 años de experiencia diseñando e implementando arquitecturas limpias, Django 5+, PostgreSQL y entornos cloud de alta disponibilidad.',
                'hourly_rate': 60000.00,
                'slug': 'carlos-dev',
                'services': [
                    {
                        'title': 'Desarrollo MVP Backend Django 5 & APIs REST',
                        'category_slug': 'desarrollo-software',
                        'description': 'Construcción modular completa de arquitectura backend con Django 5, PostgreSQL y seguridad robusta.',
                        'deliverables': '- Código fuente completo con Clean Architecture\n- APIs REST documentadas con OpenAPI/Swagger\n- Panel de administración Django configurado\n- Scripts de despliegue Docker & Dokku',
                        'estimated_duration': '3 días hábiles',
                        'price': 350000.00
                    },
                    {
                        'title': 'Auditoría de Código, Rendimiento y Seguridad Python',
                        'category_slug': 'desarrollo-software',
                        'description': 'Revisión exhaustiva de código existente, detección de bottlenecks de rendimiento y optimización de consultas ORM.',
                        'deliverables': '- Informe detallado de vulnerabilidades y cuellos de botella\n- Propuesta de refactorización y parches de código\n- Sesión de asesoría técnica de 1 hora',
                        'estimated_duration': '1 día hábil',
                        'price': 180000.00
                    }
                ]
            },
            {
                'username': 'valentina_pro',
                'email': 'valentina@skilly.com',
                'first_name': 'Valentina',
                'last_name': 'Ríos',
                'phone': '+56 9 9123 4567',
                'profession': 'Lead UX/UI Designer & Design Systems Specialist',
                'bio': 'Diseñadora de productos digitales con especialización en Design Systems escalables en Figma y optimización de conversion rate para SaaS y e-Commerce.',
                'hourly_rate': 55000.00,
                'slug': 'valentina-ux',
                'services': [
                    {
                        'title': 'Auditoría UX/UI y Heurística de Producto Digital',
                        'category_slug': 'diseno-ux',
                        'description': 'Evaluación completa de la usabilidad de tu plataforma, detección de fricciones en la navegación y propuesta de mejoras visuales.',
                        'deliverables': '- Reporte de auditoría heurística con capturas y diagnósticos\n- Wireframes de propuesta de rediseño de pantallas clave\n- Video walkthrough explicativo de 15 minutos',
                        'estimated_duration': '2 días hábiles',
                        'price': 140000.00
                    },
                    {
                        'title': 'Diseño de UI Design System Modular en Figma',
                        'category_slug': 'diseno-ux',
                        'description': 'Creación de un sistema de diseño profesional con componentes reutilizables, variantes, auto-layout y guía de tokens tipográficos y cromáticos.',
                        'deliverables': '- Archivo Figma estructurado con tokens de color y tipografía\n- Componentes interactivos (botones, inputs, modales, cards)\n- Documentación de uso para el equipo de desarrollo',
                        'estimated_duration': '4 días hábiles',
                        'price': 380000.00
                    },
                    {
                        'title': 'Rediseño de Flujo de Checkout & Onboarding Conversión',
                        'category_slug': 'diseno-ux',
                        'description': 'Optimización del embudo de conversión enfocado en reducir la tasa de abandono y mejorar la retención de usuarios.',
                        'deliverables': '- Prototipo navegable de alta fidelidad en Figma\n- Test de usabilidad sintético y recomendaciones UX\n- Especificaciones técnicas para implementación frontend',
                        'estimated_duration': '3 días hábiles',
                        'price': 220000.00
                    }
                ]
            },
            {
                'username': 'matias_pro',
                'email': 'matias@skilly.com',
                'first_name': 'Matías',
                'last_name': 'Loyola',
                'phone': '+56 9 7788 9900',
                'profession': 'AI Engineer & Machine Learning Specialist',
                'bio': 'Especialista en desarrollo de asistentes inteligentes con LangChain, LlamaIndex, OpenAI API y fine-tuning de modelos para empresas.',
                'hourly_rate': 75000.00,
                'slug': 'matias-ai',
                'services': [
                    {
                        'title': 'Integración de Agentes IA & RAG sobre Documentos Internos',
                        'category_slug': 'ia-data-science',
                        'description': 'Implementación de un motor de búsqueda y respuestas inteligentes (RAG) conectado a la base de conocimiento o PDFs de tu empresa.',
                        'deliverables': '- Pipeline de ingestión y embedding vectorial en Pinecone/ChromaDB\n- Endpoint API listo para integración frontend\n- Consola de pruebas y ajustes de prompt engineering',
                        'estimated_duration': '4 días hábiles',
                        'price': 480000.00
                    },
                    {
                        'title': 'Consultoría y Proof of Concept (PoC) de Inteligencia Artificial',
                        'category_slug': 'ia-data-science',
                        'description': 'Sesión estratégica y prototipo rápido para validar si una solución de IA o LLM aporta valor real a tu negocio.',
                        'deliverables': '- Prototipo funcional en Python/Streamlit\n- Estimación de costos operativos de tokens de API\n- Hoja de ruta técnica para producción',
                        'estimated_duration': '2 días hábiles',
                        'price': 250000.00
                    }
                ]
            },
            {
                'username': 'camila_pro',
                'email': 'camila@skilly.com',
                'first_name': 'Camila',
                'last_name': 'Morales',
                'phone': '+56 9 5544 3322',
                'profession': 'Especialista en Ciberseguridad & Ethical Hacking',
                'bio': 'Consultora en ciberseguridad con experiencia en pruebas de penetración web, análisis de vulnerabilidades y seguridad para la Ley de Protección de Datos.',
                'hourly_rate': 70000.00,
                'slug': 'camila-sec',
                'services': [
                    {
                        'title': 'Pentesting Web & Auditoría OWASP Top 10',
                        'category_slug': 'ciberseguridad-devsecops',
                        'description': 'Evaluación de seguridad cibernética en aplicaciones web para identificar brechas de SQLi, XSS, autenticación y fallas de autorización.',
                        'deliverables': '- Informe ejecutivo y técnico de vulnerabilidades clasificadas por riesgo (CVSS)\n- Guía paso a paso para remediación de hallazgos\n- Re-test de verificación posterior al parcheo',
                        'estimated_duration': '3 días hábiles',
                        'price': 320000.00
                    },
                    {
                        'title': 'Hardening y Configuración Segura de Servidores Cloud',
                        'category_slug': 'ciberseguridad-devsecops',
                        'description': 'Bastionado de instancias Linux, firewalls UFW/Security Groups, políticas IAM y encriptación de datos en reposo y tránsito.',
                        'deliverables': '- Servidor configurado con estándares CIS Benchmarks\n- Auditoría de puertos y accesos SSH con llaves\n- Checklist de buenas prácticas de infraestructura',
                        'estimated_duration': '1 día hábil',
                        'price': 190000.00
                    }
                ]
            },
            {
                'username': 'sebastian_pro',
                'email': 'sebastian@skilly.com',
                'first_name': 'Sebastián',
                'last_name': 'Arancibia',
                'phone': '+56 9 3322 1100',
                'profession': 'DevSecOps Engineer & Cloud Architect (AWS/GCP)',
                'bio': 'Arquitecto cloud certificado en AWS. Experto en Docker, Kubernetes, Terraform y automatización de despliegues continuos con cero downtime.',
                'hourly_rate': 65000.00,
                'slug': 'sebastian-cloud',
                'services': [
                    {
                        'title': 'Implementación de Pipeline CI/CD Seguro & Infrastructure as Code',
                        'category_slug': 'ciberseguridad-devsecops',
                        'description': 'Automatización completa del ciclo de compilación, testing, análisis estático y despliegue a producción usando GitHub Actions y Terraform.',
                        'deliverables': '- Workflow de GitHub Actions optimizado\n- Scripts de Terraform para infraestructura reproducible\n- Documentación de procedimientos de rollback',
                        'estimated_duration': '3 días hábiles',
                        'price': 390000.00
                    }
                ]
            },
            {
                'username': 'javier_pro',
                'email': 'javier@skilly.com',
                'first_name': 'Javier',
                'last_name': 'Undurraga',
                'phone': '+56 9 4455 6677',
                'profession': 'Abogado Corporativo & Especialista en Derecho Tecnológico',
                'bio': 'Abogado con más de 10 años asesorando a startups, empresas de software y fintechs en propiedad intelectual, regulación de datos y pactos accionarios.',
                'hourly_rate': 60000.00,
                'slug': 'javier-legal',
                'services': [
                    {
                        'title': 'Redacción de Términos, Condiciones y Políticas de Privacidad',
                        'category_slug': 'consultoria-legal',
                        'description': 'Elaboración de marco legal a medida para plataformas web o aplicaciones móviles alineado con la Ley de Protección de Datos Personales de Chile.',
                        'deliverables': '- Documentos legales listos para publicar en el sitio web\n- Cláusulas de deslinde de responsabilidad y propiedad intelectual\n- Sesión de revisión legal de 45 minutos',
                        'estimated_duration': '2 días hábiles',
                        'price': 160000.00
                    },
                    {
                        'title': 'Asesoría y Redacción de Pacto de Accionistas para Startups',
                        'category_slug': 'consultoria-legal',
                        'description': 'Estructuración jurídica de relaciones entre socios fundadores, vesting de acciones, cláusulas de drag-along / tag-along y confidencialidad.',
                        'deliverables': '- Borrador de Pacto de Accionistas a medida\n- Minuta explicativa para firmas en notaría\n- Asesoría directa en sesión de alineación',
                        'estimated_duration': '3 días hábiles',
                        'price': 290000.00
                    }
                ]
            },
            {
                'username': 'francisca_pro',
                'email': 'francisca@skilly.com',
                'first_name': 'Francisca',
                'last_name': 'Navarrete',
                'phone': '+56 9 6677 8899',
                'profession': 'Growth Marketing Lead & SEO Strategist',
                'bio': 'Consultora de crecimiento digital especializada en captación B2B, estrategias SEO omnicanal y optimización de presupuestos publicitarios.',
                'hourly_rate': 50000.00,
                'slug': 'francisca-mkt',
                'services': [
                    {
                        'title': 'Auditoría SEO Técnico & Estrategia de Posicionamiento Orgánico',
                        'category_slug': 'marketing-digital',
                        'description': 'Análisis profundo de indexación, palabras clave con intención de compra, velocidad de carga y arquitectura de contenidos.',
                        'deliverables': '- Reporte SEO técnico con hallazgos priorizados\n- Plan de contenidos estratégico para 3 meses\n- Lista de backlinks y oportunidades de authority building',
                        'estimated_duration': '2 días hábiles',
                        'price': 170000.00
                    },
                    {
                        'title': 'Estrategia & Configuración de Campañas Google Ads & Meta Ads',
                        'category_slug': 'marketing-digital',
                        'description': 'Diseño e implementación de campañas orientadas a la conversión directa con píxeles de seguimiento y atribución de eventos configurada.',
                        'deliverables': '- Configuración de la estructura de campaña en Google/Meta\n- Redacción de copys publicitarios y segmentación de audiencias\n- Dashboard sintético de métricas clave (ROAS, CAC, CPL)',
                        'estimated_duration': '2 días hábiles',
                        'price': 230000.00
                    }
                ]
            },
            {
                'username': 'rodrigo_pro',
                'email': 'rodrigo@skilly.com',
                'first_name': 'Rodrigo',
                'last_name': 'Sepúlveda',
                'phone': '+56 9 8899 0011',
                'profession': 'Agile Coach & Senior Product Manager',
                'bio': 'Coach ágil y estratega de producto con trayectoria en la transformación digital de equipos multidisciplinarios y adopción de Scrum/Kanban.',
                'hourly_rate': 58000.00,
                'slug': 'rodrigo-agile',
                'services': [
                    {
                        'title': 'Workshop de Product Discovery & User Story Mapping',
                        'category_slug': 'product-agile',
                        'description': 'Facilitación de taller para definir la propuesta de valor, priorizar el backlog del producto y mapear las historias de usuario clave.',
                        'deliverables': '- Tablero Miro/Jira estructurado con User Story Map\n- Backlog priorizado listo para desarrollo por sprints\n- Hoja de ruta (Roadmap) de entregas para los próximos 6 meses',
                        'estimated_duration': '2 días hábiles',
                        'price': 210000.00
                    }
                ]
            }
        ]

        total_services_created = 0
        today = timezone.now().date()

        for pdata in professionals_data:
            user, u_created = CustomUser.objects.get_or_create(
                username=pdata['username'],
                defaults={
                    'email': pdata['email'],
                    'first_name': pdata['first_name'],
                    'last_name': pdata['last_name'],
                    'phone': pdata['phone'],
                    'role': CustomUser.ROLE_PROFESIONAL
                }
            )
            if u_created:
                import secrets
                user.set_password(secrets.token_urlsafe(24))
                user.save()

            profile, _ = ProfessionalProfile.objects.get_or_create(
                user=user,
                defaults={
                    'profession': pdata['profession'],
                    'bio': pdata['bio'],
                    'validation_status': ProfessionalProfile.STATUS_VALIDADO,
                    'slug': pdata['slug'],
                    'hourly_rate': pdata['hourly_rate'],
                    'admin_notes': ''
                }
            )
            # -. Los valores por defecto de get_or_create no actualizan perfiles existentes.
            if profile.validation_status != ProfessionalProfile.STATUS_VALIDADO:
                profile.validation_status = ProfessionalProfile.STATUS_VALIDADO
                profile.save()

            for sdata in pdata['services']:
                cat = categories_map[sdata['category_slug']]
                svc, created_svc = Service.objects.get_or_create(
                    professional=user,
                    title=sdata['title'],
                    defaults={
                        'category': cat,
                        'description': sdata['description'],
                        'deliverables': sdata['deliverables'],
                        'estimated_duration': sdata['estimated_duration'],
                        'price': sdata['price'],
                        'is_active': True,
                        'status': getattr(Service, 'STATUS_PUBLICADO', 'PUBLICADO'),
                        'modified_by_admin': False
                    }
                )
                if not created_svc:
                    svc.status = getattr(Service, 'STATUS_PUBLICADO', 'PUBLICADO')
                    svc.is_active = True
                    svc.save()
                total_services_created += 1

            for day_offset in range(1, 8):
                slot_date = today + datetime.timedelta(days=day_offset)
                # -. No se programan servicios los domingos.
                if slot_date.weekday() == 6:
                    continue
                start_times = [
                    datetime.time(9, 0), datetime.time(9, 30), datetime.time(10, 0),
                    datetime.time(11, 30), datetime.time(15, 0), datetime.time(16, 30)
                ]
                for st in start_times:
                    et = (datetime.datetime.combine(slot_date, st) + datetime.timedelta(minutes=20)).time()
                    TimeSlot.objects.get_or_create(
                        professional=user,
                        date=slot_date,
                        start_time=st,
                        defaults={'end_time': et, 'status': TimeSlot.STATUS_DISPONIBLE}
                    )

        self.stdout.write(self.style.SUCCESS(f"[OK] {len(professionals_data)} profesionales validados y {total_services_created} servicios sembrados."))
        self.stdout.write(self.style.SUCCESS("[OK] Bloques de disponibilidad actualizados para los próximos 7 días."))
        self.stdout.write(self.style.SUCCESS("--------------------------------------------------"))
        self.stdout.write(self.style.SUCCESS("¡Marketplace de Skilly poblado con éxito!"))
        self.stdout.write(self.style.WARNING(
            "RECUERDA: Todos los usuarios del seed tienen contraseñas aleatorias. "
            "Cambia las contraseñas antes de usar en producción: "
            "python manage.py changepassword <username>"
        ))
        self.stdout.write(self.style.SUCCESS("--------------------------------------------------"))
