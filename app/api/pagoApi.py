# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# HU-013: Iniciar proceso de pago
# HU-014: Consultar estado del pago
# HU-015: Webhook Wompi + PATCH estado pago
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status, Header, Request
from typing import Optional
from app.domain.pagoDomain import (
    PagoCreate, PagoStatusUpdate, WebhookWompi, PagoResponse,
    PaymentAmountMismatchException, PaymentAlreadyApprovedException,
    PaymentGatewayException, InvalidWebhookSignatureException
)
from app.services.dependencies import payment_service as service

router = APIRouter(prefix="/api/v1/payments", tags=["Pagos"])


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


# ── POST /api/v1/payments/webhook — Wompi webhook ────────────
@router.post("/webhook", response_model=PagoResponse,
             status_code=status.HTTP_200_OK)
async def webhook_wompi(payload: WebhookWompi, request: Request):
    """
    Endpoint público para recibir notificaciones de Wompi.
    No requiere JWT. Valida firma del header x-wompi-signature.
    SIEMPRE retorna 200 OK a Wompi para evitar reintentos.
    Para testing usa el header: x-wompi-signature: wompi_test_signature
    """
    signature = request.headers.get("x-wompi-signature", "")
    try:
        return service.recibir_webhook(payload, signature)
    except InvalidWebhookSignatureException:
        raise HTTPException(status_code=401,
            detail={"success": False, "statusCode": 401,
                    "message": "Firma del webhook inválida.",
                    "error": {"error_code": "INVALID_WEBHOOK_SIGNATURE"}})
    except Exception:
        # Siempre 200 a Wompi aunque haya error interno
        return PagoResponse(
            success    = True,
            statusCode = 200,
            message    = "Webhook recibido. Error interno registrado.",
            data       = None
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
                    "message": "El monto no coincide con el total del pedido.",
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
        return service.obtener_pago(id, usuario_actual["id"],
                                    usuario_actual["role"])
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


# ── PATCH /api/v1/payments/{id} — Actualizar estado (admin) ──
@router.patch("/{id}", response_model=PagoResponse,
              status_code=status.HTTP_200_OK)
def actualizar_estado_pago(id: int, datos: PagoStatusUpdate,
                            authorization: Optional[str] = Header(None)):
    """Actualiza el estado del pago. Solo administradores."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.actualizar_estado_pago(id, datos, usuario_actual["role"])
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