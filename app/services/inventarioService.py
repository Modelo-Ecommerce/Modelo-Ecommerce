# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

import os
from datetime import date
from app.domain.inventarioDomain import (
    InventarioData, InventarioResponse, LOW_STOCK_THRESHOLD
)
from app.repositories.productoRepository import ProductoRepository

# ── Lee el umbral desde .env si existe ───────────────────────
_threshold = int(os.getenv("LOW_STOCK_THRESHOLD", LOW_STOCK_THRESHOLD))


class InventarioService:

    def __init__(self, producto_repo: ProductoRepository):
        self.producto_repo = producto_repo

    # ── HU-016: GET /api/v1/inventory/{productId} ────────────
    def consultar_stock(self, product_id: int,
                        usuario_role: str) -> InventarioResponse:

        # Regla de negocio: solo admin puede consultar directamente
        if usuario_role != "admin":
            raise PermissionError(
                "Solo un administrador puede consultar el inventario."
            )

        producto = self.producto_repo.obtener_por_id(product_id)
        if not producto:
            raise ValueError(
                f"El producto con id {product_id} no existe en el sistema."
            )

        # Regla de dominio: isLowStock si stock <= LOW_STOCK_THRESHOLD
        is_low_stock = producto.stock <= _threshold

        return InventarioResponse(
            success    = True,
            statusCode = 200,
            message    = "Stock consultado correctamente.",
            data       = InventarioData(
                productId   = producto.id,
                productName = producto.name,
                stock       = producto.stock,
                isLowStock  = is_low_stock,
                lastUpdated = str(date.today()),
            )
        )