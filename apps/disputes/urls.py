from django.urls import path
from . import views

app_name = 'disputes'

urlpatterns = [
    path('create/<int:booking_id>/', views.dispute_create_view, name='create'),
]
