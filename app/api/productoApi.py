# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# HU-004: Crear producto
# HU-005: Eliminar y actualizar producto
# HU-006: Consultar catálogo de productos
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status, Header, Query
from typing import Optional
from app.domain.productoDomain import (
    ProductoCreate, ProductoUpdate, ProductoResponse,
    PriceBelowMinimumException, ProductHasActiveOrdersException
)
from app.services.dependencies import producto_service as service

router = APIRouter(prefix="/api/v1/products", tags=["Productos"])


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


def _handle_permission_error(e: PermissionError):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "success": False, "statusCode": 403,
            "message": str(e),
            "error": {"error_code": "FORBIDDEN"}
        }
    )


def _handle_price_error(e: PriceBelowMinimumException):
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "success": False, "statusCode": 422,
            "message": "El precio del producto no cumple el mínimo requerido.",
            "error": {
                "error_code": "PRICE_BELOW_MINIMUM",
                "details": str(e),
                "timestamp": "2026-03-17"
            }
        }
    )


# ── GET /api/v1/products — Catálogo público ───────────────────
@router.get("/", response_model=ProductoResponse,
            status_code=status.HTTP_200_OK)
def catalogo_productos(
    category:  Optional[int]   = Query(None, description="Filtrar por categoryId"),
    minPrice:  Optional[float] = Query(None, description="Precio mínimo en COP"),
    maxPrice:  Optional[float] = Query(None, description="Precio máximo en COP"),
    page:      int             = Query(1,    ge=1, description="Número de página"),
    limit:     int             = Query(10,   ge=1, le=100, description="Resultados por página"),
):
    """Lista el catálogo público. Solo productos activos. Sin autenticación."""
    try:
        return service.catalogo(
            category  = category,
            min_price = minPrice,
            max_price = maxPrice,
            page      = page,
            limit     = limit,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False, "statusCode": 400,
                "message": str(e),
                "error": {"error_code": "VALIDATION_ERROR"}
            }
        )


# ── GET /api/v1/products/{id} — Detalle público ───────────────
@router.get("/{id}", response_model=ProductoResponse,
            status_code=status.HTTP_200_OK)
def detalle_producto(id: int):
    """Detalle de un producto. Sin autenticación."""
    try:
        return service.detalle_publico(id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False, "statusCode": 404,
                "message": "Producto no encontrado.",
                "error": {"error_code": "PRODUCT_NOT_FOUND", "details": str(e)}
            }
        )


# ── POST /api/v1/products — Crear producto (admin) ───────────
@router.post("/", response_model=ProductoResponse,
             status_code=status.HTTP_201_CREATED)
def crear_producto(datos: ProductoCreate,
                   authorization: Optional[str] = Header(None)):
    """Crea un nuevo producto. Solo administradores."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.crear(datos, usuario_actual["role"])
    except PermissionError as e:
        _handle_permission_error(e)
    except PriceBelowMinimumException as e:
        _handle_price_error(e)
    except ValueError as e:
        error_str = str(e)
        if "categoría" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False, "statusCode": 404,
                    "message": "Categoría no encontrada.",
                    "error": {"error_code": "CATEGORY_NOT_FOUND", "details": error_str}
                }
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False, "statusCode": 400,
                "message": str(e),
                "error": {"error_code": "VALIDATION_ERROR"}
            }
        )


# ── PUT /api/v1/products/{id} — Actualizar producto (admin) ──
@router.put("/{id}", response_model=ProductoResponse,
            status_code=status.HTTP_200_OK)
def actualizar_producto(id: int, datos: ProductoUpdate,
                        authorization: Optional[str] = Header(None)):
    """Actualiza nombre, descripción, precio o categoría. Solo admin."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.actualizar(id, datos, usuario_actual["role"])
    except PermissionError as e:
        _handle_permission_error(e)
    except PriceBelowMinimumException as e:
        _handle_price_error(e)
    except ValueError as e:
        error_str = str(e)
        if "no encontrado" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False, "statusCode": 404,
                    "message": "Producto no encontrado.",
                    "error": {"error_code": "PRODUCT_NOT_FOUND", "details": error_str}
                }
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False, "statusCode": 404,
                "message": "Categoría no encontrada.",
                "error": {"error_code": "CATEGORY_NOT_FOUND", "details": error_str}
            }
        )


# ── DELETE /api/v1/products/{id} — Eliminar producto (admin) ─
@router.delete("/{id}", response_model=ProductoResponse,
               status_code=status.HTTP_200_OK)
def eliminar_producto(id: int, authorization: Optional[str] = Header(None)):
    """Elimina un producto (soft-delete). Solo administradores."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.eliminar(id, usuario_actual["role"])
    except PermissionError as e:
        _handle_permission_error(e)
    except ProductHasActiveOrdersException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False, "statusCode": 409,
                "message": "No se puede eliminar el producto porque tiene pedidos activos.",
                "error": {
                    "error_code": "PRODUCT_HAS_ACTIVE_ORDERS",
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
                "message": "Producto no encontrado.",
                "error": {"error_code": "PRODUCT_NOT_FOUND", "details": str(e)}
            }
        )