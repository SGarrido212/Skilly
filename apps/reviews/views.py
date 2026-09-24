# -- VISTAS DEL MÓDULO DE EVALUACIONES CUALITATIVAS PRIVADAS --
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from bookings.models import Booking
from .models import Review, Badge
from .forms import ReviewForm

@login_required
def review_create_view(request, booking_id):
    # -- PROCESAMIENTO DE ENVÍO DE EVALUACIÓN CUALITATIVA DE SERVICIO --
    booking = get_object_or_404(Booking, pk=booking_id, organization=request.user)

    if booking.status != Booking.STATUS_FINALIZADO:
        messages.error(request, "Solo puedes evaluar un servicio que haya finalizado.")
        return redirect('bookings:detail', pk=booking.id)

    if hasattr(booking, 'review'):
        messages.info(request, "Ya has enviado la evaluación privada para esta reserva.")
        return redirect('bookings:detail', pk=booking.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.professional = booking.professional
            review.organization = request.user
            review.rating = 5
            review.save()
            form.save_m2m()

            # -- AGREGAR CUALIDAD EXTRA SI FUE INGRESADA POR EL USUARIO --
            custom_badge_name = form.cleaned_data.get('custom_badge', '').strip()
            if custom_badge_name:
                badge, _ = Badge.objects.get_or_create(
                    name=custom_badge_name,
                    defaults={'icon': 'fa-award', 'description': 'Cualidad agregada por cliente'}
                )
                review.badges.add(badge)

            messages.success(request, "¡Gracias! Tu evaluación cualitativa ha sido enviada confidencialmente al Back-Office.")
            return redirect('bookings:detail', pk=booking.id)
    else:
        form = ReviewForm()

    context = {
        'booking': booking,
        'form': form,
        'badges': Badge.objects.all(),
    }
    return render(request, 'reviews/formulario_evaluacion.html', context)
