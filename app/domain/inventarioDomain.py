# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad Inventario y sus reglas
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import Optional, Any
from datetime import date

# ── Regla de dominio: umbral de stock bajo ────────────────────
LOW_STOCK_THRESHOLD = 5  # configurable via .env


# ── Schema de datos del inventario en la respuesta ───────────
class InventarioData(BaseModel):
    productId:   int
    productName: str
    stock:       int
    isLowStock:  bool
    lastUpdated: str


# ── Schema de SALIDA: Respuesta estándar ─────────────────────
class InventarioResponse(BaseModel):
    success:    bool
    statusCode: int
    message:    str
    data:       Optional[Any] = None