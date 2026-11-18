"""
URL configuration for skilly_project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from users.views import public_pro_profile_view

# Personalización del sitio admin
admin.site.site_header = "Skilly Control"
admin.site.site_title = "Skilly"
admin.site.index_title = "Panel de Control Interno"

# URL del admin nativo
_admin_url = getattr(settings, 'ADMIN_URL_PATH', 'django-admin/')
if not _admin_url.endswith('/'):
    _admin_url += '/'

urlpatterns = [
    # Redirección amigable: /admin/ lleva directamente al panel administrativo de Skilly
    path('admin/', RedirectView.as_view(url='/backoffice/', permanent=False)),
    path('dashboard/', RedirectView.as_view(url='/users/dashboard/', permanent=False)),

    # Django Admin nativo
    path(_admin_url, admin.site.urls),

    # Apps del sistema
    path('', include('services.urls')),
    path('users/', include('users.urls')),
    path('pro/<slug:slug>/', public_pro_profile_view, name='public_pro_profile'),
    path('availability/', include('availability.urls')),
    path('bookings/', include('bookings.urls')),
    path('payments/', include('escrow_payments.urls')),
    path('reviews/', include('reviews.urls')),
    path('disputes/', include('disputes.urls')),
    path('benefits/', include('benefits.urls')),
    path('backoffice/', include('backoffice.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
