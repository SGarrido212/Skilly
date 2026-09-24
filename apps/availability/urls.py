from django.urls import path
from . import views

app_name = 'availability'

urlpatterns = [
    path('manage/', views.availability_manage_view, name='manage'),
    path('delete/<int:pk>/', views.slot_delete_view, name='delete'),
]
