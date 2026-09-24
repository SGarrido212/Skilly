from django.db import models
from decimal import Decimal
import uuid

class PaymentTransaction(models.Model):
    STATUS_INICIADA = 'INICIADA'
    STATUS_RETENIDO = 'RETENIDO'
    STATUS_RECHAZADA = 'RECHAZADA'
    STATUS_LIBERADO = 'LIBERADO'
    STATUS_REEMBOLSADO = 'REEMBOLSADO'
    STATUS_CONGELADO = 'CONGELADO_POR_DISPUTA'

    ESCROW_STATUS_CHOICES = [
        (STATUS_INICIADA, 'Iniciada en Webpay'),
        (STATUS_RETENIDO, 'Retenido en Custodia Escrow'),
        (STATUS_RECHAZADA, 'Rechazada / Cancelada'),
        (STATUS_LIBERADO, 'Liberado a Profesional'),
        (STATUS_REEMBOLSADO, 'Reembolsado a Organización'),
        (STATUS_CONGELADO, 'Congelado por Disputa'),
    ]

    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='payment_transaction')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Total Transado")
    skilly_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=15.00, verbose_name="Comisión Skilly (%)")
    skilly_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Comisión Skilly ($)")
    net_professional_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Neto Profesional ($)")
    payment_gateway = models.CharField(max_length=50, default='Webpay Plus Transbank (Sandbox)', verbose_name="Pasarela de Pago")
    escrow_status = models.CharField(max_length=30, choices=ESCROW_STATUS_CHOICES, default=STATUS_INICIADA, verbose_name="Estado de Custodia")
    transaction_id = models.CharField(max_length=100, unique=True, verbose_name="ID de Transacción Interna")

    # Transbank Webpay Plus Integration Fields
    buy_order = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="Orden de Compra Webpay")
    session_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID de Sesión Webpay")
    token = models.CharField(max_length=255, blank=True, null=True, verbose_name="Token Webpay (token_ws)")
    transbank_response_code = models.IntegerField(blank=True, null=True, verbose_name="Código Respuesta Transbank")
    authorization_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código Autorización Transbank")
    payment_type_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="Tipo Pago Transbank (VN, VC, etc.)")
    shares_number = models.IntegerField(default=0, verbose_name="Número de Cuotas")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"SK-PAY-{uuid.uuid4().hex[:10].upper()}"
        if not self.skilly_fee_amount or not self.net_professional_amount:
            fee_decimal = Decimal(str(self.skilly_fee_percentage)) / Decimal('100.00')
            self.skilly_fee_amount = self.total_amount * fee_decimal
            self.net_professional_amount = self.total_amount - self.skilly_fee_amount
        super().save(*args, **kwargs)

    def release_to_professional(self):
        self.escrow_status = self.STATUS_LIBERADO
        self.save()

    def refund_to_organization(self):
        self.escrow_status = self.STATUS_REEMBOLSADO
        self.save()

    def freeze_for_dispute(self):
        self.escrow_status = self.STATUS_CONGELADO
        self.save()

    def __str__(self):
        return f"Transacción {self.transaction_id} - BuyOrder: {self.buy_order or 'N/A'} (${self.total_amount:,.0f})"
