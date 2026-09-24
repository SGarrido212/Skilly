# -- VISTAS DE MARKETPLACE Y SERVICIOS --
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Service, Category
from .forms import ServiceForm
from availability.models import TimeSlot
from users.models import ProfessionalProfile

def marketplace_view(request):
    # -- CATÁLOGO GENERAL Y BÚSQUEDA DE SERVICIOS EN EL MARKETPLACE --
    services = Service.objects.filter(is_active=True).select_related('professional', 'category')
    categories = Category.objects.all()

    category_slug = request.GET.get('category')
    search_query = request.GET.get('q')
    max_price = request.GET.get('max_price')

    if category_slug:
        services = services.filter(category__slug=category_slug)

    if search_query:
        services = services.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(professional__first_name__icontains=search_query) |
            Q(professional__last_name__icontains=search_query) |
            Q(professional__professional_profile__profession__icontains=search_query)
        )

    if max_price:
        try:
            services = services.filter(price__lte=float(max_price))
        except ValueError:
            pass

    context = {
        'services': services,
        'categories': categories,
        'selected_category': category_slug,
        'search_query': search_query or '',
        'max_price': max_price or '',
    }
    return render(request, 'services/mercado_servicios.html', context)


def service_detail_view(request, pk):
    # -- DETALLE INDIVIDUAL DEL SERVICIO Y SELECTOR DE DISPONIBILIDAD --
    service = get_object_or_404(Service, pk=pk, is_active=True)
    pro_user = service.professional
    pro_profile = getattr(pro_user, 'professional_profile', None)
    
    available_slots = TimeSlot.objects.filter(
        professional=pro_user,
        status=TimeSlot.STATUS_DISPONIBLE
    ).order_by('date', 'start_time')

    context = {
        'service': service,
        'pro_user': pro_user,
        'pro_profile': pro_profile,
        'available_slots': available_slots,
    }
    return render(request, 'services/detalle_servicio.html', context)


@login_required
def service_create_view(request):
    # -- CREACIÓN DE NUEVO SERVICIO POR PROFESIONAL --
    if not request.user.is_professional:
        messages.warning(request, "Solo los profesionales pueden crear servicios.")
        return redirect('services:marketplace')

    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.professional = request.user
            service.save()
            messages.success(request, f"¡Servicio '{service.title}' publicado exitosamente!")
            return redirect('users:pro_dashboard')
    else:
        form = ServiceForm()

    return render(request, 'services/formulario_servicio.html', {'form': form, 'title': 'Publicar Nuevo Servicio'})


@login_required
def service_edit_view(request, pk):
    # -- EDICIÓN DE SERVICIO EXISTENTE --
    service = get_object_or_404(Service, pk=pk, professional=request.user)

    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, f"Servicio '{service.title}' actualizado.")
            return redirect('users:pro_dashboard')
    else:
        form = ServiceForm(instance=service)

    return render(request, 'services/formulario_servicio.html', {'form': form, 'service': service, 'title': 'Editar Servicio'})
