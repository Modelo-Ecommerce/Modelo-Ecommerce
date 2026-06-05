# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# HU-009: Crear pedido
# HU-010: Consultar pedido
# HU-011: Cancelar pedido
# HU-012: Actualizar estado del pedido
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional
from app.domain.pedidoDomain import (
    PedidoCreate, PedidoStatusUpdate, PedidoResponse,
    MinimumOrderAmountException, MinimumQuantityException,
    PaymentGatewayException, OrderNotCancellableException,
    InvalidStatusTransitionException, OrderNotUpdatableException
)
from app.domain.carritoDomain import InsufficientStockException
from app.services.dependencies import order_service as service

router = APIRouter(prefix="/api/v1/orders", tags=["Pedidos"])


def get_usuario_token(authorization: Optional[str] = None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "statusCode": 401,
                    "message": "Token requerido.",
                    "error": {"error_code": "UNAUTHORIZED"}}
        )
    token = authorization.replace("Bearer ", "").strip()
    try:
        user_id, role = token.split(":")
        return {"id": int(user_id), "role": role}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "statusCode": 401,
                    "message": "Token inválido.",
                    "error": {"error_code": "INVALID_TOKEN"}}
        )


# ── POST /api/v1/orders ───────────────────────────────────────
@router.post("/", response_model=PedidoResponse,
             status_code=status.HTTP_201_CREATED)
def crear_pedido(datos: PedidoCreate,
                 authorization: Optional[str] = Header(None)):
    """Crea un pedido a partir del carrito. Requiere JWT."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.crear_pedido(datos, usuario_actual["id"])
    except PermissionError as e:
        raise HTTPException(status_code=403,
            detail={"success": False, "statusCode": 403, "message": str(e),
                    "error": {"error_code": "FORBIDDEN"}})
    except MinimumOrderAmountException as e:
        raise HTTPException(status_code=422,
            detail={"success": False, "statusCode": 422,
                    "message": "El valor del pedido no cumple el mínimo requerido.",
                    "error": {"error_code": "MINIMUM_ORDER_AMOUNT",
                              "details": str(e), "timestamp": "2026-03-17"}})
    except MinimumQuantityException as e:
        raise HTTPException(status_code=422,
            detail={"success": False, "statusCode": 422,
                    "message": "El carrito no cumple la cantidad mínima requerida.",
                    "error": {"error_code": "MINIMUM_QUANTITY",
                              "details": str(e), "timestamp": "2026-03-17"}})
    except InsufficientStockException as e:
        raise HTTPException(status_code=422,
            detail={"success": False, "statusCode": 422,
                    "message": "Stock insuficiente para uno o más productos.",
                    "error": {"error_code": "INSUFFICIENT_STOCK",
                              "details": str(e), "timestamp": "2026-03-17"}})
    except PaymentGatewayException as e:
        raise HTTPException(status_code=502,
            detail={"success": False, "statusCode": 502,
                    "message": "Error al procesar el pago.",
                    "error": {"error_code": "PAYMENT_GATEWAY_ERROR",
                              "details": str(e), "timestamp": "2026-03-17"}})
    except ValueError as e:
        raise HTTPException(status_code=404,
            detail={"success": False, "statusCode": 404, "message": str(e),
                    "error": {"error_code": "NOT_FOUND"}})


# ── GET /api/v1/orders/{id} ───────────────────────────────────
@router.get("/{id}", response_model=PedidoResponse,
            status_code=status.HTTP_200_OK)
def obtener_pedido(id: int,
                   authorization: Optional[str] = Header(None)):
    """Consulta el detalle de un pedido. Requiere JWT."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.obtener_pedido(
            order_id         = id,
            usuario_token_id = usuario_actual["id"],
            usuario_role     = usuario_actual["role"],
        )
    except PermissionError as e:
        raise HTTPException(status_code=403,
            detail={"success": False, "statusCode": 403, "message": str(e),
                    "error": {"error_code": "FORBIDDEN"}})
    except ValueError as e:
        raise HTTPException(status_code=404,
            detail={"success": False, "statusCode": 404,
                    "message": "Pedido no encontrado.",
                    "error": {"error_code": "ORDER_NOT_FOUND",
                              "details": str(e), "timestamp": "2026-03-17"}})


# ── PATCH /api/v1/orders/{id} — Actualizar estado (admin) ────
@router.patch("/{id}", response_model=PedidoResponse,
              status_code=status.HTTP_200_OK)
def actualizar_estado(id: int, datos: PedidoStatusUpdate,
                      authorization: Optional[str] = Header(None)):
    """Actualiza el estado del pedido. Solo administradores."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.actualizar_estado(id, datos, usuario_actual["role"])
    except PermissionError as e:
        raise HTTPException(status_code=403,
            detail={"success": False, "statusCode": 403, "message": str(e),
                    "error": {"error_code": "FORBIDDEN"}})
    except InvalidStatusTransitionException as e:
        raise HTTPException(status_code=400,
            detail={"success": False, "statusCode": 400,
                    "message": "Transición de estado no permitida.",
                    "error": {"error_code": "INVALID_STATUS_TRANSITION",
                              "details": str(e), "timestamp": "2026-03-17"}})
    except OrderNotUpdatableException as e:
        raise HTTPException(status_code=409,
            detail={"success": False, "statusCode": 409,
                    "message": "El pedido no puede ser actualizado en su estado actual.",
                    "error": {"error_code": "ORDER_NOT_UPDATABLE",
                              "details": str(e), "timestamp": "2026-03-17"}})
    except ValueError as e:
        raise HTTPException(status_code=404,
            detail={"success": False, "statusCode": 404,
                    "message": "Pedido no encontrado.",
                    "error": {"error_code": "ORDER_NOT_FOUND",
                              "details": str(e), "timestamp": "2026-03-17"}})


# ── DELETE /api/v1/orders/{id} — Cancelar pedido ─────────────
@router.delete("/{id}", response_model=PedidoResponse,
               status_code=status.HTTP_200_OK)
def cancelar_pedido(id: int,
                    authorization: Optional[str] = Header(None)):
    """Cancela un pedido en estado pending. Requiere JWT."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.cancelar_pedido(
            order_id         = id,
            usuario_token_id = usuario_actual["id"],
            usuario_role     = usuario_actual["role"],
        )
    except PermissionError as e:
        raise HTTPException(status_code=403,
            detail={"success": False, "statusCode": 403, "message": str(e),
                    "error": {"error_code": "FORBIDDEN"}})
    except OrderNotCancellableException as e:
        raise HTTPException(status_code=409,
            detail={"success": False, "statusCode": 409,
                    "message": "El pedido no puede ser cancelado en su estado actual.",
                    "error": {"error_code": "ORDER_NOT_CANCELLABLE",
                              "details": str(e), "timestamp": "2026-03-17"}})
    except ValueError as e:
        raise HTTPException(status_code=404,
            detail={"success": False, "statusCode": 404,
                    "message": "Pedido no encontrado.",
                    "error": {"error_code": "ORDER_NOT_FOUND",
                              "details": str(e), "timestamp": "2026-03-17"}})