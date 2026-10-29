# -- VISTAS COMPLETAS DEL BACK-OFFICE DE ADMINISTRACIÓN Y CONTROL GLOBAL --
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from users.models import CustomUser, ProfessionalProfile, OrganizationProfile, StrikeRecord
from bookings.models import Booking
from escrow_payments.models import PaymentTransaction
from disputes.models import Dispute
from reviews.models import Review, Badge
from services.models import Service, Category
from benefits.models import Benefit
from .models import PlatformSetting, ValidationMessage
from .forms import (
    StrikeForm, AdminProNotesForm, ServiceModerationForm, BenefitForm,
    CategoryForm, BadgeForm, TakeRateForm, ValidationMessageForm
)


def admin_required(view_func):
    """Decorador de seguridad para validar rol de administrador Skilly."""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin_role:
            messages.error(request, "Acceso restringido al Back-Office de Skilly.")
            return redirect('services:marketplace')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ==============================================================================
# 1. DASHBOARD PRINCIPAL & CENTRO DE COMANDO
# ==============================================================================

@login_required
@admin_required
def admin_dashboard_view(request):
    """Panel general con métricas ejecutivas, alertas en tiempo real y accesos rápidos."""
    # Métricas financieras
    total_volume = PaymentTransaction.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_held = PaymentTransaction.objects.filter(escrow_status=PaymentTransaction.STATUS_RETENIDO).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_fees = PaymentTransaction.objects.aggregate(Sum('skilly_fee_amount'))['skilly_fee_amount__sum'] or 0

    # Contadores de usuarios
    total_users_count = CustomUser.objects.count()
    pros_count = CustomUser.objects.filter(role=CustomUser.ROLE_PROFESIONAL).count()
    orgs_count = CustomUser.objects.filter(role=CustomUser.ROLE_ORGANIZACION).count()

    # Contadores de servicios
    total_services_count = Service.objects.count()
    active_services_count = Service.objects.filter(is_active=True).count()
    pending_services_count = Service.objects.filter(status=Service.STATUS_EN_REVISION).count()

    # Contadores de reservas y supervisión
    total_bookings_count = Booking.objects.count()
    active_bookings_count = Booking.objects.filter(
        status__in=[Booking.STATUS_PAGADO_EN_CUSTODIA, Booking.STATUS_EN_EJECUCION]
    ).count()
    supervision_requested_count = Booking.objects.filter(
        skilly_staff_supervision_requested=True
    ).exclude(status__in=[Booking.STATUS_FINALIZADO, Booking.STATUS_CANCELADO]).count()

    # Alertas operativas
    pending_validations_count = ProfessionalProfile.objects.filter(validation_status=ProfessionalProfile.STATUS_PENDIENTE).count()
    open_disputes_count = Dispute.objects.filter(status=Dispute.STATUS_ABIERTA).count()

    # Feeds recientes
    recent_transactions = PaymentTransaction.objects.select_related('booking', 'booking__service', 'booking__organization').order_by('-created_at')[:6]
    recent_disputes = Dispute.objects.filter(status=Dispute.STATUS_ABIERTA).select_related('booking', 'reported_by')[:5]
    recent_validations = ProfessionalProfile.objects.filter(validation_status=ProfessionalProfile.STATUS_PENDIENTE).select_related('user')[:5]
    recent_services_to_review = Service.objects.filter(status=Service.STATUS_EN_REVISION).select_related('professional', 'category')[:5]
    recent_supervision_bookings = Booking.objects.filter(
        skilly_staff_supervision_requested=True
    ).exclude(status__in=[Booking.STATUS_FINALIZADO, Booking.STATUS_CANCELADO]).select_related('service', 'professional', 'organization')[:5]

    # Configuración de Take Rate de Skilly
    current_take_rate = PlatformSetting.get_take_rate()
    take_rate_form = TakeRateForm(instance=PlatformSetting.get_instance())

    context = {
        'total_volume': total_volume,
        'total_held': total_held,
        'total_fees': total_fees,
        'total_users_count': total_users_count,
        'pros_count': pros_count,
        'orgs_count': orgs_count,
        'total_services_count': total_services_count,
        'active_services_count': active_services_count,
        'pending_services_count': pending_services_count,
        'total_bookings_count': total_bookings_count,
        'active_bookings_count': active_bookings_count,
        'supervision_requested_count': supervision_requested_count,
        'pending_validations_count': pending_validations_count,
        'open_disputes_count': open_disputes_count,
        'recent_transactions': recent_transactions,
        'recent_disputes': recent_disputes,
        'recent_validations': recent_validations,
        'recent_services_to_review': recent_services_to_review,
        'recent_supervision_bookings': recent_supervision_bookings,
        'current_take_rate': current_take_rate,
        'take_rate_form': take_rate_form,
    }
    return render(request, 'backoffice/panel_administracion.html', context)


@login_required
@admin_required
def update_take_rate_action(request):
    """Actualiza el porcentaje global de Take Rate (comisión) de Skilly."""
    if request.method == 'POST':
        setting = PlatformSetting.get_instance()
        form = TakeRateForm(request.POST, instance=setting)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.updated_by = request.user
            rate.save()
            messages.success(request, f"¡Take Rate de Skilly actualizado exitosamente al {rate.take_rate_percentage}%!")
        else:
            messages.error(request, "Error al actualizar el Take Rate. Ingrese un valor válido entre 0% y 100%.")
    return redirect('backoffice:dashboard')


# ==============================================================================
# 2. GESTIÓN INTEGRAL DE USUARIOS, PERFILES Y SANCIONES (STRIKES)
# ==============================================================================

@login_required
@admin_required
def users_management_view(request):
    """Directorio y control de todos los usuarios de la plataforma."""
    role_filter = request.GET.get('role', 'ALL')
    status_filter = request.GET.get('status', 'ALL')
    search_query = request.GET.get('q', '').strip()

    users = CustomUser.objects.all().select_related('professional_profile', 'organization_profile').order_by('-date_joined')

    if role_filter == 'PROFESIONAL':
        users = users.filter(role=CustomUser.ROLE_PROFESIONAL)
    elif role_filter == 'ORGANIZACION':
        users = users.filter(role=CustomUser.ROLE_ORGANIZACION)
    elif role_filter == 'ADMIN':
        users = users.filter(Q(role=CustomUser.ROLE_ADMIN) | Q(is_superuser=True))

    if status_filter == 'ACTIVE':
        users = users.filter(is_active=True)
    elif status_filter == 'INACTIVE':
        users = users.filter(is_active=False)
    elif status_filter == 'EXPELLED':
        users = users.filter(professional_profile__expelled_at__isnull=False)
    elif status_filter == 'STRIKES':
        users = users.filter(professional_profile__strikes_count__gt=0)

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(professional_profile__profession__icontains=search_query) |
            Q(organization_profile__company_name__icontains=search_query)
        )

    # Conteo por rol para las pestañas
    all_count = CustomUser.objects.count()
    pros_count = CustomUser.objects.filter(role=CustomUser.ROLE_PROFESIONAL).count()
    orgs_count = CustomUser.objects.filter(role=CustomUser.ROLE_ORGANIZACION).count()
    admins_count = CustomUser.objects.filter(Q(role=CustomUser.ROLE_ADMIN) | Q(is_superuser=True)).count()

    context = {
        'users_list': users,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'all_count': all_count,
        'pros_count': pros_count,
        'orgs_count': orgs_count,
        'admins_count': admins_count,
    }
    return render(request, 'backoffice/gestion_usuarios.html', context)


@login_required
@admin_required
def user_detail_view(request, user_id):
    """Vista 360° del usuario: reservas, transacciones, notas internas y amonestaciones."""
    target_user = get_object_or_404(CustomUser, pk=user_id)
    pro_profile = getattr(target_user, 'professional_profile', None)
    org_profile = getattr(target_user, 'organization_profile', None)

    strike_form = StrikeForm()
    admin_notes_form = AdminProNotesForm(instance=pro_profile) if pro_profile else None

    # Métricas y registros específicos
    if target_user.is_professional:
        user_bookings = target_user.received_bookings.all().select_related('service', 'organization').order_by('-created_at')
        user_services = target_user.services.all().order_by('-created_at')
        strike_records = pro_profile.strike_records.all().select_related('applied_by').order_by('-created_at') if pro_profile else []
        reviews = target_user.received_reviews.all().select_related('organization', 'booking').prefetch_related('badges').order_by('-created_at')
        total_earned = PaymentTransaction.objects.filter(
            booking__professional=target_user,
            escrow_status=PaymentTransaction.STATUS_LIBERADO
        ).aggregate(Sum('net_professional_amount'))['net_professional_amount__sum'] or 0
    else:
        user_bookings = target_user.sent_bookings.all().select_related('service', 'professional').order_by('-created_at')
        user_services = []
        strike_records = []
        reviews = target_user.submitted_reviews.all().select_related('professional', 'booking').order_by('-created_at')
        total_earned = PaymentTransaction.objects.filter(
            booking__organization=target_user,
            escrow_status__in=[PaymentTransaction.STATUS_LIBERADO, PaymentTransaction.STATUS_RETENIDO]
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    context = {
        'target_user': target_user,
        'pro_profile': pro_profile,
        'org_profile': org_profile,
        'user_bookings': user_bookings,
        'user_services': user_services,
        'strike_records': strike_records,
        'reviews': reviews,
        'total_financial_flow': total_earned,
        'strike_form': strike_form,
        'admin_notes_form': admin_notes_form,
    }
    return render(request, 'backoffice/detalle_usuario.html', context)


@login_required
@admin_required
def toggle_user_status(request, user_id):
    """Activa o desactiva la cuenta de un usuario."""
    target_user = get_object_or_404(CustomUser, pk=user_id)
    if target_user == request.user:
        messages.error(request, "No puedes desactivar tu propia cuenta de administrador.")
        return redirect('backoffice:user_detail', user_id=user_id)

    target_user.is_active = not target_user.is_active
    target_user.save()
    status_label = "activada" if target_user.is_active else "desactivada"
    messages.success(request, f"La cuenta de {target_user.get_full_name() or target_user.username} ha sido {status_label}.")
    return redirect('backoffice:user_detail', user_id=user_id)


@login_required
@admin_required
def apply_strike_action(request, user_id):
    """Aplica una amonestación formal (Strike) a un profesional."""
    target_user = get_object_or_404(CustomUser, pk=user_id)
    pro_profile = getattr(target_user, 'professional_profile', None)

    if not pro_profile:
        messages.error(request, "Solo los profesionales pueden recibir amonestaciones.")
        return redirect('backoffice:user_detail', user_id=user_id)

    if request.method == 'POST':
        form = StrikeForm(request.POST)
        if form.is_valid():
            strike = form.save(commit=False)
            strike.professional = pro_profile
            strike.applied_by = request.user
            strike.save()

            pro_profile.strikes_count = pro_profile.strike_records.filter(is_active=True).count()
            if pro_profile.strikes_count >= 3 and not pro_profile.expelled_at:
                pro_profile.expelled_at = timezone.now()
                messages.warning(request, f"El profesional acumuló {pro_profile.strikes_count} strikes y ha sido marcado como EXPULSADO preventivamente.")
            pro_profile.save()

            messages.success(request, f"Amonestación registrada correctamente. Total strikes activos: {pro_profile.strikes_count}.")

    return redirect('backoffice:user_detail', user_id=user_id)


@login_required
@admin_required
def revoke_strike_action(request, strike_id):
    """Anula o desactiva una amonestación aplicada a un profesional."""
    strike = get_object_or_404(StrikeRecord, pk=strike_id)
    pro_profile = strike.professional
    user_id = pro_profile.user.id

    strike.is_active = False
    strike.save()

    pro_profile.strikes_count = pro_profile.strike_records.filter(is_active=True).count()
    if pro_profile.strikes_count < 3 and pro_profile.expelled_at:
        pro_profile.expelled_at = None
    pro_profile.save()

    messages.info(request, f"Amonestación desactivada. Nuevo conteo de strikes activos: {pro_profile.strikes_count}.")
    return redirect('backoffice:user_detail', user_id=user_id)


@login_required
@admin_required
def update_admin_notes_action(request, user_id):
    """Guarda las notas internas y confidenciales del equipo Skilly para este usuario."""
    target_user = get_object_or_404(CustomUser, pk=user_id)
    pro_profile = getattr(target_user, 'professional_profile', None)

    if pro_profile and request.method == 'POST':
        form = AdminProNotesForm(request.POST, instance=pro_profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Notas internas de administración guardadas.")

    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('backoffice:user_detail', user_id=user_id)


@login_required
@admin_required
def toggle_pro_expulsion(request, user_id):
    """Marca o desmarca la expulsión de un profesional del marketplace."""
    target_user = get_object_or_404(CustomUser, pk=user_id)
    pro_profile = getattr(target_user, 'professional_profile', None)

    if pro_profile:
        if pro_profile.expelled_at:
            pro_profile.expelled_at = None
            messages.success(request, f"Se ha levantado la expulsión de {target_user.get_full_name() or target_user.username}.")
        else:
            pro_profile.expelled_at = timezone.now()
            messages.warning(request, f"El profesional {target_user.get_full_name() or target_user.username} ha sido EXPULSADO de Skilly.")
        pro_profile.save()

    return redirect('backoffice:user_detail', user_id=user_id)


# ==============================================================================
# 3. MESA DE MODERACIÓN Y CONTROL DE SERVICIOS
# ==============================================================================

@login_required
@admin_required
def services_moderation_view(request):
    """Listado y filtro de servicios para moderación de calidad y precios."""
    status_filter = request.GET.get('status', 'ALL')
    search_query = request.GET.get('q', '').strip()

    services = Service.objects.all().select_related('professional', 'category').order_by('-created_at')

    if status_filter != 'ALL':
        services = services.filter(status=status_filter)

    if search_query:
        services = services.filter(
            Q(title__icontains=search_query) |
            Q(professional__first_name__icontains=search_query) |
            Q(professional__last_name__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    # Conteo por estado para los badges
    counts = {
        'all': Service.objects.count(),
        'en_revision': Service.objects.filter(status=Service.STATUS_EN_REVISION).count(),
        'publicados': Service.objects.filter(status=Service.STATUS_PUBLICADO).count(),
        'modificados': Service.objects.filter(status=Service.STATUS_APROBADO_CON_MODIFICACIONES).count(),
        'rechazados': Service.objects.filter(status=Service.STATUS_RECHAZADO).count(),
    }

    context = {
        'services': services,
        'status_filter': status_filter,
        'search_query': search_query,
        'counts': counts,
    }
    return render(request, 'backoffice/moderacion_servicios.html', context)


@login_required
@admin_required
def service_moderation_action(request, pk):
    """Acción de moderación: Aprobar, Modificar, Rechazar o Cambiar estado de servicio."""
    service = get_object_or_404(Service, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        admin_feedback = request.POST.get('admin_feedback', '').strip()
        new_price = request.POST.get('price')

        if action == 'approve':
            service.status = Service.STATUS_PUBLICADO
            service.is_active = True
            service.admin_feedback = admin_feedback or "Servicio revisado y aprobado por el equipo de calidad Skilly."
            service.save()
            messages.success(request, f"Servicio '{service.title}' APROBADO y publicado en el marketplace.")

        elif action == 'approve_modified':
            if new_price:
                service.original_price = service.price
                service.price = new_price
            service.status = Service.STATUS_APROBADO_CON_MODIFICACIONES
            service.modified_by_admin = True
            service.is_active = True
            service.admin_feedback = admin_feedback or "Aprobado con ajuste de tarifa/términos por administración."
            service.save()
            messages.success(request, f"Servicio '{service.title}' Aprobado con Modificaciones.")

        elif action == 'reject':
            service.status = Service.STATUS_RECHAZADO
            service.is_active = False
            service.admin_feedback = admin_feedback or "No cumple con las pautas de calidad y alcance del marketplace."
            service.save()
            messages.warning(request, f"Servicio '{service.title}' RECHAZADO.")

        elif action == 'toggle_active':
            service.is_active = not service.is_active
            service.save()
            status_text = "activado" if service.is_active else "pausado"
            messages.info(request, f"Servicio '{service.title}' ha sido {status_text}.")

    return redirect('backoffice:services_moderation')


# ==============================================================================
# 4. MONITOREO DE RESERVAS Y SUPERVISIÓN DE SESIONES
# ==============================================================================

@login_required
@admin_required
def bookings_monitor_view(request):
    """Supervisión de reservas activas, solicitudes de staff Skilly e intervención."""
    status_filter = request.GET.get('status', 'ALL')
    supervision_only = request.GET.get('supervision') == '1'
    search_query = request.GET.get('q', '').strip()

    bookings = Booking.objects.all().select_related(
        'service', 'professional', 'organization', 'timeslot', 'payment_transaction'
    ).order_by('-created_at')

    if supervision_only:
        bookings = bookings.filter(skilly_staff_supervision_requested=True)

    if status_filter != 'ALL':
        bookings = bookings.filter(status=status_filter)

    if search_query:
        bookings = bookings.filter(
            Q(id__icontains=search_query) |
            Q(service__title__icontains=search_query) |
            Q(professional__first_name__icontains=search_query) |
            Q(professional__last_name__icontains=search_query) |
            Q(organization__first_name__icontains=search_query) |
            Q(organization__last_name__icontains=search_query)
        )

    # Contadores
    supervision_count = Booking.objects.filter(skilly_staff_supervision_requested=True).exclude(status__in=[Booking.STATUS_FINALIZADO, Booking.STATUS_CANCELADO]).count()
    in_escrow_count = Booking.objects.filter(status=Booking.STATUS_PAGADO_EN_CUSTODIA).count()
    in_execution_count = Booking.objects.filter(status=Booking.STATUS_EN_EJECUCION).count()

    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'supervision_only': supervision_only,
        'search_query': search_query,
        'supervision_count': supervision_count,
        'in_escrow_count': in_escrow_count,
        'in_execution_count': in_execution_count,
    }
    return render(request, 'backoffice/monitoreo_reservas.html', context)


@login_required
@admin_required
def booking_admin_action(request, pk):
    """Intervención administrativa de una reserva: forzar entrega, cancelación o supervisión."""
    booking = get_object_or_404(Booking, pk=pk)
    payment = getattr(booking, 'payment_transaction', None)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('admin_notes', '')

        if action == 'force_complete':
            booking.status = Booking.STATUS_FINALIZADO
            booking.completed_at = timezone.now()
            booking.save()
            if payment and payment.escrow_status == PaymentTransaction.STATUS_RETENIDO:
                payment.release_to_professional()
            messages.success(request, f"Reserva #{booking.id} finalizada administrativamente y fondos liberados al profesional.")

        elif action == 'force_cancel':
            booking.status = Booking.STATUS_CANCELADO
            booking.cancelled_at = timezone.now()
            booking.save()
            if payment and payment.escrow_status in [PaymentTransaction.STATUS_RETENIDO, PaymentTransaction.STATUS_CONGELADO]:
                payment.refund_to_organization()
            messages.warning(request, f"Reserva #{booking.id} cancelada administrativamente y fondos reembolsados a la organización.")

        elif action == 'toggle_supervision':
            booking.skilly_staff_supervision_requested = not booking.skilly_staff_supervision_requested
            booking.save()
            state = "activada" if booking.skilly_staff_supervision_requested else "retirada"
            messages.info(request, f"Supervisión Skilly {state} para la Reserva #{booking.id}.")

    return redirect('backoffice:bookings_monitor')


# ==============================================================================
# 5. MESA DE VALIDACIÓN DOCUMENTAL DE PROFESIONALES (MEJORADA)
# ==============================================================================

@login_required
@admin_required
def pro_validations_view(request):
    """Mesa de validación de documentos y acreditaciones profesionales."""
    pending_pros = ProfessionalProfile.objects.filter(
        validation_status=ProfessionalProfile.STATUS_PENDIENTE
    ).select_related('user').prefetch_related('validation_messages')
    
    validated_pros = ProfessionalProfile.objects.filter(
        validation_status=ProfessionalProfile.STATUS_VALIDADO
    ).select_related('user').prefetch_related('validation_messages')
    
    rejected_pros = ProfessionalProfile.objects.filter(
        validation_status=ProfessionalProfile.STATUS_RECHAZADO
    ).select_related('user').prefetch_related('validation_messages')

    context = {
        'pending_pros': pending_pros,
        'validated_pros': validated_pros,
        'rejected_pros': rejected_pros,
    }
    return render(request, 'backoffice/validaciones_profesionales.html', context)


@login_required
@admin_required
def validate_pro_action(request, pk, action):
    """Acción de aprobación, rechazo documental o reintegro a estado pendiente."""
    profile = get_object_or_404(ProfessionalProfile, pk=pk)

    if action == 'approve':
        profile.validation_status = ProfessionalProfile.STATUS_VALIDADO
        profile.rejection_reason = None
        profile.save()
        messages.success(request, f"Perfil del profesional {profile.user.get_full_name() or profile.user.username} ha sido VALIDADO.")

    elif action == 'reject' and request.method == 'POST':
        reason = request.POST.get('rejection_reason', 'Documentos no válidos o incompletos.')
        profile.validation_status = ProfessionalProfile.STATUS_RECHAZADO
        profile.rejection_reason = reason
        profile.save()
        messages.info(request, f"Perfil del profesional {profile.user.get_full_name() or profile.user.username} ha sido RECHAZADO.")

    elif action == 'pending':
        profile.validation_status = ProfessionalProfile.STATUS_PENDIENTE
        profile.save()
        messages.info(request, f"Perfil del profesional {profile.user.get_full_name() or profile.user.username} reabierto a PENDIENTE de revisión.")

    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('backoffice:validations')


@login_required
@admin_required
def validation_chat_view(request, pro_id):
    """Mesa de chat de validación y coordinación de reunión de bienvenida/entrevista con el profesional."""
    pro_profile = get_object_or_404(ProfessionalProfile, pk=pro_id)
    chat_messages = pro_profile.validation_messages.all().select_related('sender').order_by('created_at')
    scheduled_meeting = pro_profile.validation_messages.filter(meeting_scheduled_at__isnull=False).order_by('-created_at').first()

    if request.method == 'POST':
        form = ValidationMessageForm(request.POST, request.FILES)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.professional = pro_profile
            msg.sender = request.user
            msg.save()
            messages.success(request, f"Mensaje enviado a {pro_profile.user.get_full_name() or pro_profile.user.username}.")
            return redirect('backoffice:validation_chat', pro_id=pro_id)
        else:
            messages.error(request, "Error al enviar mensaje. Verifique los campos ingresados.")
    else:
        form = ValidationMessageForm()

    admin_notes_form = AdminProNotesForm(instance=pro_profile)

    context = {
        'pro_profile': pro_profile,
        'chat_messages': chat_messages,
        'scheduled_meeting': scheduled_meeting,
        'form': form,
        'admin_notes_form': admin_notes_form,
    }
    return render(request, 'backoffice/chat_validacion.html', context)


@login_required
def pro_own_validation_chat_view(request):
    """Acceso del profesional a su propio chat de validación y reunión con Skilly."""
    if not request.user.is_professional:
        messages.warning(request, "Acceso exclusivo para profesionales.")
        return redirect('services:marketplace')

    pro_profile = get_object_or_404(ProfessionalProfile, user=request.user)
    chat_messages = pro_profile.validation_messages.all().select_related('sender').order_by('created_at')
    scheduled_meeting = pro_profile.validation_messages.filter(meeting_scheduled_at__isnull=False).order_by('-created_at').first()

    if request.method == 'POST':
        form = ValidationMessageForm(request.POST, request.FILES)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.professional = pro_profile
            msg.sender = request.user
            msg.save()
            messages.success(request, "Mensaje enviado al equipo de administración Skilly.")
            return redirect('backoffice:pro_own_validation_chat')
        else:
            messages.error(request, "Error al enviar mensaje.")
    else:
        form = ValidationMessageForm()

    context = {
        'pro_profile': pro_profile,
        'chat_messages': chat_messages,
        'scheduled_meeting': scheduled_meeting,
        'form': form,
    }
    return render(request, 'backoffice/chat_validacion_pro.html', context)


# ==============================================================================
# 6. CENTRO DE MEDIACIÓN DE DISPUTAS Y ARBITRAJE
# ==============================================================================

@login_required
@admin_required
def disputes_list_view(request):
    """Listado de disputas y casos de controversia."""
    open_disputes = Dispute.objects.filter(status=Dispute.STATUS_ABIERTA).select_related('booking', 'reported_by')
    resolved_disputes = Dispute.objects.exclude(status=Dispute.STATUS_ABIERTA).select_related('booking', 'reported_by', 'resolved_by')

    context = {
        'open_disputes': open_disputes,
        'resolved_disputes': resolved_disputes,
    }
    return render(request, 'backoffice/lista_disputas.html', context)


@login_required
@admin_required
def dispute_detail_view(request, pk):
    """Detalle, análisis de evidencias y resolución arbitral de una disputa."""
    dispute = get_object_or_404(Dispute, pk=pk)
    booking = dispute.booking
    payment = getattr(booking, 'payment_transaction', None)
    chat_messages = booking.messages.all().select_related('sender')

    if request.method == 'POST':
        resolution_type = request.POST.get('resolution_type')
        notes = request.POST.get('resolution_notes', '')

        if resolution_type == 'RELEASE_PRO':
            dispute.status = Dispute.STATUS_RESUELTA_PROFESIONAL
            dispute.resolution_notes = notes
            dispute.resolved_by = request.user
            dispute.resolved_at = timezone.now()
            dispute.save()

            booking.status = Booking.STATUS_FINALIZADO
            booking.completed_at = timezone.now()
            booking.save()

            if payment:
                payment.release_to_professional()

            messages.success(request, "Disputa resuelta a favor del Profesional. Pago liberado.")

        elif resolution_type == 'REFUND_ORG':
            dispute.status = Dispute.STATUS_RESUELTA_ORGANIZACION
            dispute.resolution_notes = notes
            dispute.resolved_by = request.user
            dispute.resolved_at = timezone.now()
            dispute.save()

            booking.status = Booking.STATUS_CANCELADO
            booking.cancelled_at = timezone.now()
            booking.save()

            if payment:
                payment.refund_to_organization()

            messages.info(request, "Disputa resuelta a favor de la Organización. Pago reembolsado.")

        elif resolution_type == 'MIXED':
            dispute.status = Dispute.STATUS_RESUELTA_MIXTA
            dispute.resolution_notes = notes
            dispute.resolved_by = request.user
            dispute.resolved_at = timezone.now()
            dispute.save()

            messages.success(request, "Disputa resuelta con acuerdo mixto registrado.")

        return redirect('backoffice:disputes_list')

    context = {
        'dispute': dispute,
        'booking': booking,
        'payment': payment,
        'chat_messages': chat_messages,
    }
    return render(request, 'backoffice/detalle_disputa.html', context)


# ==============================================================================
# 7. LIBRO MAYOR DE AUDITORÍA TRANSACCIONAL Y CUSTODIA (ESCROW LEDGER)
# ==============================================================================

@login_required
@admin_required
def escrow_ledger_view(request):
    """Libro mayor con filtros por estado de custodia y búsqueda de transacciones."""
    status_filter = request.GET.get('status', 'ALL')
    search_query = request.GET.get('q', '').strip()

    transactions = PaymentTransaction.objects.all().select_related(
        'booking', 'booking__organization', 'booking__professional'
    ).order_by('-created_at')

    if status_filter != 'ALL':
        transactions = transactions.filter(escrow_status=status_filter)

    if search_query:
        transactions = transactions.filter(
            Q(transaction_id__icontains=search_query) |
            Q(buy_order__icontains=search_query) |
            Q(booking__organization__username__icontains=search_query) |
            Q(booking__professional__username__icontains=search_query)
        )

    # Totales para resumen del ledger
    total_retained = PaymentTransaction.objects.filter(escrow_status=PaymentTransaction.STATUS_RETENIDO).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_released = PaymentTransaction.objects.filter(escrow_status=PaymentTransaction.STATUS_LIBERADO).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_refunded = PaymentTransaction.objects.filter(escrow_status=PaymentTransaction.STATUS_REEMBOLSADO).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_fees = PaymentTransaction.objects.aggregate(Sum('skilly_fee_amount'))['skilly_fee_amount__sum'] or 0

    context = {
        'transactions': transactions,
        'status_filter': status_filter,
        'search_query': search_query,
        'total_retained': total_retained,
        'total_released': total_released,
        'total_refunded': total_refunded,
        'total_fees': total_fees,
    }
    return render(request, 'backoffice/libro_custodia.html', context)


# ==============================================================================
# 8. AUDITORÍA DE CALIDAD E INSIGNIAS CUALITATIVAS
# ==============================================================================

@login_required
@admin_required
def quality_audit_view(request):
    """Auditoría confidencial de evaluaciones e insignias cualitativas."""
    reviews = Review.objects.all().select_related('booking', 'professional', 'organization').prefetch_related('badges').order_by('-created_at')
    badge_tallies = Badge.objects.annotate(usage_count=Count('reviews')).order_by('-usage_count')
    badge_form = BadgeForm()

    context = {
        'reviews': reviews,
        'badge_tallies': badge_tallies,
        'badge_form': badge_form,
    }
    return render(request, 'backoffice/auditoria_calidad.html', context)


@login_required
@admin_required
def badge_create_action(request):
    """Crea una nueva insignia cualitativa para evaluación de profesionales."""
    if request.method == 'POST':
        form = BadgeForm(request.POST)
        if form.is_valid():
            badge = form.save()
            messages.success(request, f"Insignia '{badge.name}' creada exitosamente.")
        else:
            messages.error(request, "Error al crear la insignia. Verifique los datos ingresados.")

    return redirect('backoffice:quality_audit')


# ==============================================================================
# 9. GESTIÓN DE BENEFICIOS Y CONVENIOS
# ==============================================================================

@login_required
@admin_required
def benefits_management_view(request):
    """CRUD de alianzas estratégicas y beneficios para profesionales."""
    benefits = Benefit.objects.all().order_by('-created_at')
    benefit_form = BenefitForm()

    if request.method == 'POST':
        form = BenefitForm(request.POST)
        if form.is_valid():
            benefit = form.save()
            messages.success(request, f"Beneficio '{benefit.title}' registrado con éxito.")
            return redirect('backoffice:benefits_management')
        else:
            messages.error(request, "Error en los campos del beneficio. Verifique la información.")

    context = {
        'benefits': benefits,
        'benefit_form': benefit_form,
    }
    return render(request, 'backoffice/gestion_beneficios.html', context)


@login_required
@admin_required
def benefit_edit_action(request, pk):
    """Edita un beneficio existente."""
    benefit = get_object_or_404(Benefit, pk=pk)

    if request.method == 'POST':
        form = BenefitForm(request.POST, instance=benefit)
        if form.is_valid():
            form.save()
            messages.success(request, f"Beneficio '{benefit.title}' actualizado.")
        else:
            messages.error(request, "Error al actualizar el beneficio.")

    return redirect('backoffice:benefits_management')


@login_required
@admin_required
def benefit_toggle_action(request, pk):
    """Activa o pausa la publicación de un beneficio."""
    benefit = get_object_or_404(Benefit, pk=pk)
    benefit.is_active = not benefit.is_active
    benefit.save()
    status_label = "activado" if benefit.is_active else "pausado"
    messages.info(request, f"El beneficio '{benefit.title}' ha sido {status_label}.")
    return redirect('backoffice:benefits_management')


@login_required
@admin_required
def benefit_delete_action(request, pk):
    """Elimina un beneficio del catálogo."""
    benefit = get_object_or_404(Benefit, pk=pk)
    title = benefit.title
    benefit.delete()
    messages.success(request, f"Beneficio '{title}' eliminado.")
    return redirect('backoffice:benefits_management')


# ==============================================================================
# 10. GESTIÓN DE CATEGORÍAS DEL MARKETPLACE
# ==============================================================================

@login_required
@admin_required
def categories_management_view(request):
    """Gestor de categorías y sectores del marketplace."""
    categories = Category.objects.annotate(services_count=Count('services')).order_by('name')
    category_form = CategoryForm()

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Categoría '{cat.name}' creada exitosamente.")
            return redirect('backoffice:categories_management')
        else:
            messages.error(request, "Error al crear la categoría. Revise el nombre.")

    context = {
        'categories': categories,
        'category_form': category_form,
    }
    return render(request, 'backoffice/gestion_categorias.html', context)


@login_required
@admin_required
def category_edit_action(request, pk):
    """Edita una categoría existente."""
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"Categoría '{category.name}' actualizada.")
        else:
            messages.error(request, "Error al actualizar la categoría.")

    return redirect('backoffice:categories_management')


@login_required
@admin_required
def category_delete_action(request, pk):
    """Elimina una categoría si no tiene servicios asociados críticos."""
    category = get_object_or_404(Category, pk=pk)
    if category.services.exists():
        messages.error(request, f"No puedes eliminar '{category.name}' porque tiene servicios asociados. Reasigna los servicios primero.")
    else:
        name = category.name
        category.delete()
        messages.success(request, f"Categoría '{name}' eliminada correctamente.")

    return redirect('backoffice:categories_management')
