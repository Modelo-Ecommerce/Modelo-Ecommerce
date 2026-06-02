# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — Categorías
# Almacén en memoria con categorías precargadas.
# ─────────────────────────────────────────────────────────────


class CategoriaRepository:

    def __init__(self):
        # Categorías precargadas en memoria
        self._datos: dict[int, str] = {
            1: "Electrónica",
            2: "Ropa y Accesorios",
            3: "Computadores y Laptops",
            4: "Hogar y Jardín",
            5: "Deportes",
            6: "Libros",
            7: "Juguetes",
            8: "Alimentos",
        }

    def existe(self, id: int) -> bool:
        return id in self._datos

    def obtener_nombre(self, id: int) -> str:
        return self._datos.get(id, "")

    def obtener_todos(self) -> dict:
        return self._datos


# Instancia única compartida (Singleton simple)
categoria_repository = CategoriaRepository()