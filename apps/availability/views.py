# -- VISTAS DE GESTIÓN DE DISPONIBILIDAD Y BLOQUES HORARIOS --
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TimeSlot
import datetime

@login_required
def availability_manage_view(request):
    # -- GESTIÓN Y GENERACIÓN DE BLOQUES HORARIOS DE 20 MINUTOS --
    if not request.user.is_professional:
        messages.warning(request, "Acceso solo para profesionales.")
        return redirect('services:marketplace')

    if request.method == 'POST':
        date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')

        try:
            date_val = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            start_t = datetime.datetime.strptime(start_time_str, '%H:%M').time()
            end_t = datetime.datetime.strptime(end_time_str, '%H:%M').time()

            curr_dt = datetime.datetime.combine(date_val, start_t)
            end_dt = datetime.datetime.combine(date_val, end_t)

            created_count = 0
            while curr_dt + datetime.timedelta(minutes=20) <= end_dt:
                slot_start = curr_dt.time()
                slot_end = (curr_dt + datetime.timedelta(minutes=20)).time()
                
                if not TimeSlot.objects.filter(professional=request.user, date=date_val, start_time=slot_start).exists():
                    TimeSlot.objects.create(
                        professional=request.user,
                        date=date_val,
                        start_time=slot_start,
                        end_time=slot_end,
                        status=TimeSlot.STATUS_DISPONIBLE
                    )
                    created_count += 1

                curr_dt += datetime.timedelta(minutes=20)

            messages.success(request, f"¡Se han creado {created_count} bloques de disponibilidad de 20 minutos!")
        except Exception as e:
            messages.error(request, f"Error al generar bloques horarios: {str(e)}")

        return redirect('availability:manage')

    slots = TimeSlot.objects.filter(professional=request.user).order_by('date', 'start_time')
    return render(request, 'availability/gestion_disponibilidad.html', {'slots': slots})


@login_required
def slot_delete_view(request, pk):
    # -- ELIMINACIÓN DE BLOQUE HORARIO NO RESERVADO --
    slot = get_object_or_404(TimeSlot, pk=pk, professional=request.user)
    if slot.status == TimeSlot.STATUS_OCUPADO:
        messages.error(request, "No se puede eliminar un bloque que ya está reservado por un cliente.")
    else:
        slot.delete()
        messages.success(request, "Bloque horario eliminado.")
    return redirect('availability:manage')
