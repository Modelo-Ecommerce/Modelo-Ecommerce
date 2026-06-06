# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad Inventario y sus reglas
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Any
from datetime import date

# ── Regla de dominio: umbral de stock bajo ────────────────────
LOW_STOCK_THRESHOLD = 5


# ── Excepciones de dominio ────────────────────────────────────
class InsufficientStockForOperationException(ValueError):
    def __init__(self, current_stock: int, quantity: int):
        super().__init__(
            f"El stock actual es {current_stock} y se intentó descontar "
            f"{quantity} unidades. El stock no puede ser negativo."
        )

class MissingOrderIdException(ValueError):
    def __init__(self):
        super().__init__(
            "El campo orderId es obligatorio cuando reason es purchase."
        )


# ── Schema de ENTRADA: Actualizar stock ──────────────────────
class InventarioUpdate(BaseModel):
    operation: str           = Field(..., description="increase | decrease")
    quantity:  int           = Field(..., gt=0, description="Cantidad > 0")
    reason:    str           = Field(..., description="purchase | return | restock")
    orderId:   Optional[int] = Field(None, description="Obligatorio si reason=purchase")

    @field_validator("operation")
    @classmethod
    def operacion_valida(cls, v):
        if v not in {"increase", "decrease"}:
            raise ValueError("La operación debe ser 'increase' o 'decrease'.")
        return v

    @field_validator("reason")
    @classmethod
    def razon_valida(cls, v):
        if v not in {"purchase", "return", "restock"}:
            raise ValueError("El reason debe ser 'purchase', 'return' o 'restock'.")
        return v

    @model_validator(mode="after")
    def validar_order_id(self):
        """Regla de dominio: orderId obligatorio si reason = purchase."""
        if self.reason == "purchase" and self.orderId is None:
            raise MissingOrderIdException()
        return self


# ── Schema de datos del inventario — consulta ────────────────
class InventarioData(BaseModel):
    productId:   int
    productName: str
    stock:       int
    isLowStock:  bool
    lastUpdated: str


# ── Schema de datos del inventario — actualización ───────────
class InventarioUpdateData(BaseModel):
    productId:       int
    productName:     str
    previousStock:   int
    quantityChanged: int
    currentStock:    int
    isLowStock:      bool
    updatedAt:       str


# ── Schema de movimiento de inventario ───────────────────────
class InventoryMovement(BaseModel):
    productId:  int
    operation:  str
    quantity:   int
    reason:     str
    orderId:    Optional[int]
    stockBefore: int
    stockAfter:  int
    createdAt:  str


# ── Schema de SALIDA: Respuesta estándar ─────────────────────
class InventarioResponse(BaseModel):
    success:    bool
    statusCode: int
    message:    str
    data:       Optional[Any] = None