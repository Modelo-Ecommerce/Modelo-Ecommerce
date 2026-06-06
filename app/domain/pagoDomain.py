# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad Pago y sus reglas
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from datetime import date, datetime


# ── Excepciones de dominio ────────────────────────────────────
class PaymentAmountMismatchException(ValueError):
    def __init__(self, amount_sent: float, order_total: float):
        super().__init__(
            f"El monto enviado es ${amount_sent:,.0f} pero el total del pedido "
            f"es ${order_total:,.0f}."
        )

class PaymentAlreadyApprovedException(ValueError):
    def __init__(self):
        super().__init__("El pedido ya tiene un pago aprobado.")

class PaymentGatewayException(Exception):
    def __init__(self, detail: str = "Error en la pasarela de pago."):
        super().__init__(detail)

class InvalidWebhookSignatureException(Exception):
    def __init__(self):
        super().__init__("Firma del webhook inválida. La solicitud no proviene de Wompi.")


# ── Schema de ENTRADA: Método de pago ────────────────────────
class MetodoPago(BaseModel):
    type:  str = Field(..., description="CARD | PSE | NEQUI")
    token: str = Field(..., description="Token del método de pago")

    @field_validator("type")
    @classmethod
    def tipo_valido(cls, v):
        tipos = {"CARD", "PSE", "NEQUI"}
        if v.upper() not in tipos:
            raise ValueError(f"Tipo inválido. Use: {', '.join(tipos)}")
        return v.upper()


# ── Schema de ENTRADA: Iniciar pago ──────────────────────────
class PagoCreate(BaseModel):
    orderId:       int        = Field(..., description="ID del pedido")
    userId:        int        = Field(..., description="ID del usuario")
    amount:        float      = Field(..., description="Monto en COP")
    currency:      str        = Field("COP", description="Moneda")
    paymentMethod: MetodoPago
    customerEmail: str        = Field(..., description="Correo del cliente")
    redirectUrl:   str        = Field(..., description="URL de redirección")

    @field_validator("currency")
    @classmethod
    def moneda_valida(cls, v):
        if v.upper() != "COP":
            raise ValueError("Solo se acepta COP.")
        return v.upper()

    @field_validator("customerEmail")
    @classmethod
    def email_valido(cls, v):
        if "@" not in v or "." not in v:
            raise ValueError("El correo no es válido.")
        return v


# ── Schema de ENTRADA: Actualizar estado pago (PATCH) ────────
class PagoStatusUpdate(BaseModel):
    status: str = Field(..., description="approved | declined | voided")

    @field_validator("status")
    @classmethod
    def estado_valido(cls, v):
        estados = {"approved", "declined", "voided"}
        if v not in estados:
            raise ValueError(f"Estado inválido. Use: {', '.join(estados)}")
        return v


# ── Schema de ENTRADA: Webhook Wompi ─────────────────────────
class WompiTransaccion(BaseModel):
    id:                  str   = Field(..., description="wompiTransactionId")
    status:              str   = Field(..., description="APPROVED | DECLINED | VOIDED")
    amount_in_cents:     int   = Field(..., description="Monto en centavos")
    reference:           str   = Field(..., description="orderId del pedido")
    payment_method_type: str   = Field("CARD")

class WompiData(BaseModel):
    transaction: WompiTransaccion

class WebhookWompi(BaseModel):
    event:   str      = Field(..., description="transaction.updated")
    data:    WompiData
    sent_at: str      = Field(..., description="Timestamp ISO 8601")


# ── Schema de datos del webhook procesado ────────────────────
class WebhookResultData(BaseModel):
    paymentId:       int
    newStatus:       str
    orderId:         int
    orderNewStatus:  str
    stockRestored:   bool


# ── Schemas de respuesta ──────────────────────────────────────
class PagoData(BaseModel):
    paymentId:          int
    orderId:            int
    wompiTransactionId: str
    status:             str
    amount:             float
    currency:           str
    paymentUrl:         str
    createdAt:          str

class PagoDetalleData(BaseModel):
    paymentId:          int
    orderId:            int
    wompiTransactionId: str
    status:             str
    amount:             float
    currency:           str
    paymentMethodType:  str
    createdAt:          str
    approvedAt:         Optional[str] = None

class PagoResponse(BaseModel):
    success:    bool
    statusCode: int
    message:    str
    data:       Optional[Any] = None


# ── Modelo interno: pago ──────────────────────────────────────
class Pago:
    def __init__(self, payment_id: int, order_id: int,
                 user_id: int, amount: float, currency: str,
                 wompi_transaction_id: str, payment_url: str,
                 payment_method_type: str = "CARD"):
        self.payment_id           = payment_id
        self.order_id             = order_id
        self.user_id              = user_id
        self.amount               = amount
        self.currency             = currency
        self.wompi_transaction_id = wompi_transaction_id
        self.payment_url          = payment_url
        self.payment_method_type  = payment_method_type
        self.status               = "pending"
        self.createdAt            = str(date.today())
        self.approvedAt           = None

    def aprobar(self) -> None:
        self.status     = "approved"
        self.approvedAt = datetime.now().isoformat()

    def rechazar(self) -> None:
        self.status = "declined"

    def anular(self) -> None:
        self.status = "voided"

    def actualizar_estado(self, new_status: str) -> None:
        if new_status == "approved":
            self.aprobar()
        elif new_status == "declined":
            self.rechazar()
        elif new_status == "voided":
            self.anular()

    def to_response(self) -> dict:
        return {
            "paymentId":          self.payment_id,
            "orderId":            self.order_id,
            "wompiTransactionId": self.wompi_transaction_id,
            "status":             self.status,
            "amount":             self.amount,
            "currency":           self.currency,
            "paymentUrl":         self.payment_url,
            "createdAt":          self.createdAt,
        }

    def to_detalle(self) -> dict:
        return {
            "paymentId":          self.payment_id,
            "orderId":            self.order_id,
            "wompiTransactionId": self.wompi_transaction_id,
            "status":             self.status,
            "amount":             self.amount,
            "currency":           self.currency,
            "paymentMethodType":  self.payment_method_type,
            "createdAt":          self.createdAt,
            "approvedAt":         self.approvedAt,
        }