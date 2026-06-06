# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

import os
from datetime import date
from app.domain.inventarioDomain import (
    InventarioData, InventarioUpdateData, InventarioUpdate,
    InventarioResponse, InventoryMovement,
    InsufficientStockForOperationException,
    LOW_STOCK_THRESHOLD
)
from app.repositories.productoRepository import ProductoRepository

_threshold = int(os.getenv("LOW_STOCK_THRESHOLD", LOW_STOCK_THRESHOLD))


class InventarioService:

    def __init__(self, producto_repo: ProductoRepository):
        self.producto_repo = producto_repo
        # Registro de movimientos en memoria
        self._movimientos: list[InventoryMovement] = []

    # ── HU-016: GET /api/v1/inventory/{productId} ────────────
    def consultar_stock(self, product_id: int,
                        usuario_role: str) -> InventarioResponse:
        if usuario_role != "admin":
            raise PermissionError(
                "Solo un administrador puede consultar el inventario."
            )
        producto = self.producto_repo.obtener_por_id(product_id)
        if not producto:
            raise ValueError(
                f"El producto con id {product_id} no existe en el sistema."
            )
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

    # ── HU-017: PATCH /api/v1/inventory/{productId} ──────────
    def actualizar_stock(self, product_id: int,
                         datos: InventarioUpdate,
                         usuario_role: str) -> InventarioResponse:

        # Regla de negocio: solo admin
        if usuario_role != "admin":
            raise PermissionError(
                "Solo un administrador puede actualizar el inventario."
            )

        # Regla de negocio: producto debe existir
        producto = self.producto_repo.obtener_por_id(product_id)
        if not producto:
            raise ValueError(
                f"El producto con id {product_id} no existe en el sistema."
            )

        previous_stock = producto.stock

        if datos.operation == "decrease":
            # Regla de dominio: stock no puede ser negativo
            if producto.stock < datos.quantity:
                raise InsufficientStockForOperationException(
                    producto.stock, datos.quantity
                )
            producto.stock -= datos.quantity

        elif datos.operation == "increase":
            producto.stock += datos.quantity

        current_stock = producto.stock
        is_low_stock  = current_stock <= _threshold

        # Registrar movimiento en inventory_movements
        movimiento = InventoryMovement(
            productId   = product_id,
            operation   = datos.operation,
            quantity    = datos.quantity,
            reason      = datos.reason,
            orderId     = datos.orderId,
            stockBefore = previous_stock,
            stockAfter  = current_stock,
            createdAt   = str(date.today()),
        )
        self._movimientos.append(movimiento)

        # Notificar stock bajo automáticamente
        if is_low_stock:
            self._notificar_stock_bajo(product_id, producto.name, current_stock)

        return InventarioResponse(
            success    = True,
            statusCode = 200,
            message    = "Stock actualizado correctamente.",
            data       = InventarioUpdateData(
                productId       = producto.id,
                productName     = producto.name,
                previousStock   = previous_stock,
                quantityChanged = datos.quantity,
                currentStock    = current_stock,
                isLowStock      = is_low_stock,
                updatedAt       = str(date.today()),
            )
        )

    def _notificar_stock_bajo(self, product_id: int,
                               product_name: str, stock: int) -> None:
        """
        Simula la notificación de stock bajo.
        En producción enviaría un email o evento al sistema de alertas.
        """
        print(
            f"⚠️  ALERTA STOCK BAJO — Producto: {product_name} "
            f"(id: {product_id}) — Stock actual: {stock} unidades."
        )

    def obtener_movimientos(self, product_id: int) -> list:
        return [m for m in self._movimientos if m.productId == product_id]