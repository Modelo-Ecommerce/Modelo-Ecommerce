# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.productoDomain import (
    ProductoCreate, ProductoUpdate, ProductoResponse, ProductoData,
    PriceBelowMinimumException, ProductHasActiveOrdersException
)
from app.repositories.productoRepository import ProductoRepository
from app.repositories.categoriaRepository import CategoriaRepository
from app.repositories.pedidoRepository import PedidoRepository


class InventoryService:
    """Inicializa y gestiona el stock."""
    def __init__(self, repo: ProductoRepository):
        self.repo = repo

    def inicializar_stock(self, producto_id: int, stock: int) -> None:
        self.repo.actualizar_stock(producto_id, stock)


class ProductoService:

    def __init__(self, repo: ProductoRepository,
                 categoria_repo: CategoriaRepository,
                 pedido_repo: PedidoRepository,
                 inventory_service: InventoryService):
        self.repo              = repo
        self.categoria_repo    = categoria_repo
        self.pedido_repo       = pedido_repo
        self.inventory_service = inventory_service

    # ── HU-004: POST /api/v1/products ────────────────────────
    def crear(self, datos: ProductoCreate, usuario_role: str) -> ProductoResponse:
        if usuario_role != "admin":
            raise PermissionError("Solo un administrador puede crear productos.")

        if not self.categoria_repo.existe(datos.categoryId):
            raise ValueError(f"La categoría con id {datos.categoryId} no existe.")

        p = self.repo.crear(
            name        = datos.name,
            description = datos.description,
            price       = datos.price,
            stock       = datos.stock,
            categoryId  = datos.categoryId,
        )

        self.inventory_service.inicializar_stock(p.id, datos.stock)

        return ProductoResponse(
            success    = True,
            statusCode = 201,
            message    = "Producto creado correctamente.",
            data       = ProductoData(**p.to_response())
        )

    # ── HU-005: DELETE /api/v1/products/{id} ─────────────────
    def eliminar(self, id: int, usuario_role: str) -> ProductoResponse:
        # Regla de negocio: solo admin
        if usuario_role != "admin":
            raise PermissionError("Solo un administrador puede eliminar productos.")

        # Regla de negocio: producto debe existir
        p = self.repo.obtener_por_id(id)
        if not p:
            raise ValueError(f"Producto con id {id} no encontrado.")

        # Regla de negocio: no puede tener pedidos activos
        if self.pedido_repo.tiene_pedidos_activos(id):
            raise ProductHasActiveOrdersException(id)

        # Soft-delete: status = "discontinued"
        p = self.repo.discontinuar(id)
        return ProductoResponse(
            success    = True,
            statusCode = 200,
            message    = "Producto eliminado correctamente.",
            data       = ProductoData(**p.to_response())
        )

    # ── HU-005: PUT /api/v1/products/{id} ────────────────────
    def actualizar(self, id: int, datos: ProductoUpdate,
                   usuario_role: str) -> ProductoResponse:
        # Regla de negocio: solo admin
        if usuario_role != "admin":
            raise PermissionError("Solo un administrador puede actualizar productos.")

        # Regla de negocio: producto debe existir
        p = self.repo.obtener_por_id(id)
        if not p:
            raise ValueError(f"Producto con id {id} no encontrado.")

        # Convertir solo los campos enviados (excluir None y stock)
        data = datos.model_dump(exclude_none=True)
        data.pop("stock", None)  # stock no se actualiza por este endpoint

        # Regla de negocio: categoryId debe existir si se envía
        if "categoryId" in data:
            if not self.categoria_repo.existe(data["categoryId"]):
                raise ValueError(
                    f"La categoría con id {data['categoryId']} no existe."
                )

        p = self.repo.actualizar(id, data)
        return ProductoResponse(
            success    = True,
            statusCode = 200,
            message    = "Producto actualizado correctamente.",
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