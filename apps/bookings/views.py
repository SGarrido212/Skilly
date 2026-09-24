# -- VISTAS DE AGENDAMIENTO, RESERVAS Y CHAT TRAZABLE --
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.utils.crypto import get_random_string
from .models import Booking, BookingMessage
from .forms import BookingCreateForm, BookingMessageForm
from services.models import Service
from availability.models import TimeSlot
from users.models import CustomUser, OrganizationProfile
from escrow_payments.models import PaymentTransaction

def booking_create_view(request, service_id):
    # -- AGENDAMIENTO RÁPIDO Y RESERVA GUEST CHECKOUT --
    service = get_object_or_404(Service, pk=service_id, is_active=True)
    slot_id = request.GET.get('slot_id') or request.POST.get('slot_id')

    if not slot_id:
        messages.error(request, "Debes seleccionar un horario disponible para agendar el servicio.")
        return redirect('services:service_detail', pk=service_id)

    slot = get_object_or_404(TimeSlot, pk=slot_id, professional=service.professional)

    if not slot.is_available:
        messages.error(request, "Este bloque horario ya no se encuentra disponible.")
        return redirect('services:service_detail', pk=service_id)

    if request.method == 'POST':
        form = BookingCreateForm(request.POST, user=request.user if request.user.is_authenticated else None)
        if form.is_valid():
            locked = slot.lock_for_checkout()
            if not locked:
                messages.error(request, "El bloque horario expiró o fue reservado por otro usuario.")
                return redirect('services:service_detail', pk=service_id)

            if request.user.is_authenticated:
                org_user = request.user
            else:
                email = form.cleaned_data['email'].strip().lower()
                first_name = form.cleaned_data['first_name'].strip()
                last_name = form.cleaned_data['last_name'].strip()
                phone = form.cleaned_data.get('phone', '').strip()
                company_name = form.cleaned_data['company_name'].strip()
                company_rut = form.cleaned_data.get('company_rut', '').strip() or 'PENDIENTE'

                existing_user = CustomUser.objects.filter(email=email).first()
                if existing_user:
                    org_user = existing_user
                    OrganizationProfile.objects.get_or_create(
                        user=org_user,
                        defaults={'company_name': company_name, 'tax_id': company_rut}
                    )
                else:
                    base_username = email.split('@')[0]
                    username = base_username
                    counter = 1
                    while CustomUser.objects.filter(username=username).exists():
                        username = f"{base_username}_{counter}"
                        counter += 1

                    org_user = CustomUser.objects.create(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,
                        role=CustomUser.ROLE_ORGANIZACION
                    )
                    org_user.set_password(get_random_string(12))
                    org_user.save()

                    OrganizationProfile.objects.create(
                        user=org_user,
                        company_name=company_name,
                        tax_id=company_rut
                    )

                login(request, org_user)

            booking = form.save(commit=False)
            booking.service = service
            booking.professional = service.professional
            booking.organization = org_user
            booking.timeslot = slot
            booking.scheduled_date = slot.date
            booking.start_time = slot.start_time
            booking.end_time = slot.end_time
            booking.status = Booking.STATUS_PRE_RESERVADA
            booking.save()

            messages.info(request, "Horario pre-reservado por 20 minutos. Procede con el pago en custodia para confirmar.")
            return redirect('escrow_payments:checkout', booking_id=booking.id)
    else:
        form = BookingCreateForm(user=request.user if request.user.is_authenticated else None)

    context = {
        'service': service,
        'slot': slot,
        'form': form,
    }
    return render(request, 'bookings/crear_reserva.html', context)


@login_required
def booking_detail_view(request, pk):
    # -- DETALLE DE RESERVA, ACCIONES DE HITOS Y CHAT INTERNO --
    booking = get_object_or_404(Booking, pk=pk)

    if request.user != booking.organization and request.user != booking.professional and not request.user.is_admin_role:
        messages.error(request, "No tienes permiso para ver esta reserva.")
        return redirect('services:marketplace')

    chat_messages = booking.messages.all().select_related('sender')
    message_form = BookingMessageForm()

    context = {
        'booking': booking,
        'chat_messages': chat_messages,
        'message_form': message_form,
        'payment': getattr(booking, 'payment_transaction', None),
        'dispute': getattr(booking, 'dispute', None),
        'review': getattr(booking, 'review', None),
        'is_cancellation_warning': booking.is_cancellation_within_24h,
    }
    return render(request, 'bookings/detalle_reserva.html', context)


@login_required
def booking_send_message_view(request, pk):
    # -- ENVÍO DE MENSAJES Y ARCHIVOS ADJUNTOS EN CHAT INTERNO --
    booking = get_object_or_404(Booking, pk=pk)
    if request.user != booking.organization and request.user != booking.professional and not request.user.is_admin_role:
        messages.error(request, "No tienes acceso a este chat.")
        return redirect('services:marketplace')

    if request.method == 'POST':
        form = BookingMessageForm(request.POST, request.FILES)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.booking = booking
            msg.sender = request.user
            msg.save()

    return redirect('bookings:detail', pk=pk)


@login_required
def booking_update_status_view(request, pk, new_status):
    # -- ACTUALIZACIÓN DE HITOS DEL CICLO DE VIDA DE LA RESERVA --
    booking = get_object_or_404(Booking, pk=pk)
    user = request.user

    if new_status == Booking.STATUS_ACEPTADA and user == booking.professional:
        booking.status = Booking.STATUS_ACEPTADA
        booking.accepted_at = timezone.now()
        booking.save()
        messages.success(request, "Has aceptado la solicitud de reserva.")

    elif new_status == Booking.STATUS_RECHAZADA and user == booking.professional:
        booking.status = Booking.STATUS_RECHAZADA
        booking.save()
        if booking.timeslot:
            booking.timeslot.release_lock()
        messages.info(request, "Has rechazado la solicitud de reserva.")

    elif new_status == Booking.STATUS_EN_EJECUCION and user == booking.professional:
        if booking.status in [Booking.STATUS_PAGADO_EN_CUSTODIA, Booking.STATUS_ACEPTADA]:
            booking.status = Booking.STATUS_EN_EJECUCION
            booking.save()
            messages.success(request, "Has iniciado la ejecución del servicio.")

    elif new_status == Booking.STATUS_ENTREGADO and user == booking.professional:
        if booking.status in [Booking.STATUS_EN_EJECUCION, Booking.STATUS_PAGADO_EN_CUSTODIA]:
            booking.status = Booking.STATUS_ENTREGADO
            booking.save()
            messages.success(request, "Has marcado el servicio como entregado. La organización validará el resultado.")

    elif new_status == Booking.STATUS_FINALIZADO and user == booking.organization:
        if booking.status in [Booking.STATUS_ENTREGADO, Booking.STATUS_EN_EJECUCION, Booking.STATUS_PAGADO_EN_CUSTODIA]:
            booking.status = Booking.STATUS_FINALIZADO
            booking.completed_at = timezone.now()
            booking.save()
            if booking.timeslot:
                booking.timeslot.mark_booked()

            if hasattr(booking, 'payment_transaction'):
                booking.payment_transaction.release_to_professional()

            messages.success(request, "¡Servicio finalizado con éxito! El pago en custodia ha sido liberado al profesional.")
            return redirect('reviews:create', booking_id=booking.id)

    elif new_status == Booking.STATUS_CANCELADO:
        if user == booking.organization or user == booking.professional:
            if booking.is_cancellation_within_24h:
                booking.cancellation_penalty_applies = True
                messages.warning(request, "Atención: La cancelación se realiza con menos de 24h de anticipación. Aplica política de penalización.")

            booking.status = Booking.STATUS_CANCELADO
            booking.cancelled_at = timezone.now()
            booking.save()
            if booking.timeslot:
                booking.timeslot.release_lock()

            if hasattr(booking, 'payment_transaction'):
                booking.payment_transaction.refund_to_organization()

            messages.info(request, "La reserva ha sido cancelada.")

    return redirect('bookings:detail', pk=pk)
