from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('', views.marketplace_view, name='marketplace'),
    path('services/<int:pk>/', views.service_detail_view, name='service_detail'),
    path('services/create/', views.service_create_view, name='service_create'),
    path('services/<int:pk>/edit/', views.service_edit_view, name='service_edit'),
]
