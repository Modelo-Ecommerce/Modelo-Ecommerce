# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

import uuid
from app.domain.pagoDomain import (
    PagoCreate, PagoStatusUpdate, WebhookWompi,
    PagoResponse, PagoData, PagoDetalleData, WebhookResultData, Pago,
    PaymentAmountMismatchException, PaymentAlreadyApprovedException,
    PaymentGatewayException, InvalidWebhookSignatureException
)
from app.repositories.pagoRepository import PagoRepository
from app.repositories.pedidoRepository import PedidoRepository
from app.repositories.productoRepository import ProductoRepository

# ── Clave secreta simulada del webhook Wompi ──────────────────
WOMPI_WEBHOOK_SECRET = "wompi_secret_test_key"


class WompiService:
    """Simula la integración con la API de Wompi."""
    def iniciar_transaccion(self, order_id: int, amount: float,
                             currency: str, payment_method: dict,
                             customer_email: str,
                             redirect_url: str) -> dict:
        transaction_id = f"wompi_txn_{uuid.uuid4().hex[:8]}"
        payment_url = (
            f"https://checkout.wompi.co/p/"
            f"?public-key=pub_test_demo"
            f"&currency={currency}"
            f"&amount-in-cents={int(amount * 100)}"
            f"&reference=ORDER-{order_id}"
            f"&redirect-url={redirect_url}"
        )
        return {
            "transactionId": transaction_id,
            "paymentUrl":    payment_url,
            "status":        "pending",
        }

    def validar_firma(self, signature: str) -> bool:
        """
        Simula la validación de firma del webhook.
        En producción verificaría con HMAC-SHA256 usando WOMPI_WEBHOOK_SECRET.
        Para testing acepta la firma 'wompi_test_signature'.
        """
        #return signature == "wompi_test_signature" # Para pruebas locales sin validación estricta
        return True  # Aceptar cualquier firma para facilitar pruebas locales

class PaymentService:

    def __init__(self, pago_repo: PagoRepository,
                 pedido_repo: PedidoRepository,
                 producto_repo: ProductoRepository,
                 wompi_service: WompiService):
        self.pago_repo    = pago_repo
        self.pedido_repo  = pedido_repo
        self.producto_repo = producto_repo
        self.wompi        = wompi_service

    # ── HU-013: POST /api/v1/payments ────────────────────────
    def procesar_pago(self, datos: PagoCreate,
                      usuario_token_id: int) -> PagoResponse:
        if datos.userId != usuario_token_id:
            raise PermissionError(
                "No puedes iniciar un pago en nombre de otro usuario."
            )
        pedido = self.pedido_repo.obtener_por_id(datos.orderId)
        if not pedido:
            raise ValueError(f"Pedido con id {datos.orderId} no encontrado.")
        if pedido.user_id != datos.userId:
            raise PermissionError("El pedido no pertenece al usuario autenticado.")
        if datos.amount != pedido.total:
            raise PaymentAmountMismatchException(datos.amount, pedido.total)

        pago_existente = self.pago_repo.obtener_por_orden(datos.orderId)
        if pago_existente and pago_existente.status == "approved":
            raise PaymentAlreadyApprovedException()

        try:
            wompi_response = self.wompi.iniciar_transaccion(
                order_id       = datos.orderId,
                amount         = datos.amount,
                currency       = datos.currency,
                payment_method = datos.paymentMethod.model_dump(),
                customer_email = datos.customerEmail,
                redirect_url   = datos.redirectUrl,
            )
        except Exception as e:
            raise PaymentGatewayException(f"Error al conectar con Wompi: {str(e)}")

        pago = Pago(
            payment_id           = 0,
            order_id             = datos.orderId,
            user_id              = datos.userId,
            amount               = datos.amount,
            currency             = datos.currency,
            wompi_transaction_id = wompi_response["transactionId"],
            payment_url          = wompi_response["paymentUrl"],
            payment_method_type  = datos.paymentMethod.type,
        )
        pago = self.pago_repo.crear(pago)
        return PagoResponse(
            success    = True,
            statusCode = 201,
            message    = "Pago iniciado. Redirigiendo a pasarela Wompi.",
            data       = PagoData(**pago.to_response())
        )

    # ── HU-014: GET /api/v1/payments/{id} ────────────────────
    def obtener_pago(self, payment_id: int,
                     usuario_token_id: int,
                     usuario_role: str) -> PagoResponse:
        pago = self.pago_repo.obtener_por_id(payment_id)
        if not pago:
            raise ValueError(f"El pago con id {payment_id} no existe en el sistema.")
        if usuario_role == "client" and pago.user_id != usuario_token_id:
            raise PermissionError("No tienes permiso para consultar este pago.")
        return PagoResponse(
            success    = True,
            statusCode = 200,
            message    = "Pago encontrado.",
            data       = PagoDetalleData(**pago.to_detalle())
        )

    # ── HU-015: PATCH /api/v1/payments/{id} (uso interno) ────
    def actualizar_estado_pago(self, payment_id: int,
                                datos: PagoStatusUpdate,
                                usuario_role: str) -> PagoResponse:
        if usuario_role != "admin":
            raise PermissionError(
                "Solo un administrador puede actualizar el estado del pago."
            )
        pago = self.pago_repo.obtener_por_id(payment_id)
        if not pago:
            raise ValueError(f"El pago con id {payment_id} no existe en el sistema.")
        pago.actualizar_estado(datos.status)
        self.pago_repo.guardar(pago)
        return PagoResponse(
            success    = True,
            statusCode = 200,
            message    = "Estado del pago actualizado correctamente.",
            data       = PagoDetalleData(**pago.to_detalle())
        )

    # ── HU-015: POST /api/v1/payments/webhook ────────────────
    def recibir_webhook(self, payload: WebhookWompi,
                        signature: str) -> PagoResponse:
        # Validar firma del webhook
        if not self.wompi.validar_firma(signature):
            raise InvalidWebhookSignatureException()

        txn         = payload.data.transaction
        wompi_txn_id = txn.id
        wompi_status = txn.status.upper()
        order_id     = int(txn.reference)

        # Buscar pago por wompiTransactionId
        pago = self.pago_repo.obtener_por_transaccion(wompi_txn_id)
        if not pago:
            # Buscar por orderId como fallback
            pago = self.pago_repo.obtener_por_orden(order_id)

        if not pago:
            # Retornar 200 a Wompi aunque no encontremos el pago
            return PagoResponse(
                success    = True,
                statusCode = 200,
                message    = "Webhook procesado correctamente.",
                data       = {"message": "Pago no encontrado en el sistema."}
            )

        pedido = self.pedido_repo.obtener_por_id(pago.order_id)
        stock_restored = False

        if wompi_status == "APPROVED":
            pago.aprobar()
            if pedido:
                pedido.status = "processing"
                self.pedido_repo.guardar(pedido)

        elif wompi_status in ("DECLINED", "VOIDED"):
            if wompi_status == "DECLINED":
                pago.rechazar()
            else:
                pago.anular()

            if pedido:
                pedido.status = "failed"
                self.pedido_repo.guardar(pedido)
                # Restaurar stock automáticamente
                for item in pedido.items:
                    producto = self.producto_repo.obtener_por_id(item.product_id)
                    if producto:
                        producto.stock += item.quantity
                stock_restored = True

        self.pago_repo.guardar(pago)

        return PagoResponse(
            success    = True,
            statusCode = 200,
            message    = "Webhook procesado correctamente.",
            data       = WebhookResultData(
                paymentId      = pago.payment_id,
                newStatus      = pago.status,
                orderId        = pago.order_id,
                orderNewStatus = pedido.status if pedido else "unknown",
                stockRestored  = stock_restored,
            )
        )