"""
URL configuration for skilly_project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import public_pro_profile_view

urlpatterns = [
    path('django-admin/', admin.site.urls),
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
