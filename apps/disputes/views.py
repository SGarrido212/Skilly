# -- VISTAS DE APERTURA Y REPORTE DE DISPUTAS --
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from bookings.models import Booking
from .models import Dispute
from .forms import DisputeForm

@login_required
def dispute_create_view(request, booking_id):
    # -- FORMULARIO DE APERTURA DE DISPUTA Y CONGELAMIENTO DE FONDOS ESCROW --
    booking = get_object_or_404(Booking, pk=booking_id)

    if request.user != booking.organization and request.user != booking.professional:
        messages.error(request, "No tienes permisos sobre esta reserva.")
        return redirect('services:marketplace')

    if hasattr(booking, 'dispute'):
        messages.info(request, "Esta reserva ya se encuentra en proceso de disputa.")
        return redirect('bookings:detail', pk=booking.id)

    if request.method == 'POST':
        form = DisputeForm(request.POST, request.FILES)
        if form.is_valid():
            dispute = form.save(commit=False)
            dispute.booking = booking
            dispute.reported_by = request.user
            dispute.save()

            booking.status = Booking.STATUS_EN_DISPUTA
            booking.save()

            if hasattr(booking, 'payment_transaction'):
                booking.payment_transaction.freeze_for_dispute()

            messages.warning(request, "Se ha abierto el proceso de mediación. El equipo de Skilly Back-Office revisará los antecedentes.")
            return redirect('bookings:detail', pk=booking.id)
    else:
        form = DisputeForm()

    context = {
        'booking': booking,
        'form': form,
    }
    return render(request, 'disputes/formulario_disputa.html', context)
