# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

import os
import httpx
from datetime import date, datetime
from app.domain.inventarioDomain import (
    InventarioData, InventarioUpdateData, InventarioUpdate,
    InventarioResponse, InventoryMovement,
    LowStockAlertPayload, LowStockAlertData,
    InsufficientStockForOperationException,
    LOW_STOCK_THRESHOLD
)
from app.repositories.productoRepository import ProductoRepository

_threshold = int(os.getenv("LOW_STOCK_THRESHOLD", LOW_STOCK_THRESHOLD))

# URL del servicio de notificaciones (configurable en .env)
NOTIFICATION_SERVICE_URL = os.getenv(
    "NOTIFICATION_SERVICE_URL",
    "http://localhost:8000/api/v1/inventory/notify-low-stock"
)


class InventarioService:

    def __init__(self, producto_repo: ProductoRepository):
        self.producto_repo = producto_repo
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

    # ── HU-017 + HU-018: PATCH /api/v1/inventory/{productId} ─
    def actualizar_stock(self, product_id: int,
                         datos: InventarioUpdate,
                         usuario_role: str) -> InventarioResponse:
        if usuario_role != "admin":
            raise PermissionError(
                "Solo un administrador puede actualizar el inventario."
            )
        producto = self.producto_repo.obtener_por_id(product_id)
        if not producto:
            raise ValueError(
                f"El producto con id {product_id} no existe en el sistema."
            )

        previous_stock = producto.stock

        if datos.operation == "decrease":
            if producto.stock < datos.quantity:
                raise InsufficientStockForOperationException(
                    producto.stock, datos.quantity
                )
            producto.stock -= datos.quantity
        elif datos.operation == "increase":
            producto.stock += datos.quantity

        current_stock = producto.stock
        is_low_stock  = current_stock <= _threshold

        # Registrar movimiento
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

        # ── HU-018: Notificar stock bajo automáticamente ──────
        low_stock_notified = False
        message = "Stock actualizado correctamente."

        if is_low_stock:
            low_stock_notified = self._notificar_stock_bajo(
                product_id   = product_id,
                product_name = producto.name,
                current_stock = current_stock,
            )
            if low_stock_notified:
                message = "Stock actualizado correctamente. Se ha enviado alerta de stock bajo."
            else:
                message = "Stock actualizado correctamente. La notificación de stock bajo no pudo enviarse."

        return InventarioResponse(
            success    = True,
            statusCode = 200,
            message    = message,
            data       = InventarioUpdateData(
                productId        = producto.id,
                productName      = producto.name,
                previousStock    = previous_stock,
                quantityChanged  = datos.quantity,
                currentStock     = current_stock,
                isLowStock       = is_low_stock,
                lowStockNotified = low_stock_notified,
                updatedAt        = str(date.today()),
            )
        )

    # ── HU-018: Notificar stock bajo ──────────────────────────
    def _notificar_stock_bajo(self, product_id: int,
                               product_name: str,
                               current_stock: int) -> bool:
        """
        Envía el payload al Servicio de Notificaciones externo.
        Si falla, registra en logs y retorna False — nunca lanza excepción.
        """
        payload = LowStockAlertPayload(
            event = "low_stock_alert",
            data  = LowStockAlertData(
                productId    = product_id,
                productName  = product_name,
                currentStock = current_stock,
                threshold    = _threshold,
                alertedAt    = datetime.now().isoformat(),
            )
        )
        try:
            # Llamada interna al endpoint de notificación
            response = httpx.post(
                NOTIFICATION_SERVICE_URL,
                json    = payload.model_dump(),
                timeout = 3.0,
            )
            if response.status_code == 200:
                return True
            print(
                f"[LOG] Servicio de notificaciones respondió {response.status_code} "
                f"para producto {product_id}."
            )
            return False
        except Exception as e:
            # Fallo silencioso — la operación de stock no se revierte
            print(
                f"[LOG] Error al contactar Servicio de Notificaciones: {str(e)} "
                f"— Producto: {product_name} (id: {product_id}), "
                f"stock: {current_stock}."
            )
            return False

    def obtener_movimientos(self, product_id: int) -> list:
        return [m for m in self._movimientos if m.productId == product_id]