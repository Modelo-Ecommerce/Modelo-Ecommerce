# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad Producto y sus reglas
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from datetime import date

# ── Regla de dominio: precio mínimo ──────────────────────────
MIN_PRODUCT_PRICE = 10_000  # $10.000 COP


# ── Excepción de dominio ──────────────────────────────────────
class PriceBelowMinimumException(ValueError):
    def __init__(self):
        super().__init__(
            f"El precio mínimo permitido es $10.000 COP (MIN_PRODUCT_PRICE)."
        )


# ── Schema de ENTRADA: Crear producto ────────────────────────
class ProductoCreate(BaseModel):
    name:        str   = Field(..., min_length=3, description="Nombre del producto")
    description: str   = Field(..., description="Descripción del producto")
    price:       float = Field(..., description="Precio en COP (mínimo $10.000)")
    stock:       int   = Field(..., ge=0, description="Stock inicial (>= 0)")
    categoryId:  int   = Field(..., description="ID de la categoría")

    # ── REGLA DE DOMINIO: precio mínimo ──────────────────────
    @field_validator("price")
    @classmethod
    def precio_minimo(cls, v):
        if v < MIN_PRODUCT_PRICE:
            raise PriceBelowMinimumException()
        return v


# ── Schema de datos del producto en la respuesta ─────────────
class ProductoData(BaseModel):
    id:          int
    name:        str
    price:       float
    stock:       int
    categoryId:  int
    status:      str = "active"
    createdAt:   str

    class Config:
        from_attributes = True


# ── Schema de SALIDA: Respuesta estándar ─────────────────────
class ProductoResponse(BaseModel):
    success:    bool
    statusCode: int
    message:    str
    data:       Optional[Any] = None


# ── Modelo interno del dominio (la "entidad real") ────────────
class Producto:
    def __init__(self, id: int, name: str, description: str,
                 price: float, stock: int, categoryId: int):
        self.id          = id
        self.name        = name
        self.description = description
        self.price       = price
        self.stock       = stock
        self.categoryId  = categoryId
        self.status      = "active"  # siempre activo por defecto
        self.createdAt   = str(date.today())

    def esta_activo(self) -> bool:
        return self.status == "active"

    def to_response(self) -> dict:
        return {
            "id":         self.id,
            "name":       self.name,
            "price":      self.price,
            "stock":      self.stock,
            "categoryId": self.categoryId,
            "status":     self.status,
            "createdAt":  self.createdAt,
        }