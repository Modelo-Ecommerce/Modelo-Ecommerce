# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad Producto y sus reglas
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any, List
from datetime import date

# ── Regla de dominio: precio mínimo ──────────────────────────
MIN_PRODUCT_PRICE = 10_000  # $10.000 COP


# ── Excepciones de dominio ────────────────────────────────────
class PriceBelowMinimumException(ValueError):
    def __init__(self):
        super().__init__(
            "El precio mínimo permitido es $10.000 COP (MIN_PRODUCT_PRICE)."
        )


class ProductHasActiveOrdersException(ValueError):
    def __init__(self, producto_id: int):
        super().__init__(
            f"El producto con id {producto_id} está asociado a pedidos "
            "en estado pending o processing."
        )


# ── Schema de ENTRADA: Crear producto ────────────────────────
class ProductoCreate(BaseModel):
    name:        str   = Field(..., min_length=3, description="Nombre del producto")
    description: str   = Field(..., description="Descripción del producto")
    price:       float = Field(..., description="Precio en COP (mínimo $10.000)")
    stock:       int   = Field(..., ge=0, description="Stock inicial (>= 0)")
    categoryId:  int   = Field(..., description="ID de la categoría")

    @field_validator("price")
    @classmethod
    def precio_minimo(cls, v):
        if v < MIN_PRODUCT_PRICE:
            raise PriceBelowMinimumException()
        return v


# ── Schema de ENTRADA: Actualizar producto ────────────────────
class ProductoUpdate(BaseModel):
    name:        Optional[str]   = Field(None, min_length=3)
    description: Optional[str]   = Field(None)
    price:       Optional[float] = Field(None, description="Mínimo $10.000 COP")
    categoryId:  Optional[int]   = Field(None)
    # stock NO se incluye — se actualiza solo vía módulo Inventario

    @field_validator("price")
    @classmethod
    def precio_minimo(cls, v):
        if v is None:
            return v
        if v < MIN_PRODUCT_PRICE:
            raise PriceBelowMinimumException()
        return v


# ── Schema de datos del producto en la respuesta (admin) ─────
class ProductoData(BaseModel):
    id:         int
    name:       str
    price:      float
    stock:      int
    categoryId: int
    status:     str = "active"
    createdAt:  str

    class Config:
        from_attributes = True


# ── Schema de datos del producto en el catálogo público ──────
class ProductoCatalogoItem(BaseModel):
    id:         int
    name:       str
    price:      float
    stock:      int
    categoryId: int
    imageUrl:   str

    class Config:
        from_attributes = True


# ── Schema de datos del producto detalle público ─────────────
class ProductoDetalleData(BaseModel):
    id:          int
    name:        str
    description: str
    price:       float
    stock:       int
    categoryId:  int
    imageUrl:    str
    createdAt:   str

    class Config:
        from_attributes = True


# ── Schema de paginación ──────────────────────────────────────
class Pagination(BaseModel):
    total:      int
    page:       int
    limit:      int
    totalPages: int


# ── Schema de catálogo paginado ───────────────────────────────
class CatalogoData(BaseModel):
    products:   List[ProductoCatalogoItem]
    pagination: Pagination


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
        self.status      = "active"
        self.createdAt   = str(date.today())

    def esta_activo(self) -> bool:
        return self.status == "active"

    def discontinuar(self):
        """Soft-delete: marca el producto como discontinuado."""
        self.status = "discontinued"

    def get_image_url(self) -> str:
        return f"https://cdn.ecommerce.com/productos/{self.id}.jpg"

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

    def to_catalogo_item(self) -> dict:
        return {
            "id":         self.id,
            "name":       self.name,
            "price":      self.price,
            "stock":      self.stock,
            "categoryId": self.categoryId,
            "imageUrl":   self.get_image_url(),
        }

    def to_detalle(self) -> dict:
        return {
            "id":          self.id,
            "name":        self.name,
            "description": self.description,
            "price":       self.price,
            "stock":       self.stock,
            "categoryId":  self.categoryId,
            "imageUrl":    self.get_image_url(),
            "createdAt":   self.createdAt,
        }