# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.productoDomain import (
    ProductoCreate, ProductoResponse, ProductoData, PriceBelowMinimumException
)
from app.repositories.productoRepository import ProductoRepository
from app.repositories.categoriaRepository import CategoriaRepository


class InventoryService:
    """
    Servicio de inventario — inicializa y gestiona el stock.
    ProductService lo llama automáticamente al crear un producto.
    """
    def __init__(self, repo: ProductoRepository):
        self.repo = repo

    def inicializar_stock(self, producto_id: int, stock: int) -> None:
        """Inicializa el stock de un producto recién creado."""
        self.repo.actualizar_stock(producto_id, stock)


class ProductoService:

    def __init__(self, repo: ProductoRepository,
                 categoria_repo: CategoriaRepository,
                 inventory_service: InventoryService):
        self.repo              = repo
        self.categoria_repo    = categoria_repo
        self.inventory_service = inventory_service

    # ── HU-004: POST /api/v1/products ────────────────────────
    def crear(self, datos: ProductoCreate, usuario_role: str) -> ProductoResponse:
        # Regla de negocio: solo admin puede crear productos
        if usuario_role != "admin":
            raise PermissionError("Solo un administrador puede crear productos.")

        # Regla de negocio: categoryId debe existir
        # (PriceBelowMinimumException ya fue lanzada por Pydantic al validar)
        if not self.categoria_repo.existe(datos.categoryId):
            raise ValueError(f"La categoría con id {datos.categoryId} no existe.")

        # Crear el producto
        p = self.repo.crear(
            name        = datos.name,
            description = datos.description,
            price       = datos.price,
            stock       = datos.stock,
            categoryId  = datos.categoryId,
        )

        # Llamar automáticamente a InventoryService para inicializar stock
        self.inventory_service.inicializar_stock(p.id, datos.stock)

        return ProductoResponse(
            success    = True,
            statusCode = 201,
            message    = "Producto creado correctamente.",
            data       = ProductoData(**p.to_response())
        )

    def listar(self) -> ProductoResponse:
        productos = self.repo.obtener_todos()
        return ProductoResponse(
            success    = True,
            statusCode = 200,
            message    = "Lista de productos.",
            data       = [ProductoData(**p.to_response()) for p in productos]
        )

    def obtener(self, id: int) -> ProductoResponse:
        p = self.repo.obtener_por_id(id)
        if not p:
            raise ValueError(f"Producto con id {id} no encontrado.")
        return ProductoResponse(
            success    = True,
            statusCode = 200,
            message    = "Producto encontrado.",
            data       = ProductoData(**p.to_response())
        )