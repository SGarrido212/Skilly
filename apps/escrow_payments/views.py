# -- VISTAS DE PAGO EN CUSTODIA Y WEBPAY PLUS TRANSBANK --
import os
import time
import logging
from decimal import Decimal
from django.conf import settings
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

logger = logging.getLogger('skilly.transbank')


def get_webpay_transaction():
    """
    Configura el cliente Webpay Plus de Transbank:
    - En modo TEST: usa el código de comercio y API key de Sandbox oficial de Transbank.
    - En modo LIVE/PRODUCCIÓN: usa TRANSBANK_COMMERCE_CODE y TRANSBANK_API_KEY desde variables de entorno.
    """
    env_mode = os.environ.get('TRANSBANK_ENVIRONMENT', 'TEST').upper()

    if env_mode in ['LIVE', 'PROD', 'PRODUCTION']:
        commerce_code = os.environ.get('TRANSBANK_COMMERCE_CODE')
        api_key = os.environ.get('TRANSBANK_API_KEY')
        integration_type = IntegrationType.LIVE
        if not commerce_code or not api_key:
            logger.error("Transbank configurado en PRODUCCIÓN pero faltan TRANSBANK_COMMERCE_CODE o TRANSBANK_API_KEY")
    else:
        # Credenciales de integración oficiales (Sandbox)
        commerce_code = os.environ.get('TRANSBANK_COMMERCE_CODE') or IntegrationCommerceCodes.WEBPAY_PLUS
        api_key = os.environ.get('TRANSBANK_API_KEY') or IntegrationApiKeys.WEBPAY
        integration_type = IntegrationType.TEST

    options = WebpayOptions(
        commerce_code=commerce_code,
        api_key=api_key,
        integration_type=integration_type
    )
    return Transaction(options=options)


@login_required
def checkout_view(request, booking_id):
    """Pantalla de resumen y checkout de pago en custodia para la organización."""
    booking = get_object_or_404(Booking, pk=booking_id, organization=request.user)

    from backoffice.models import PlatformSetting
    total_amount = booking.service.price
    fee_percentage = PlatformSetting.get_take_rate()
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
    """
    Inicializa la transacción en Webpay Plus de Transbank y redirige al formulario de pago.
    En Render asegura que return_url use siempre HTTPS para evitar pérdidas de token POST.
    """
    booking = get_object_or_404(Booking, pk=booking_id, organization=request.user)

    if booking.status in [Booking.STATUS_FINALIZADO, Booking.STATUS_CANCELADO]:
        messages.error(request, "Esta reserva no puede ser pagada en este estado.")
        return redirect('bookings:detail', pk=booking.id)

    total_amount = booking.service.price
    amount_int = int(total_amount)

    if amount_int <= 0:
        messages.error(request, "El monto del servicio debe ser mayor a $0 para pagar con Webpay.")
        return redirect('bookings:detail', pk=booking.id)

    buy_order = f"ORD-{booking.id}-{int(time.time())}"
    session_id = f"SESS-{request.user.id}-{int(time.time())}"

    # Construir URL de retorno absoluta
    return_url = request.build_absolute_uri(reverse('escrow_payments:webpay_commit'))

    # EN RENDER: El proxy inverso termina SSL. Forzar https:// para que Transbank
    # nunca redirija a http:// (lo que causaría un 301 y pérdida del token POST).
    if not settings.DEBUG and return_url.startswith('http://'):
        return_url = return_url.replace('http://', 'https://', 1)

    is_live = os.environ.get('TRANSBANK_ENVIRONMENT', 'TEST').upper() in ['LIVE', 'PROD', 'PRODUCTION']
    gateway_label = 'Webpay Plus Transbank (Producción)' if is_live else 'Webpay Plus Transbank (Sandbox)'

    from backoffice.models import PlatformSetting
    transaction, created = PaymentTransaction.objects.get_or_create(
        booking=booking,
        defaults={
            'total_amount': total_amount,
            'skilly_fee_percentage': PlatformSetting.get_take_rate(),
            'buy_order': buy_order,
            'session_id': session_id,
            'escrow_status': PaymentTransaction.STATUS_INICIADA,
            'payment_gateway': gateway_label
        }
    )
    if not created:
        transaction.buy_order = buy_order
        transaction.session_id = session_id
        transaction.escrow_status = PaymentTransaction.STATUS_INICIADA
        transaction.payment_gateway = gateway_label
        transaction.save()

    tx = get_webpay_transaction()
    try:
        logger.info("Iniciando Transbank Webpay | BuyOrder: %s | Monto: %s | Return: %s", buy_order, amount_int, return_url)
        response = tx.create(
            buy_order=buy_order,
            session_id=session_id,
            amount=amount_int,
            return_url=return_url
        )

        token = response.get('token') if isinstance(response, dict) else getattr(response, 'token', None)
        url = response.get('url') if isinstance(response, dict) else getattr(response, 'url', None)

        if not token or not url:
            raise ValueError(f"Respuesta inesperada de Transbank: {response}")

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
        logger.exception("Error al conectar con Webpay Plus: %s", str(e))
        messages.error(request, f"Error al comunicar con pasarela Webpay Plus Transbank: {str(e)}")
        return redirect('escrow_payments:checkout', booking_id=booking.id)


@csrf_exempt
def webpay_commit_view(request):
    """
    Recibe la respuesta de Transbank tras la interacción en Webpay.
    Maneja confirmaciones exitosas, anulaciones por el usuario y expiraciones.
    """
    token_ws = request.POST.get('token_ws') or request.GET.get('token_ws')
    tbk_token = request.POST.get('TBK_TOKEN') or request.GET.get('TBK_TOKEN')
    tbk_buy_order = request.POST.get('TBK_ORDEN_COMPRA') or request.GET.get('TBK_ORDEN_COMPRA')

    logger.info("Callback Webpay Commit | token_ws: %s | tbk_token: %s | tbk_buy_order: %s", bool(token_ws), bool(tbk_token), tbk_buy_order)

    # Caso 1: Transacción anulada por el usuario en el formulario de Webpay
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
            logger.warning("Pago anulado por usuario | Transacción: %s", transaction.transaction_id)
            return redirect('escrow_payments:payment_failed', transaction_id=transaction.id)
        else:
            messages.warning(request, "El pago fue anulado por el usuario en el formulario de Webpay Plus.")
            return redirect('services:marketplace')

    # Caso 2: Transacción completada en Webpay -> Confirmar con commit
    transaction = get_object_or_404(PaymentTransaction, token=token_ws)

    # Si la transacción ya estaba retenida/confirmada (ej: recarga de página), redirigir al éxito
    if transaction.escrow_status == PaymentTransaction.STATUS_RETENIDO:
        return redirect('escrow_payments:payment_success', transaction_id=transaction.id)

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

        # Código 0 indica éxito en Transbank Webpay Plus
        if res_code == 0:
            transaction.escrow_status = PaymentTransaction.STATUS_RETENIDO
            transaction.save()

            booking = transaction.booking
            booking.status = Booking.STATUS_PAGADO_EN_CUSTODIA
            booking.paid_at = timezone.now()
            booking.save()

            if booking.timeslot:
                booking.timeslot.mark_booked()

            logger.info("Transacción Webpay APROBADA y retenida en Escrow | ID: %s | Auth: %s", transaction.transaction_id, auth_code)
            return redirect('escrow_payments:payment_success', transaction_id=transaction.id)
        else:
            transaction.escrow_status = PaymentTransaction.STATUS_RECHAZADA
            transaction.save()
            logger.warning("Transacción Webpay RECHAZADA por emisor | Código: %s | ID: %s", res_code, transaction.transaction_id)
            return redirect('escrow_payments:payment_failed', transaction_id=transaction.id)

    except Exception as e:
        transaction.escrow_status = PaymentTransaction.STATUS_RECHAZADA
        transaction.save()
        logger.exception("Error al hacer commit en Webpay: %s", str(e))
        messages.error(request, f"Ocurrió un error al confirmar la transacción de Webpay: {str(e)}")
        return redirect('escrow_payments:payment_failed', transaction_id=transaction.id)


def payment_success_view(request, transaction_id):
    """Vista de pago exitoso y comprobante de custodia Escrow."""
    transaction = get_object_or_404(PaymentTransaction, pk=transaction_id)
    booking = transaction.booking

    context = {
        'transaction': transaction,
        'booking': booking,
    }
    return render(request, 'escrow_payments/pago_exitoso.html', context)


def payment_failed_view(request, transaction_id):
    """Vista de pago rechazado o anulado."""
    transaction = get_object_or_404(PaymentTransaction, pk=transaction_id)
    booking = transaction.booking

    context = {
        'transaction': transaction,
        'booking': booking,
    }
    return render(request, 'escrow_payments/pago_fallido.html', context)
