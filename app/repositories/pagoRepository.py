# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — Pagos
# Almacén en memoria de pagos.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from app.domain.pagoDomain import Pago


class PagoRepository:

    def __init__(self):
        self._datos: dict[int, Pago] = {}
        self._siguiente_id: int = 1
        self._por_orden:     dict[int, int] = {}  # orderId → paymentId
        self._por_transaccion: dict[str, int] = {}  # wompiTxnId → paymentId

    def crear(self, pago: Pago) -> Pago:
        pago.payment_id = self._siguiente_id
        self._datos[self._siguiente_id]               = pago
        self._por_orden[pago.order_id]                = self._siguiente_id
        self._por_transaccion[pago.wompi_transaction_id] = self._siguiente_id
        self._siguiente_id += 1
        return pago

    def obtener_por_id(self, payment_id: int) -> Optional[Pago]:
        return self._datos.get(payment_id)

    def obtener_por_orden(self, order_id: int) -> Optional[Pago]:
        payment_id = self._por_orden.get(order_id)
        return self._datos.get(payment_id) if payment_id else None

    def obtener_por_transaccion(self, wompi_txn_id: str) -> Optional[Pago]:
        payment_id = self._por_transaccion.get(wompi_txn_id)
        return self._datos.get(payment_id) if payment_id else None

    def guardar(self, pago: Pago) -> Pago:
        self._datos[pago.payment_id] = pago
        return pago


# Instancia única compartida (Singleton simple)
pago_repository = PagoRepository()