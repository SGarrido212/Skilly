from django.urls import path
from . import views

app_name = 'escrow_payments'

urlpatterns = [
    path('checkout/<int:booking_id>/', views.checkout_view, name='checkout'),
    path('webpay/init/<int:booking_id>/', views.webpay_init_view, name='webpay_init'),
    path('webpay/commit/', views.webpay_commit_view, name='webpay_commit'),
    path('success/<int:transaction_id>/', views.payment_success_view, name='payment_success'),
    path('failed/<int:transaction_id>/', views.payment_failed_view, name='payment_failed'),
]
