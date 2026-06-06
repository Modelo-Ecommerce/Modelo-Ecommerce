# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# HU-013: Iniciar proceso de pago
# HU-014: Consultar estado del pago
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional
from app.domain.pagoDomain import (
    PagoCreate, PagoResponse,
    PaymentAmountMismatchException, PaymentAlreadyApprovedException,
    PaymentGatewayException
)
from app.services.dependencies import payment_service as service

router = APIRouter(prefix="/api/v1/payments", tags=["Pagos"])


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


# ── POST /api/v1/payments — Iniciar pago ─────────────────────
@router.post("/", response_model=PagoResponse,
             status_code=status.HTTP_201_CREATED)
def iniciar_pago(datos: PagoCreate,
                 authorization: Optional[str] = Header(None)):
    """Inicia el proceso de pago con Wompi. Requiere JWT."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.procesar_pago(datos, usuario_actual["id"])
    except PermissionError as e:
        raise HTTPException(status_code=403,
            detail={"success": False, "statusCode": 403, "message": str(e),
                    "error": {"error_code": "FORBIDDEN"}})
    except PaymentAmountMismatchException as e:
        raise HTTPException(status_code=422,
            detail={"success": False, "statusCode": 422,
                    "message": "El monto del pago no coincide con el total del pedido.",
                    "error": {"error_code": "PAYMENT_AMOUNT_MISMATCH",
                              "details": str(e), "timestamp": "2026-03-17"}})
    except PaymentAlreadyApprovedException as e:
        raise HTTPException(status_code=409,
            detail={"success": False, "statusCode": 409,
                    "message": "El pedido ya tiene un pago aprobado.",
                    "error": {"error_code": "PAYMENT_ALREADY_APPROVED",
                              "details": str(e), "timestamp": "2026-03-17"}})
    except PaymentGatewayException as e:
        raise HTTPException(status_code=502,
            detail={"success": False, "statusCode": 502,
                    "message": "Error al conectar con la pasarela de pago.",
                    "error": {"error_code": "PAYMENT_GATEWAY_ERROR",
                              "details": str(e), "timestamp": "2026-03-17"}})
    except ValueError as e:
        raise HTTPException(status_code=404,
            detail={"success": False, "statusCode": 404, "message": str(e),
                    "error": {"error_code": "NOT_FOUND"}})


# ── GET /api/v1/payments/{id} — Consultar pago ───────────────
@router.get("/{id}", response_model=PagoResponse,
            status_code=status.HTTP_200_OK)
def obtener_pago(id: int,
                 authorization: Optional[str] = Header(None)):
    """Consulta el estado de un pago. Requiere JWT."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.obtener_pago(
            payment_id       = id,
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
                    "message": "Pago no encontrado.",
                    "error": {"error_code": "PAYMENT_NOT_FOUND",
                              "details": str(e), "timestamp": "2026-03-17"}})