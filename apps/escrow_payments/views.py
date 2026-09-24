# -- VISTAS DE PAGO EN CUSTODIA Y WEBPAY PLUS TRANSBANK --
import time
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_type import IntegrationType

from bookings.models import Booking
from .models import PaymentTransaction

def get_webpay_transaction():
    # -- CONFIGURACIÓN DE CREDENCIALES DE PRUEBA WEBPAY PLUS --
    options = WebpayOptions(
        commerce_code=IntegrationCommerceCodes.WEBPAY_PLUS,
        api_key=IntegrationApiKeys.WEBPAY,
        integration_type=IntegrationType.TEST
    )
    return Transaction(options=options)


@login_required
def checkout_view(request, booking_id):
    # -- PANTALLA DE RESUMEN Y CHECKOUT DE PAGO EN CUSTODIA --
    booking = get_object_or_404(Booking, pk=booking_id, organization=request.user)

    total_amount = booking.service.price
    fee_percentage = Decimal('15.00')
    fee_amount = total_amount * (fee_percentage / Decimal('100.00'))
    pro_net = total_amount - fee_amount

    context = {
        'booking': booking,
        'total_amount': total_amount,
        'fee_percentage': fee_percentage,
        'fee_amount': fee_amount,
        'pro_net': pro_net,
    }
    return render(request, 'escrow_payments/caja_pago.html', context)


@login_required
def webpay_init_view(request, booking_id):
    # -- INICIALIZACIÓN DE TRANSACCIÓN WEBPAY PLUS Y CONEXIÓN A TRANSBANK --
    booking = get_object_or_404(Booking, pk=booking_id, organization=request.user)

    if booking.status in [Booking.STATUS_FINALIZADO, Booking.STATUS_CANCELADO]:
        messages.error(request, "Esta reserva no puede ser pagada en este estado.")
        return redirect('bookings:detail', pk=booking.id)

    total_amount = booking.service.price
    amount_int = int(total_amount)

    buy_order = f"ORD-{booking.id}-{int(time.time())}"
    session_id = f"SESS-{request.user.id}-{int(time.time())}"
    return_url = request.build_absolute_uri(reverse('escrow_payments:webpay_commit'))

    transaction, created = PaymentTransaction.objects.get_or_create(
        booking=booking,
        defaults={
            'total_amount': total_amount,
            'buy_order': buy_order,
            'session_id': session_id,
            'escrow_status': PaymentTransaction.STATUS_INICIADA,
            'payment_gateway': 'Webpay Plus Transbank (Sandbox)'
        }
    )
    if not created:
        transaction.buy_order = buy_order
        transaction.session_id = session_id
        transaction.escrow_status = PaymentTransaction.STATUS_INICIADA
        transaction.save()

    tx = get_webpay_transaction()
    try:
        response = tx.create(
            buy_order=buy_order,
            session_id=session_id,
            amount=amount_int,
            return_url=return_url
        )

        token = response.get('token') if isinstance(response, dict) else getattr(response, 'token', None)
        url = response.get('url') if isinstance(response, dict) else getattr(response, 'url', None)

        transaction.token = token
        transaction.save()

        context = {
            'webpay_url': url,
            'token_ws': token,
            'booking': booking,
            'total_amount': total_amount,
        }
        return render(request, 'escrow_payments/redireccion_webpay.html', context)

    except Exception as e:
        messages.error(request, f"Error al comunicar con pasarela Webpay Plus Transbank: {str(e)}")
        return redirect('escrow_payments:checkout', booking_id=booking.id)


@csrf_exempt
def webpay_commit_view(request):
    # -- CONFIRMACIÓN DE TRANSACCIÓN WEBPAY PLUS Y MANEJO DE ANULACIÓN --
    token_ws = request.POST.get('token_ws') or request.GET.get('token_ws')
    tbk_token = request.POST.get('TBK_TOKEN') or request.GET.get('TBK_TOKEN')
    tbk_buy_order = request.POST.get('TBK_ORDEN_COMPRA') or request.GET.get('TBK_ORDEN_COMPRA')

    if tbk_token or not token_ws:
        search_token = tbk_token or token_ws
        transaction = None
        if search_token:
            transaction = PaymentTransaction.objects.filter(token=search_token).first()
        elif tbk_buy_order:
            transaction = PaymentTransaction.objects.filter(buy_order=tbk_buy_order).first()

        if transaction:
            transaction.escrow_status = PaymentTransaction.STATUS_RECHAZADA
            transaction.save()
            return redirect('escrow_payments:payment_failed', transaction_id=transaction.id)
        else:
            messages.warning(request, "El pago fue anulado por el usuario en el formulario de Webpay Plus.")
            return redirect('services:marketplace')

    transaction = get_object_or_404(PaymentTransaction, token=token_ws)
    tx = get_webpay_transaction()

    try:
        response = tx.commit(token_ws)

        res_code = response.get('response_code') if isinstance(response, dict) else getattr(response, 'response_code', -1)
        auth_code = response.get('authorization_code') if isinstance(response, dict) else getattr(response, 'authorization_code', None)
        pay_type = response.get('payment_type_code') if isinstance(response, dict) else getattr(response, 'payment_type_code', None)
        shares = response.get('shares_number') if isinstance(response, dict) else getattr(response, 'shares_number', 0)

        transaction.transbank_response_code = res_code
        transaction.authorization_code = auth_code
        transaction.payment_type_code = pay_type
        transaction.shares_number = shares or 0

        if res_code == 0:
            transaction.escrow_status = PaymentTransaction.STATUS_RETENIDO
            transaction.save()

            booking = transaction.booking
            booking.status = Booking.STATUS_PAGADO_EN_CUSTODIA
            booking.paid_at = timezone.now()
            booking.save()

            if booking.timeslot:
                booking.timeslot.mark_booked()

            return redirect('escrow_payments:payment_success', transaction_id=transaction.id)
        else:
            transaction.escrow_status = PaymentTransaction.STATUS_RECHAZADA
            transaction.save()
            return redirect('escrow_payments:payment_failed', transaction_id=transaction.id)

    except Exception as e:
        transaction.escrow_status = PaymentTransaction.STATUS_RECHAZADA
        transaction.save()
        messages.error(request, f"Ocurrió un error al confirmar la transacción de Webpay: {str(e)}")
        return redirect('escrow_payments:payment_failed', transaction_id=transaction.id)


def payment_success_view(request, transaction_id):
    # -- VISTA DE PAGO EXITOSO Y COMPROBANTE DE CUSTODIA --
    transaction = get_object_or_404(PaymentTransaction, pk=transaction_id)
    booking = transaction.booking

    context = {
        'transaction': transaction,
        'booking': booking,
    }
    return render(request, 'escrow_payments/pago_exitoso.html', context)


def payment_failed_view(request, transaction_id):
    # -- VISTA DE PAGO RECHAZADO O ANULADO --
    transaction = get_object_or_404(PaymentTransaction, pk=transaction_id)
    booking = transaction.booking

    context = {
        'transaction': transaction,
        'booking': booking,
    }
    return render(request, 'escrow_payments/pago_fallido.html', context)
