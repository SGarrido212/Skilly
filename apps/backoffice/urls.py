from django.urls import path
from . import views

app_name = 'backoffice'

urlpatterns = [
    # -. Panel principal y configuración de la plataforma.
    path('', views.admin_dashboard_view, name='dashboard'),
    path('update-take-rate/', views.update_take_rate_action, name='update_take_rate'),

    # -. Gestión de usuarios y sanciones.
    path('users/', views.users_management_view, name='users_management'),
    path('users/<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('users/<int:user_id>/apply-strike/', views.apply_strike_action, name='apply_strike'),
    path('users/revoke-strike/<int:strike_id>/', views.revoke_strike_action, name='revoke_strike'),
    path('users/<int:user_id>/admin-notes/', views.update_admin_notes_action, name='update_admin_notes'),
    path('users/<int:user_id>/toggle-expulsion/', views.toggle_pro_expulsion, name='toggle_pro_expulsion'),

    # -. Moderación de servicios.
    path('services-moderation/', views.services_moderation_view, name='services_moderation'),
    path('services-moderation/<int:pk>/action/', views.service_moderation_action, name='service_moderation_action'),

    # -. Monitoreo y supervisión de reservas.
    path('bookings-monitor/', views.bookings_monitor_view, name='bookings_monitor'),
    path('bookings-monitor/<int:pk>/action/', views.booking_admin_action, name='booking_admin_action'),

    # -. Validación profesional y coordinación.
    path('validations/', views.pro_validations_view, name='validations'),
    path('validations/<int:pro_id>/chat/', views.validation_chat_view, name='validation_chat'),
    path('validations/<int:pk>/<str:action>/', views.validate_pro_action, name='validate_pro'),
    path('my-validation-chat/', views.pro_own_validation_chat_view, name='pro_own_validation_chat'),

    # -. Mediación de disputas.
    path('disputes/', views.disputes_list_view, name='disputes_list'),
    path('disputes/<int:pk>/', views.dispute_detail_view, name='dispute_detail'),

    # -. Libro mayor de custodia.
    path('escrow-ledger/', views.escrow_ledger_view, name='escrow_ledger'),

    # -. Auditoría de calidad e insignias.
    path('quality-audit/', views.quality_audit_view, name='quality_audit'),
    path('quality-audit/badges/create/', views.badge_create_action, name='badge_create'),

    # -. Gestión de beneficios.
    path('benefits/', views.benefits_management_view, name='benefits_management'),
    path('benefits/<int:pk>/edit/', views.benefit_edit_action, name='benefit_edit'),
    path('benefits/<int:pk>/toggle/', views.benefit_toggle_action, name='benefit_toggle'),
    path('benefits/<int:pk>/delete/', views.benefit_delete_action, name='benefit_delete'),

    # -. Categorías del marketplace.
    path('categories/', views.categories_management_view, name='categories_management'),
    path('categories/<int:pk>/edit/', views.category_edit_action, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete_action, name='category_delete'),
]
