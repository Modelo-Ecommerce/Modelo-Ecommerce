# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# HU-004: Crear producto
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional
from app.domain.productoDomain import ProductoCreate, ProductoResponse, PriceBelowMinimumException
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


# ── POST /api/v1/products — Crear producto ────────────────────
@router.post("/", response_model=ProductoResponse,
             status_code=status.HTTP_201_CREATED)
def crear_producto(datos: ProductoCreate,
                   authorization: Optional[str] = Header(None)):
    """Crea un nuevo producto. Solo administradores."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.crear(datos, usuario_actual["role"])
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False, "statusCode": 403,
                "message": str(e),
                "error": {"error_code": "FORBIDDEN"}
            }
        )
    except PriceBelowMinimumException as e:
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
    except ValueError as e:
        error_str = str(e)
        if "categoría" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False, "statusCode": 404,
                    "message": "Categoría no encontrada.",
                    "error": {
                        "error_code": "CATEGORY_NOT_FOUND",
                        "details": error_str
                    }
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


# ── GET /api/v1/products — Listar productos ───────────────────
@router.get("/", response_model=ProductoResponse,
            status_code=status.HTTP_200_OK)
def listar_productos(authorization: Optional[str] = Header(None)):
    """Lista todos los productos disponibles."""
    get_usuario_token(authorization)
    return service.listar()


# ── GET /api/v1/products/{id} — Obtener producto ─────────────
@router.get("/{id}", response_model=ProductoResponse,
            status_code=status.HTTP_200_OK)
def obtener_producto(id: int, authorization: Optional[str] = Header(None)):
    """Obtiene un producto por ID."""
    get_usuario_token(authorization)
    try:
        return service.obtener(id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False, "statusCode": 404,
                "message": "Producto no encontrado.",
                "error": {"error_code": "PRODUCT_NOT_FOUND", "details": str(e)}
            }
        )