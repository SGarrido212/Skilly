"""
Django Settings for Skilly — Production-ready (Render.com) & Local-compatible
Diseñado para funcionar sin errores tanto en desarrollo local como en producción.
"""

from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / 'apps'))

# Detección de paquetes opcionales instalados (para evitar errores en local si no están)
try:
    import dj_database_url
    HAS_DJ_DATABASE_URL = True
except ImportError:
    HAS_DJ_DATABASE_URL = False

try:
    import whitenoise
    HAS_WHITENOISE = True
except ImportError:
    HAS_WHITENOISE = False

try:
    import axes
    HAS_AXES = True
except ImportError:
    HAS_AXES = False

# ─────────────────────────────────────────────
# SEGURIDAD CORE
# ─────────────────────────────────────────────
# En producción (Render), SECRET_KEY viene obligatoria de env var.
# En local, tiene un fallback seguro para no crashear en desarrollo.
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-skilly-dev-key-change-in-production-2026-safe-fallback-x9!'
)

# DEBUG es True por defecto para desarrollo local; en Render render.yaml define DEBUG=False
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS_ENV = os.environ.get('ALLOWED_HOSTS', '')
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_ENV.split(',') if h.strip()]
else:
    # En desarrollo local permite localhost y 127.0.0.1
    ALLOWED_HOSTS = ['*'] if DEBUG else ['localhost', '127.0.0.1', 'skilly.onrender.com']

# Custom User Model
AUTH_USER_MODEL = 'users.CustomUser'

# ─────────────────────────────────────────────
# URL SECRETA DEL ADMIN — nunca exponer /admin/
# ─────────────────────────────────────────────
# En producción, define ADMIN_URL_PATH en variables de entorno.
# Ejemplo: ADMIN_URL_PATH=x9k2p7-control-panel/
ADMIN_URL_PATH = os.environ.get('ADMIN_URL_PATH', 'django-admin/')

# ─────────────────────────────────────────────
# APLICACIONES
# ─────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Skilly Apps
    'users',
    'services',
    'availability',
    'bookings',
    'escrow_payments',
    'reviews',
    'disputes',
    'benefits',
    'backoffice',
]

if HAS_AXES:
    INSTALLED_APPS.insert(6, 'axes')

# ─────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
]

if HAS_WHITENOISE:
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')

MIDDLEWARE.extend([
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
])

if HAS_AXES:
    MIDDLEWARE.append('axes.middleware.AxesMiddleware')

MIDDLEWARE.extend([
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'skilly_project.middleware.AdminIPWhitelistMiddleware',
])

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

if HAS_AXES:
    AUTHENTICATION_BACKENDS.insert(0, 'axes.backends.AxesStandaloneBackend')

ROOT_URLCONF = 'skilly_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'skilly_project.wsgi.application'

# ─────────────────────────────────────────────
# BASE DE DATOS — PostgreSQL en Render / SQLite en Local
# ─────────────────────────────────────────────
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and HAS_DJ_DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ─────────────────────────────────────────────
# VALIDACIÓN DE CONTRASEÑAS
# ─────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {'max_similarity': 0.5},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8 if DEBUG else 16},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─────────────────────────────────────────────
# INTERNACIONALIZACIÓN
# ─────────────────────────────────────────────
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────────
# ARCHIVOS ESTÁTICOS
# ─────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'assets',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

if HAS_WHITENOISE and not DEBUG:
    STORAGES = {
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
    }
else:
    STORAGES = {
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
    }

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────
# SESIONES — Expiración y Seguridad
# ─────────────────────────────────────────────
SESSION_COOKIE_AGE = 1800            # 30 minutos de inactividad
SESSION_SAVE_EVERY_REQUEST = True    # Renueva el timer con cada request
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Siempre cierra al cerrar pestaña
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Sesiones en BD (revocables)

# ─────────────────────────────────────────────
# AUTH REDIRECTS — Ruteo Inteligente por Rol
# ─────────────────────────────────────────────
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'users:dashboard'   # Redirige a dashboard_view que distribuye según rol
LOGOUT_REDIRECT_URL = 'services:marketplace'

# ─────────────────────────────────────────────
# SEGURIDAD EN PRODUCCIÓN (Solo cuando DEBUG=False)
# ─────────────────────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000       # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_TRUSTED_ORIGINS = [
        f"https://{h.strip()}"
        for h in os.environ.get('ALLOWED_HOSTS', '').split(',')
        if h.strip()
    ]

# ─────────────────────────────────────────────
# DJANGO-AXES (Solo si está disponible)
# ─────────────────────────────────────────────
if HAS_AXES:
    AXES_ENABLED = True
    AXES_FAILURE_LIMIT = 5               # Bloquear tras 5 intentos fallidos
    AXES_COOLOFF_TIME = 1                # Bloqueo de 1 hora
    AXES_LOCKOUT_PARAMETERS = ['ip_address', 'username']
    AXES_RESET_ON_SUCCESS = True
    AXES_LOCKOUT_TEMPLATE = None
    AXES_VERBOSE = False
    AXES_NEVER_LOCKOUT_WHITELIST = False
    AXES_HTTP_RESPONSE_CODE = 403

# ─────────────────────────────────────────────
# WHITELIST DE IPs PARA EL ADMIN
# ─────────────────────────────────────────────
_admin_ips_raw = os.environ.get('ADMIN_ALLOWED_IPS', '')
ADMIN_ALLOWED_IPS = [ip.strip() for ip in _admin_ips_raw.split(',') if ip.strip()]

# ─────────────────────────────────────────────
# LOGGING — Auditoría del Admin y Back-Office
# ─────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'audit': {
            'format': '[{asctime}] {levelname} | {name} | {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'audit',
        },
    },
    'loggers': {
        'skilly.admin_security': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'skilly.backoffice_audit': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
