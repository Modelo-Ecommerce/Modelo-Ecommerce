# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — Pedidos
# Almacén en memoria de pedidos reales.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from app.domain.pedidoDomain import Pedido


class PedidoRepository:

    def __init__(self):
        self._datos: dict[int, Pedido] = {}
        self._siguiente_id: int = 1

    def crear(self, pedido: Pedido) -> Pedido:
        pedido.order_id = self._siguiente_id
        self._datos[self._siguiente_id] = pedido
        self._siguiente_id += 1
        return pedido

    def obtener_por_id(self, id: int) -> Optional[Pedido]:
        return self._datos.get(id)

    def obtener_por_usuario(self, user_id: int) -> list[Pedido]:
        return [p for p in self._datos.values() if p.user_id == user_id]

    def tiene_pedidos_activos(self, producto_id: int) -> bool:
        """Verifica si un producto tiene pedidos pending o processing."""
        estados_activos = {"pending", "processing"}
        return any(
            any(item.product_id == producto_id for item in p.items)
            and p.status in estados_activos
            for p in self._datos.values()
        )

    def guardar(self, pedido: Pedido) -> Pedido:
        self._datos[pedido.order_id] = pedido
        return pedido


# Instancia única compartida (Singleton simple)
pedido_repository = PedidoRepository()