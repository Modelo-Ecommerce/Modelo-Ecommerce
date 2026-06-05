# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad Pedido y sus reglas
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, List
from datetime import date

# ── Reglas de dominio ─────────────────────────────────────────
MIN_ORDER_AMOUNT  = 60_000
MIN_CART_QUANTITY = 3

# ── Flujo de transiciones válidas ─────────────────────────────
TRANSICIONES_VALIDAS = {
    "pending":    "processing",
    "processing": "shipped",
    "shipped":    "delivered",
}

# ── Estados no actualizables ──────────────────────────────────
ESTADOS_NO_ACTUALIZABLES = {"cancelled", "failed"}


# ── Excepciones de dominio ────────────────────────────────────
class MinimumOrderAmountException(ValueError):
    def __init__(self):
        super().__init__(
            "El valor mínimo de un pedido es $60.000 COP (MIN_ORDER_AMOUNT)."
        )

class MinimumQuantityException(ValueError):
    def __init__(self):
        super().__init__(
            f"El carrito debe tener al menos {MIN_CART_QUANTITY} unidades totales."
        )

class PaymentGatewayException(Exception):
    def __init__(self):
        super().__init__(
            "Error al procesar el pago con la pasarela. Intente nuevamente."
        )

class OrderNotCancellableException(ValueError):
    def __init__(self, current_status: str):
        super().__init__(
            f"Solo los pedidos en estado pending pueden cancelarse. "
            f"Estado actual: {current_status}."
        )

class InvalidStatusTransitionException(ValueError):
    def __init__(self, current_status: str, new_status: str):
        super().__init__(
            f"No se puede cambiar de {current_status} a {new_status}. "
            f"Transiciones válidas: pending → processing → shipped → delivered."
        )

class OrderNotUpdatableException(ValueError):
    def __init__(self, current_status: str):
        super().__init__(
            f"El pedido en estado {current_status} no puede ser actualizado."
        )


# ── Schema de ENTRADA: Dirección de envío ────────────────────
class DireccionEnvio(BaseModel):
    street:     str = Field(..., description="Calle o carrera")
    city:       str = Field(..., description="Ciudad")
    department: str = Field(..., description="Departamento")
    postalCode: str = Field(..., description="Código postal")


# ── Schema de ENTRADA: Crear pedido ──────────────────────────
class PedidoCreate(BaseModel):
    userId:          int            = Field(..., description="ID del usuario")
    cartId:          int            = Field(..., description="ID del carrito")
    shippingAddress: DireccionEnvio
    paymentMethod:   str            = Field(..., description="wompi_card | wompi_pse | wompi_nequi")

    @field_validator("paymentMethod")
    @classmethod
    def metodo_valido(cls, v):
        metodos = {"wompi_card", "wompi_pse", "wompi_nequi"}
        if v not in metodos:
            raise ValueError(f"Método de pago inválido. Use: {', '.join(metodos)}")
        return v


# ── Schema de ENTRADA: Actualizar estado ─────────────────────
class PedidoStatusUpdate(BaseModel):
    status: str = Field(..., description="processing | shipped | delivered")

    @field_validator("status")
    @classmethod
    def estado_valido(cls, v):
        estados = {"processing", "shipped", "delivered"}
        if v not in estados:
            raise ValueError(
                f"Estado inválido. Use: {', '.join(estados)}"
            )
        return v


# ── Schemas de datos ──────────────────────────────────────────
class PagoData(BaseModel):
    paymentId: int
    status:    str

class PedidoItemData(BaseModel):
    productId:   int
    productName: str
    quantity:    int
    unitPrice:   float
    subtotal:    float

class StockRestoradoData(BaseModel):
    productId:        int
    productName:      str
    quantityRestored: int
    currentStock:     int

class PedidoData(BaseModel):
    orderId:    int
    userId:     int
    status:     str
    total:      float
    paymentUrl: str
    createdAt:  str
    items:      List[PedidoItemData]

class PedidoDetalleData(BaseModel):
    orderId:         int
    userId:          int
    status:          str
    total:           float
    payment:         PagoData
    shippingAddress: DireccionEnvio
    items:           List[PedidoItemData]
    createdAt:       str

class PedidoCancelData(BaseModel):
    orderId:       int
    status:        str
    cancelledAt:   str
    stockRestored: List[StockRestoradoData]

class PedidoStatusData(BaseModel):
    orderId:        int
    previousStatus: str
    newStatus:      str
    updatedAt:      str

class PedidoResponse(BaseModel):
    success:    bool
    statusCode: int
    message:    str
    data:       Optional[Any] = None


# ── Modelo interno: ítem del pedido ──────────────────────────
class PedidoItem:
    def __init__(self, product_id: int, product_name: str,
                 quantity: int, unit_price: float):
        self.product_id   = product_id
        self.product_name = product_name
        self.quantity     = quantity
        self.unit_price   = unit_price

    @property
    def subtotal(self) -> float:
        return self.unit_price * self.quantity

    def to_response(self) -> dict:
        return {
            "productId":   self.product_id,
            "productName": self.product_name,
            "quantity":    self.quantity,
            "unitPrice":   self.unit_price,
            "subtotal":    self.subtotal,
        }


# ── Modelo interno: pedido ────────────────────────────────────
class Pedido:
    def __init__(self, order_id: int, user_id: int,
                 items: list, payment_url: str,
                 shipping_address: dict = None):
        self.order_id         = order_id
        self.user_id          = user_id
        self.items            = items
        self.payment_url      = payment_url
        self.shipping_address = shipping_address or {}
        self.status           = "pending"
        self.createdAt        = str(date.today())
        self.cancelledAt      = None
        self.updatedAt        = None
        self.payment_id       = order_id * 10 + 5
        self.payment_status   = "approved"

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)

    def cancelar(self) -> None:
        if self.status != "pending":
            raise OrderNotCancellableException(self.status)
        self.status      = "cancelled"
        self.cancelledAt = str(date.today())

    def actualizar_estado(self, new_status: str) -> str:
        """
        Regla de dominio: valida la transición y actualiza el estado.
        Retorna el estado anterior.
        """
        if self.status in ESTADOS_NO_ACTUALIZABLES:
            raise OrderNotUpdatableException(self.status)

        estado_esperado = TRANSICIONES_VALIDAS.get(self.status)
        if new_status != estado_esperado:
            raise InvalidStatusTransitionException(self.status, new_status)

        previous = self.status
        self.status    = new_status
        self.updatedAt = str(date.today())
        return previous

    def marcar_fallido(self):
        self.status         = "failed"
        self.payment_status = "failed"

    def to_response(self) -> dict:
        return {
            "orderId":    self.order_id,
            "userId":     self.user_id,
            "status":     self.status,
            "total":      self.total,
            "paymentUrl": self.payment_url,
            "createdAt":  self.createdAt,
            "items":      [item.to_response() for item in self.items],
        }

    def to_detalle(self) -> dict:
        return {
            "orderId":         self.order_id,
            "userId":          self.user_id,
            "status":          self.status,
            "total":           self.total,
            "payment":         {"paymentId": self.payment_id,
                                "status":    self.payment_status},
            "shippingAddress": self.shipping_address,
            "items":           [item.to_response() for item in self.items],
            "createdAt":       self.createdAt,
        }