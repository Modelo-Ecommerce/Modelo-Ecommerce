# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad Carrito y sus reglas
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, List

# ── Regla de dominio: límite de ítems por carrito ────────────
MAX_ITEMS_PER_CART = 20


# ── Excepciones de dominio ────────────────────────────────────
class InsufficientStockException(ValueError):
    def __init__(self, product_name: str, stock: int):
        super().__init__(
            f"El producto {product_name} solo tiene {stock} unidad(es) disponible(s)."
        )


class ProductDiscontinuedException(ValueError):
    def __init__(self):
        super().__init__(
            "El producto está descontinuado y no puede agregarse al carrito."
        )


class CartItemLimitExceededException(ValueError):
    def __init__(self):
        super().__init__(
            f"El carrito no puede tener más de {MAX_ITEMS_PER_CART} ítems distintos."
        )


# ── Schema de ENTRADA: Agregar ítem al carrito ───────────────
class CarritoItemAdd(BaseModel):
    userId:    int = Field(..., description="ID del usuario")
    productId: int = Field(..., description="ID del producto")
    quantity:  int = Field(..., ge=1, description="Cantidad (mínimo 1)")


# ── Schema de datos de un ítem en el carrito ─────────────────
class CarritoItemData(BaseModel):
    itemId:      int
    productId:   int
    productName: str
    unitPrice:   float
    quantity:    int
    subtotal:    float


# ── Schema de datos del carrito en la respuesta ──────────────
class CarritoData(BaseModel):
    cartId:  int
    userId:  int
    items:   List[CarritoItemData]
    total:   float


# ── Schema de SALIDA: Respuesta estándar ─────────────────────
class CarritoResponse(BaseModel):
    success:    bool
    statusCode: int
    message:    str
    data:       Optional[Any] = None


# ── Modelo interno: ítem del carrito ─────────────────────────
class CarritoItem:
    def __init__(self, item_id: int, product_id: int,
                 product_name: str, unit_price: float, quantity: int):
        self.item_id      = item_id
        self.product_id   = product_id
        self.product_name = product_name
        self.unit_price   = unit_price
        self.quantity     = quantity

    @property
    def subtotal(self) -> float:
        return self.unit_price * self.quantity

    def to_response(self) -> dict:
        return {
            "itemId":      self.item_id,
            "productId":   self.product_id,
            "productName": self.product_name,
            "unitPrice":   self.unit_price,
            "quantity":    self.quantity,
            "subtotal":    self.subtotal,
        }


# ── Modelo interno: carrito ───────────────────────────────────
class Carrito:
    def __init__(self, cart_id: int, user_id: int):
        self.cart_id  = cart_id
        self.user_id  = user_id
        self.items:   dict[int, CarritoItem] = {}  # productId → CarritoItem
        self._next_item_id: int = 1

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items.values())

    def agregar_item(self, product_id: int, product_name: str,
                     unit_price: float, quantity: int) -> None:
        """
        Regla de dominio: si el producto ya existe en el carrito,
        suma la cantidad al ítem existente. No crea duplicados.
        """
        if product_id in self.items:
            self.items[product_id].quantity += quantity
        else:
            # Regla de dominio: no superar MAX_ITEMS_PER_CART
            if len(self.items) >= MAX_ITEMS_PER_CART:
                raise CartItemLimitExceededException()
            self.items[product_id] = CarritoItem(
                item_id      = self._next_item_id,
                product_id   = product_id,
                product_name = product_name,
                unit_price   = unit_price,
                quantity     = quantity,
            )
            self._next_item_id += 1

    def to_response(self) -> dict:
        return {
            "cartId":  self.cart_id,
            "userId":  self.user_id,
            "items":   [item.to_response() for item in self.items.values()],
            "total":   self.total,
        }