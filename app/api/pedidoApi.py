# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# HU-009: Crear pedido
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional
from app.domain.pedidoDomain import (
    PedidoCreate, PedidoResponse,
    MinimumOrderAmountException, MinimumQuantityException,
    PaymentGatewayException
)
from app.domain.carritoDomain import InsufficientStockException
from app.services.dependencies import order_service as service

router = APIRouter(prefix="/api/v1/orders", tags=["Pedidos"])


# ── Leer token JWT simulado ───────────────────────────────────
def get_usuario_token(authorization: Optional[str] = None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False, "statusCode": 401,
                "message": "Token requerido.",
                "error": {"error_code": "UNAUTHORIZED"}
            }
        )
    token = authorization.replace("Bearer ", "").strip()
    try:
        user_id, role = token.split(":")
        return {"id": int(user_id), "role": role}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False, "statusCode": 401,
                "message": "Token inválido.",
                "error": {"error_code": "INVALID_TOKEN"}
            }
        )


# ── POST /api/v1/orders — Crear pedido ───────────────────────
@router.post("/", response_model=PedidoResponse,
             status_code=status.HTTP_201_CREATED)
def crear_pedido(datos: PedidoCreate,
                 authorization: Optional[str] = Header(None)):
    """Crea un pedido a partir del carrito. Requiere JWT."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.crear_pedido(datos, usuario_actual["id"])
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False, "statusCode": 403,
                "message": str(e),
                "error": {"error_code": "FORBIDDEN"}
            }
        )
    except MinimumOrderAmountException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False, "statusCode": 422,
                "message": "El valor del pedido no cumple el mínimo requerido.",
                "error": {
                    "error_code": "MINIMUM_ORDER_AMOUNT",
                    "details": str(e),
                    "timestamp": "2026-03-17"
                }
            }
        )
    except MinimumQuantityException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False, "statusCode": 422,
                "message": "El carrito no cumple la cantidad mínima requerida.",
                "error": {
                    "error_code": "MINIMUM_QUANTITY",
                    "details": str(e),
                    "timestamp": "2026-03-17"
                }
            }
        )
    except InsufficientStockException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "success": False, "statusCode": 422,
                "message": "Stock insuficiente para uno o más productos.",
                "error": {
                    "error_code": "INSUFFICIENT_STOCK",
                    "details": str(e),
                    "timestamp": "2026-03-17"
                }
            }
        )
    except PaymentGatewayException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "success": False, "statusCode": 502,
                "message": "Error al procesar el pago. El pedido fue revertido.",
                "error": {
                    "error_code": "PAYMENT_GATEWAY_ERROR",
                    "details": str(e),
                    "timestamp": "2026-03-17"
                }
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False, "statusCode": 404,
                "message": str(e),
                "error": {"error_code": "NOT_FOUND"}
            }
        )