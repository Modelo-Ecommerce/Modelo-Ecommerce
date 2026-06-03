# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — única responsabilidad: guardar y recuperar
# Solo manipula datos. Sin lógica de negocio aquí.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from typing import Optional
from app.domain.productoDomain import Producto


class ProductoRepository:

    def __init__(self):
        self._datos: dict[int, Producto] = {}
        self._siguiente_id: int = 1

    def obtener_todos(self) -> list[Producto]:
        return list(self._datos.values())

    def obtener_por_id(self, id: int) -> Optional[Producto]:
        return self._datos.get(id)

    def crear(self, name: str, description: str, price: float,
              stock: int, categoryId: int) -> Producto:
        nuevo = Producto(
            id          = self._siguiente_id,
            name        = name,
            description = description,
            price       = price,
            stock       = stock,
            categoryId  = categoryId,
        )
        self._datos[self._siguiente_id] = nuevo
        self._siguiente_id += 1
        return nuevo

    def actualizar(self, id: int, data: dict) -> Optional[Producto]:
        producto = self._datos.get(id)
        if not producto:
            return None
        for key, value in data.items():
            if hasattr(producto, key):
                setattr(producto, key, value)
        return producto

    def actualizar_stock(self, id: int, stock: int) -> Optional[Producto]:
        producto = self._datos.get(id)
        if not producto:
            return None
        producto.stock = stock
        return producto

    def discontinuar(self, id: int) -> Optional[Producto]:
        """Soft-delete: cambia status a discontinued."""
        producto = self._datos.get(id)
        if not producto:
            return None
        producto.discontinuar()
        return producto

    def eliminar(self, id: int) -> bool:
        if id in self._datos:
            del self._datos[id]
            return True
        return False


# Instancia única compartida (Singleton simple)
producto_repository = ProductoRepository()