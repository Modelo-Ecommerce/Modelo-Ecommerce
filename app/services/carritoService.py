# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.carritoDomain import (
    CarritoItemAdd, CarritoItemUpdate, CarritoResponse, CarritoData, CarritoItemData,
    InsufficientStockException, ProductDiscontinuedException,
    CartItemLimitExceededException
)
from app.repositories.carritoRepository import CarritoRepository
from app.repositories.productoRepository import ProductoRepository


class CartService:

    def __init__(self, carrito_repo: CarritoRepository,
                 producto_repo: ProductoRepository):
        self.carrito_repo  = carrito_repo
        self.producto_repo = producto_repo

    def _carrito_a_response(self, carrito, message: str,
                             status_code: int) -> CarritoResponse:
        return CarritoResponse(
            success    = True,
            statusCode = status_code,
            message    = message,
            data       = CarritoData(
                cartId    = carrito.cart_id,
                userId    = carrito.user_id,
                items     = [CarritoItemData(**i.to_response())
                             for i in carrito.items.values()],
                itemCount = carrito.item_count,
                total     = carrito.total,
            )
        )

    # ── HU-007: POST /api/v1/carts/items ─────────────────────
    def agregar_item(self, datos: CarritoItemAdd,
                     usuario_token_id: int) -> CarritoResponse:
        if datos.userId != usuario_token_id:
            raise PermissionError(
                "No puedes agregar productos al carrito de otro usuario."
            )
        producto = self.producto_repo.obtener_por_id(datos.productId)
        if not producto:
            raise ValueError(f"Producto con id {datos.productId} no encontrado.")
        if not producto.esta_activo():
            raise ProductDiscontinuedException()
        if datos.quantity > producto.stock:
            raise InsufficientStockException(producto.name, producto.stock)

        carrito = self.carrito_repo.obtener_o_crear(datos.userId)
        carrito.agregar_item(
            product_id   = producto.id,
            product_name = producto.name,
            unit_price   = producto.price,
            quantity     = datos.quantity,
        )
        self.carrito_repo.guardar(carrito)
        return self._carrito_a_response(carrito, "Producto agregado al carrito.", 201)

    # ── HU-008: GET /api/v1/carts/{userId} ───────────────────
    def obtener_carrito(self, user_id: int,
                        usuario_token_id: int) -> CarritoResponse:
        if user_id != usuario_token_id:
            raise PermissionError("No puedes ver el carrito de otro usuario.")
        carrito = self.carrito_repo.obtener_por_usuario(user_id)
        if not carrito:
            raise ValueError(f"No existe carrito para el usuario {user_id}.")
        return self._carrito_a_response(carrito, "Carrito obtenido correctamente.", 200)

    # ── HU-008: PATCH /api/v1/carts/items/{id} ───────────────
    def actualizar_cantidad(self, item_id: int, datos: CarritoItemUpdate,
                            usuario_token_id: int) -> CarritoResponse:
        carrito = self.carrito_repo.obtener_por_usuario(usuario_token_id)
        if not carrito:
            raise ValueError("No existe carrito para este usuario.")

        # Buscar el ítem para obtener el producto y verificar stock
        item = carrito._buscar_item_por_id(item_id)
        if not item:
            raise ValueError(f"Ítem con id {item_id} no encontrado en el carrito.")

        producto = self.producto_repo.obtener_por_id(item.product_id)
        if datos.quantity > producto.stock:
            raise InsufficientStockException(producto.name, producto.stock)

        carrito.actualizar_cantidad(item_id, datos.quantity)
        self.carrito_repo.guardar(carrito)
        return self._carrito_a_response(carrito, "Cantidad actualizada correctamente.", 200)

    # ── HU-008: DELETE /api/v1/carts/items/{id} ──────────────
    def eliminar_item(self, item_id: int,
                      usuario_token_id: int) -> CarritoResponse:
        carrito = self.carrito_repo.obtener_por_usuario(usuario_token_id)
        if not carrito:
            raise ValueError("No existe carrito para este usuario.")
        carrito.eliminar_item(item_id)
        self.carrito_repo.guardar(carrito)
        return self._carrito_a_response(carrito, "Ítem eliminado del carrito.", 200)

    # ── Interno: vaciar carrito (lo llama OrderService) ───────
    def vaciar_carrito(self, user_id: int) -> None:
        carrito = self.carrito_repo.obtener_por_usuario(user_id)
        if carrito:
            carrito.vaciar()
            self.carrito_repo.guardar(carrito)