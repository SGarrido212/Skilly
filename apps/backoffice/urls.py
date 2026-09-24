from django.urls import path
from . import views

app_name = 'backoffice'

urlpatterns = [
    path('', views.admin_dashboard_view, name='dashboard'),
    path('validations/', views.pro_validations_view, name='validations'),
    path('validations/<int:pk>/<str:action>/', views.validate_pro_action, name='validate_pro'),
    path('disputes/', views.disputes_list_view, name='disputes_list'),
    path('disputes/<int:pk>/', views.dispute_detail_view, name='dispute_detail'),
    path('quality-audit/', views.quality_audit_view, name='quality_audit'),
    path('escrow-ledger/', views.escrow_ledger_view, name='escrow_ledger'),
]
