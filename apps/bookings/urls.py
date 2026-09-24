from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('create/<int:service_id>/', views.booking_create_view, name='create'),
    path('<int:pk>/', views.booking_detail_view, name='detail'),
    path('<int:pk>/message/', views.booking_send_message_view, name='send_message'),
    path('<int:pk>/status/<str:new_status>/', views.booking_update_status_view, name='update_status'),
]
