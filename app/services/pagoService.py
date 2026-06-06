# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

import uuid
from app.domain.pagoDomain import (
    PagoCreate, PagoResponse, PagoData, PagoDetalleData, Pago,
    PaymentAmountMismatchException, PaymentAlreadyApprovedException,
    PaymentGatewayException
)
from app.repositories.pagoRepository import PagoRepository
from app.repositories.pedidoRepository import PedidoRepository


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


class PaymentService:

    def __init__(self, pago_repo: PagoRepository,
                 pedido_repo: PedidoRepository,
                 wompi_service: WompiService):
        self.pago_repo   = pago_repo
        self.pedido_repo = pedido_repo
        self.wompi       = wompi_service

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
            raise PermissionError(
                "El pedido no pertenece al usuario autenticado."
            )
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
            raise ValueError(
                f"El pago con id {payment_id} no existe en el sistema."
            )

        # Regla de negocio: cliente solo ve sus propios pagos
        if usuario_role == "client" and pago.user_id != usuario_token_id:
            raise PermissionError(
                "No tienes permiso para consultar este pago."
            )

        return PagoResponse(
            success    = True,
            statusCode = 200,
            message    = "Pago encontrado.",
            data       = PagoDetalleData(**pago.to_detalle())
        )