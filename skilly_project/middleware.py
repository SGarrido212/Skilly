"""
Middleware de Seguridad Extrema para Skilly Admin.

AdminIPWhitelistMiddleware:
  - Bloquea acceso al panel de administración desde IPs no autorizadas.
  - En producción: requiere ADMIN_ALLOWED_IPS definida. Si está vacía, solo
    permite acceso desde 127.0.0.1 (Render Shell).
  - En desarrollo (DEBUG=True): permite todas las IPs sin restricción.
"""

import logging
from django.conf import settings
from django.http import HttpResponseForbidden

logger = logging.getLogger('skilly.admin_security')


def _get_client_ip(request):
    """Extrae la IP real del cliente, considerando proxies (Render usa X-Forwarded-For)."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


class AdminIPWhitelistMiddleware:
    """
    Middleware que restringe el acceso a los paneles administrativos:
    1. Django Admin nativo (ADMIN_URL_PATH)
    2. Back-Office Administrativo de Skilly (/backoffice/* excepto chat de pro)
    Únicamente permite el acceso a IPs autorizadas en ADMIN_ALLOWED_IPS.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_path = getattr(settings, 'ADMIN_URL_PATH', 'django-admin/')
        if not admin_path.startswith('/'):
            admin_path = f'/{admin_path}'

        # Detectar rutas protegidas de administración
        is_django_admin = request.path.startswith(admin_path)
        is_custom_backoffice = (
            request.path.startswith('/backoffice/') and 
            not request.path.startswith('/backoffice/my-validation-chat/')
        )

        if is_django_admin or is_custom_backoffice:
            # En desarrollo (DEBUG=True) no bloquear para facilitar pruebas locales
            if getattr(settings, 'DEBUG', False):
                return self.get_response(request)

            allowed_ips = getattr(settings, 'ADMIN_ALLOWED_IPS', [])
            if '*' in allowed_ips:
                return self.get_response(request)

            # Si no hay IPs configuradas en producción, solo localhost (Render Shell)
            if not allowed_ips:
                allowed_ips = ['127.0.0.1', '::1']

            client_ip = _get_client_ip(request)

            if client_ip not in allowed_ips:
                logger.warning(
                    "ACCESO ADMIN/BACKOFFICE BLOQUEADO | IP: %s | Ruta: %s | Usuario: %s",
                    client_ip,
                    request.path,
                    getattr(request.user, 'username', 'anónimo'),
                )
                return HttpResponseForbidden(
                    "<h1>403 Forbidden</h1>"
                    "<p>Acceso restringido: Esta dirección IP no tiene autorización para acceder al panel de administración de Skilly.</p>"
                )

            logger.info(
                "Acceso admin autorizado | IP: %s | Ruta: %s | Usuario: %s",
                client_ip,
                request.path,
                getattr(request.user, 'username', 'anónimo'),
            )

        return self.get_response(request)

