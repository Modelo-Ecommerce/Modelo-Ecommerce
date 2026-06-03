# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — Carrito
# Almacén en memoria: un carrito por usuario.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from app.domain.carritoDomain import Carrito


class CarritoRepository:

    def __init__(self):
        # Un carrito por usuario: { user_id → Carrito }
        self._datos: dict[int, Carrito] = {}
        self._siguiente_cart_id: int = 1

    def obtener_por_usuario(self, user_id: int) -> Optional[Carrito]:
        return self._datos.get(user_id)

    def obtener_o_crear(self, user_id: int) -> Carrito:
        """Retorna el carrito existente o crea uno nuevo."""
        if user_id not in self._datos:
            self._datos[user_id] = Carrito(
                cart_id = self._siguiente_cart_id,
                user_id = user_id,
            )
            self._siguiente_cart_id += 1
        return self._datos[user_id]

    def guardar(self, carrito: Carrito) -> Carrito:
        self._datos[carrito.user_id] = carrito
        return carrito


# Instancia única compartida (Singleton simple)
carrito_repository = CarritoRepository()