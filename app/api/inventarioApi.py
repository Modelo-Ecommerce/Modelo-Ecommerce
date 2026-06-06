# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# HU-016: Consultar stock de producto
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional
from app.domain.inventarioDomain import InventarioResponse
from app.services.dependencies import inventario_service as service

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventario"])


def get_usuario_token(authorization: Optional[str] = None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401,
            detail={"success": False, "statusCode": 401,
                    "message": "Token requerido.",
                    "error": {"error_code": "UNAUTHORIZED"}})
    token = authorization.replace("Bearer ", "").strip()
    try:
        user_id, role = token.split(":")
        return {"id": int(user_id), "role": role}
    except Exception:
        raise HTTPException(status_code=401,
            detail={"success": False, "statusCode": 401,
                    "message": "Token inválido.",
                    "error": {"error_code": "INVALID_TOKEN"}})


# ── GET /api/v1/inventory/{productId} — Consultar stock ──────
@router.get("/{productId}", response_model=InventarioResponse,
            status_code=status.HTTP_200_OK)
def consultar_stock(productId: int,
                    authorization: Optional[str] = Header(None)):
    """Consulta el stock actual de un producto. Solo administradores."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.consultar_stock(productId, usuario_actual["role"])
    except PermissionError as e:
        raise HTTPException(status_code=403,
            detail={"success": False, "statusCode": 403, "message": str(e),
                    "error": {"error_code": "FORBIDDEN"}})
    except ValueError as e:
        raise HTTPException(status_code=404,
            detail={"success": False, "statusCode": 404,
                    "message": "Producto no encontrado.",
                    "error": {"error_code": "PRODUCT_NOT_FOUND",
                              "details": str(e), "timestamp": "2026-03-17"}})