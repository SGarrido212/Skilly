from django.urls import path
from . import views

app_name = 'backoffice'

urlpatterns = [
    # Centro de Comando & Dashboard Principal
    path('', views.admin_dashboard_view, name='dashboard'),
    path('update-take-rate/', views.update_take_rate_action, name='update_take_rate'),

    # Directorio de Usuarios, Perfiles 360 y Sanciones (Strikes)
    path('users/', views.users_management_view, name='users_management'),
    path('users/<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('users/<int:user_id>/apply-strike/', views.apply_strike_action, name='apply_strike'),
    path('users/revoke-strike/<int:strike_id>/', views.revoke_strike_action, name='revoke_strike'),
    path('users/<int:user_id>/admin-notes/', views.update_admin_notes_action, name='update_admin_notes'),
    path('users/<int:user_id>/toggle-expulsion/', views.toggle_pro_expulsion, name='toggle_pro_expulsion'),

    # Moderación y Control de Servicios
    path('services-moderation/', views.services_moderation_view, name='services_moderation'),
    path('services-moderation/<int:pk>/action/', views.service_moderation_action, name='service_moderation_action'),

    # Monitoreo de Reservas y Supervisión de Sesiones Skilly
    path('bookings-monitor/', views.bookings_monitor_view, name='bookings_monitor'),
    path('bookings-monitor/<int:pk>/action/', views.booking_admin_action, name='booking_admin_action'),

    # Mesa de Validación Documental de Profesionales y Chat de Entrevista/Reunión
    path('validations/', views.pro_validations_view, name='validations'),
    path('validations/<int:pro_id>/chat/', views.validation_chat_view, name='validation_chat'),
    path('validations/<int:pk>/<str:action>/', views.validate_pro_action, name='validate_pro'),
    path('my-validation-chat/', views.pro_own_validation_chat_view, name='pro_own_validation_chat'),

    # Mediación y Arbitraje de Disputas
    path('disputes/', views.disputes_list_view, name='disputes_list'),
    path('disputes/<int:pk>/', views.dispute_detail_view, name='dispute_detail'),

    # Libro Mayor de Custodia Transaccional (Escrow Ledger)
    path('escrow-ledger/', views.escrow_ledger_view, name='escrow_ledger'),

    # Auditoría de Calidad e Insignias Cualitativas
    path('quality-audit/', views.quality_audit_view, name='quality_audit'),
    path('quality-audit/badges/create/', views.badge_create_action, name='badge_create'),

    # Alianzas y Beneficios Estratégicos
    path('benefits/', views.benefits_management_view, name='benefits_management'),
    path('benefits/<int:pk>/edit/', views.benefit_edit_action, name='benefit_edit'),
    path('benefits/<int:pk>/toggle/', views.benefit_toggle_action, name='benefit_toggle'),
    path('benefits/<int:pk>/delete/', views.benefit_delete_action, name='benefit_delete'),

    # Categorías del Catálogo
    path('categories/', views.categories_management_view, name='categories_management'),
    path('categories/<int:pk>/edit/', views.category_edit_action, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete_action, name='category_delete'),
]
