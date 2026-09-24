# -- VISTAS DEL BACK-OFFICE DE ADMINISTRACIÓN Y CONTROL --
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from users.models import CustomUser, ProfessionalProfile
from bookings.models import Booking
from escrow_payments.models import PaymentTransaction
from disputes.models import Dispute
from reviews.models import Review, Badge

def admin_required(view_func):
    # -- DECORADOR DE SEGURIDAD PARA VALIDAR ROL ADMINISTRADOR --
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin_role:
            messages.error(request, "Acceso restringido al Back-Office de Skilly.")
            return redirect('services:marketplace')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required
@admin_required
def admin_dashboard_view(request):
    # -- DASHBOARD GENERAL CON KPIs Y MÉTRICAS CLAVE DEL MARKETPLACE --
    total_volume = PaymentTransaction.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_held = PaymentTransaction.objects.filter(escrow_status=PaymentTransaction.STATUS_RETENIDO).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_fees = PaymentTransaction.objects.aggregate(Sum('skilly_fee_amount'))['skilly_fee_amount__sum'] or 0
    pending_validations_count = ProfessionalProfile.objects.filter(validation_status=ProfessionalProfile.STATUS_PENDIENTE).count()
    open_disputes_count = Dispute.objects.filter(status=Dispute.STATUS_ABIERTA).count()

    recent_transactions = PaymentTransaction.objects.select_related('booking', 'booking__service', 'booking__organization').order_by('-created_at')[:5]
    recent_disputes = Dispute.objects.filter(status=Dispute.STATUS_ABIERTA).select_related('booking', 'reported_by')[:5]

    context = {
        'total_volume': total_volume,
        'total_held': total_held,
        'total_fees': total_fees,
        'pending_validations_count': pending_validations_count,
        'open_disputes_count': open_disputes_count,
        'recent_transactions': recent_transactions,
        'recent_disputes': recent_disputes,
    }
    return render(request, 'backoffice/panel_administracion.html', context)


@login_required
@admin_required
def pro_validations_view(request):
    # -- MESA DE VALIDACIÓN DE DOCUMENTOS DE PROFESIONALES --
    pending_pros = ProfessionalProfile.objects.filter(validation_status=ProfessionalProfile.STATUS_PENDIENTE).select_related('user')
    validated_pros = ProfessionalProfile.objects.filter(validation_status=ProfessionalProfile.STATUS_VALIDADO).select_related('user')
    rejected_pros = ProfessionalProfile.objects.filter(validation_status=ProfessionalProfile.STATUS_RECHAZADO).select_related('user')

    context = {
        'pending_pros': pending_pros,
        'validated_pros': validated_pros,
        'rejected_pros': rejected_pros,
    }
    return render(request, 'backoffice/validaciones_profesionales.html', context)


@login_required
@admin_required
def validate_pro_action(request, pk, action):
    # -- ACCIÓN DE APROBACIÓN O RECHAZO DOCUMENTAL --
    profile = get_object_or_404(ProfessionalProfile, pk=pk)

    if action == 'approve':
        profile.validation_status = ProfessionalProfile.STATUS_VALIDADO
        profile.rejection_reason = None
        profile.save()
        messages.success(request, f"Perfil del profesional {profile.user.get_full_name()} ha sido VALIDADO.")

    elif action == 'reject' and request.method == 'POST':
        reason = request.POST.get('rejection_reason', 'Documentos no válidos o incompletos.')
        profile.validation_status = ProfessionalProfile.STATUS_RECHAZADO
        profile.rejection_reason = reason
        profile.save()
        messages.info(request, f"Perfil del profesional {profile.user.get_full_name()} ha sido RECHAZADO.")

    return redirect('backoffice:validations')


@login_required
@admin_required
def disputes_list_view(request):
    # -- LISTADO DE DISPUTAS Y CASOS DE CONTROVERSIA --
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
    # -- DETALLE Y RESOLUCIÓN ARBITRAL DE DISPUTA --
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


@login_required
@admin_required
def quality_audit_view(request):
    # -- AUDITORÍA CONFIDENCIAL DE EVALUACIONES CUALITATIVAS E INSIGNIAS --
    reviews = Review.objects.all().select_related('booking', 'professional', 'organization').prefetch_related('badges')

    pros = CustomUser.objects.filter(role=CustomUser.ROLE_PROFESIONAL).annotate(
        reviews_count=Count('received_reviews')
    )

    badge_tallies = Badge.objects.annotate(usage_count=Count('reviews'))

    context = {
        'reviews': reviews,
        'pros': pros,
        'badge_tallies': badge_tallies,
    }
    return render(request, 'backoffice/auditoria_calidad.html', context)


@login_required
@admin_required
def escrow_ledger_view(request):
    # -- LIBRO MAYOR DE AUDITORÍA TRANSACCIONAL Y CUSTODIA --
    transactions = PaymentTransaction.objects.all().select_related('booking', 'booking__organization', 'booking__professional').order_by('-created_at')

    context = {
        'transactions': transactions,
    }
    return render(request, 'backoffice/libro_custodia.html', context)
