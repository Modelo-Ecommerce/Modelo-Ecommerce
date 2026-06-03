# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# HU-007: Agregar producto al carrito
# HU-008: Consultar y confirmar carrito
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional
from app.domain.carritoDomain import (
    CarritoItemAdd, CarritoItemUpdate, CarritoResponse,
    InsufficientStockException, ProductDiscontinuedException,
    CartItemLimitExceededException
)
from app.services.dependencies import cart_service as service

router = APIRouter(prefix="/api/v1/carts", tags=["Carrito"])


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


def _handle_stock_error(e: InsufficientStockException):
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "success": False, "statusCode": 422,
            "message": "Stock insuficiente para agregar el producto al carrito.",
            "error": {
                "error_code": "INSUFFICIENT_STOCK",
                "details": str(e),
                "timestamp": "2026-03-17"
            }
        }
    )


# ── POST /api/v1/carts/items — Agregar producto ───────────────
@router.post("/items", response_model=CarritoResponse,
             status_code=status.HTTP_201_CREATED)
def agregar_item(datos: CarritoItemAdd,
                 authorization: Optional[str] = Header(None)):
    """Agrega un producto al carrito. Requiere JWT."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.agregar_item(datos, usuario_actual["id"])
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "statusCode": 403, "message": str(e),
                    "error": {"error_code": "FORBIDDEN"}})
    except ProductDiscontinuedException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"success": False, "statusCode": 422,
                    "message": "El producto está descontinuado.",
                    "error": {"error_code": "PRODUCT_DISCONTINUED", "details": str(e)}})
    except InsufficientStockException as e:
        _handle_stock_error(e)
    except CartItemLimitExceededException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"success": False, "statusCode": 422,
                    "message": "Se alcanzó el límite de ítems en el carrito.",
                    "error": {"error_code": "CART_ITEM_LIMIT_EXCEEDED", "details": str(e)}})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "statusCode": 404,
                    "message": "Producto no encontrado.",
                    "error": {"error_code": "PRODUCT_NOT_FOUND", "details": str(e)}})


# ── GET /api/v1/carts/{userId} — Consultar carrito ───────────
@router.get("/{userId}", response_model=CarritoResponse,
            status_code=status.HTTP_200_OK)
def obtener_carrito(userId: int,
                    authorization: Optional[str] = Header(None)):
    """Consulta el carrito de un usuario. Requiere JWT."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.obtener_carrito(userId, usuario_actual["id"])
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "statusCode": 403, "message": str(e),
                    "error": {"error_code": "FORBIDDEN"}})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "statusCode": 404, "message": str(e),
                    "error": {"error_code": "CART_NOT_FOUND"}})


# ── PATCH /api/v1/carts/items/{id} — Actualizar cantidad ─────
@router.patch("/items/{id}", response_model=CarritoResponse,
              status_code=status.HTTP_200_OK)
def actualizar_cantidad(id: int, datos: CarritoItemUpdate,
                        authorization: Optional[str] = Header(None)):
    """Actualiza la cantidad de un ítem en el carrito. Requiere JWT."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.actualizar_cantidad(id, datos, usuario_actual["id"])
    except InsufficientStockException as e:
        _handle_stock_error(e)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "statusCode": 404, "message": str(e),
                    "error": {"error_code": "ITEM_NOT_FOUND"}})


# ── DELETE /api/v1/carts/items/{id} — Eliminar ítem ──────────
@router.delete("/items/{id}", response_model=CarritoResponse,
               status_code=status.HTTP_200_OK)
def eliminar_item(id: int, authorization: Optional[str] = Header(None)):
    """Elimina un ítem del carrito. Requiere JWT."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.eliminar_item(id, usuario_actual["id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "statusCode": 404, "message": str(e),
                    "error": {"error_code": "ITEM_NOT_FOUND"}})