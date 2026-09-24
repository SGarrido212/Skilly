# -- VISTAS DE USUARIOS Y PERFILES EN SKILLY --
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser, ProfessionalProfile, OrganizationProfile
from .forms import CustomUserRegisterForm, ProfessionalProfileForm, OrganizationProfileForm
from availability.models import TimeSlot
from services.models import Service

def register_view(request):
    # -- REGISTRO DE NUEVAS CUENTAS (PROFESIONAL U ORGANIZACIÓN) --
    if request.user.is_authenticated:
        return redirect('users:dashboard')

    if request.method == 'POST':
        form = CustomUserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role')
            if role == CustomUser.ROLE_PROFESIONAL:
                ProfessionalProfile.objects.create(
                    user=user,
                    profession="Profesional Skilly",
                    bio="Añade tu presentación profesional...",
                    hourly_rate=50.00
                )
            elif role == CustomUser.ROLE_ORGANIZACION:
                OrganizationProfile.objects.create(
                    user=user,
                    company_name=f"Empresa {user.first_name or user.username}",
                    tax_id="PENDIENTE"
                )
            login(request, user)
            messages.success(request, f"¡Bienvenido a Skilly, {user.first_name or user.username}! Tu cuenta se ha creado exitosamente.")
            return redirect('users:dashboard')
    else:
        form = CustomUserRegisterForm()

    return render(request, 'users/registro.html', {'form': form})


def public_pro_profile_view(request, slug):
    # -- VISUALIZACIÓN DEL PERFIL PÚBLICO DEL PROFESIONAL POR SLUG --
    profile = get_object_or_404(ProfessionalProfile, slug=slug)
    services = Service.objects.filter(professional=profile.user, is_active=True)
    available_slots = TimeSlot.objects.filter(
        professional=profile.user,
        status=TimeSlot.STATUS_DISPONIBLE
    )
    
    for slot in TimeSlot.objects.filter(professional=profile.user, status=TimeSlot.STATUS_PRE_RESERVADO):
        if not slot.is_available:
            pass
        else:
            slot.release_lock()

    context = {
        'profile': profile,
        'pro_user': profile.user,
        'services': services,
        'available_slots': available_slots,
    }
    return render(request, 'users/perfil_profesional.html', context)


@login_required
def dashboard_view(request):
    # -- REDIRECCIÓN SEGÚN ROL DE USUARIO AUTENTICADO --
    user = request.user
    if user.is_admin_role:
        return redirect('backoffice:dashboard')
    elif user.is_professional:
        return redirect('users:pro_dashboard')
    else:
        return redirect('users:org_dashboard')


@login_required
def pro_dashboard_view(request):
    # -- PANEL DE CONTROL PARA PROFESIONALES --
    if not request.user.is_professional:
        messages.warning(request, "Acceso exclusivo para profesionales.")
        return redirect('services:marketplace')
    
    profile = getattr(request.user, 'professional_profile', None)
    services = request.user.services.all()
    received_bookings = request.user.received_bookings.all().select_related('service', 'organization')
    timeslots = request.user.timeslots.all()

    context = {
        'profile': profile,
        'services': services,
        'bookings': received_bookings,
        'timeslots': timeslots,
    }
    return render(request, 'users/panel_profesional.html', context)


@login_required
def org_dashboard_view(request):
    # -- PANEL DE CONTROL PARA ORGANIZACIONES --
    if not request.user.is_organization:
        messages.warning(request, "Acceso exclusivo para organizaciones.")
        return redirect('services:marketplace')

    profile = getattr(request.user, 'organization_profile', None)
    sent_bookings = request.user.sent_bookings.all().select_related('service', 'professional')

    context = {
        'profile': profile,
        'bookings': sent_bookings,
    }
    return render(request, 'users/panel_organizacion.html', context)


@login_required
def profile_edit_view(request):
    # -- EDICIÓN DE DATOS Y DOCUMENTOS DE PERFIL --
    user = request.user
    if user.is_professional:
        profile, created = ProfessionalProfile.objects.get_or_create(user=user)
        form_class = ProfessionalProfileForm
    elif user.is_organization:
        profile, created = OrganizationProfile.objects.get_or_create(user=user)
        form_class = OrganizationProfileForm
    else:
        messages.info(request, "Los administradores no requieren editar perfil de marketplace.")
        return redirect('backoffice:dashboard')

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            if user.is_professional and 'support_document' in request.FILES:
                profile.validation_status = ProfessionalProfile.STATUS_PENDIENTE
                profile.rejection_reason = None
            form.save()
            messages.success(request, "Tu perfil ha sido actualizado correctamente.")
            return redirect('users:dashboard')
    else:
        form = form_class(instance=profile)

    return render(request, 'users/editar_perfil.html', {'form': form, 'profile': profile})
