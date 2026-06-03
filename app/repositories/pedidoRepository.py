# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — Pedidos (stub para HU-005)
# Contiene pedidos de prueba precargados para validar
# que no existan pedidos activos al eliminar un producto.
# Será reemplazado cuando se implemente la HU de pedidos.
# ─────────────────────────────────────────────────────────────


class PedidoRepository:

    def __init__(self):
        # Pedidos de prueba precargados
        # Formato: { pedido_id: { "productId": int, "status": str } }
        self._datos: dict[int, dict] = {
            1: {"productId": 99, "status": "pending"},
            2: {"productId": 99, "status": "processing"},
            3: {"productId": 98, "status": "completed"},
        }

    def tiene_pedidos_activos(self, producto_id: int) -> bool:
        """
        Verifica si un producto tiene pedidos en estado
        'pending' o 'processing'.
        El producto con id 99 tiene pedidos activos (para probar el 409).
        Cualquier otro producto NO tiene pedidos activos.
        """
        estados_activos = {"pending", "processing"}
        return any(
            p["productId"] == producto_id and p["status"] in estados_activos
            for p in self._datos.values()
        )


# Instancia única compartida (Singleton simple)
pedido_repository = PedidoRepository()