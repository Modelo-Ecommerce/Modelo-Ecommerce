# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.carritoDomain import (
    CarritoItemAdd, CarritoResponse, CarritoData, CarritoItemData,
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

    # ── HU-007: POST /api/v1/carts/items ─────────────────────
    def agregar_item(self, datos: CarritoItemAdd,
                     usuario_token_id: int) -> CarritoResponse:

        # Regla de negocio: userId debe coincidir con el token
        if datos.userId != usuario_token_id:
            raise PermissionError(
                "No puedes agregar productos al carrito de otro usuario."
            )

        # Regla de negocio: producto debe existir
        producto = self.producto_repo.obtener_por_id(datos.productId)
        if not producto:
            raise ValueError(f"Producto con id {datos.productId} no encontrado.")

        # Regla de dominio: producto no puede estar discontinued
        if not producto.esta_activo():
            raise ProductDiscontinuedException()

        # Regla de dominio: stock suficiente (CartService → InventoryService)
        if datos.quantity > producto.stock:
            raise InsufficientStockException(producto.name, producto.stock)

        # Obtener o crear carrito del usuario
        carrito = self.carrito_repo.obtener_o_crear(datos.userId)

        # Regla de dominio: agregar ítem (suma si ya existe, lanza si supera límite)
        carrito.agregar_item(
            product_id   = producto.id,
            product_name = producto.name,
            unit_price   = producto.price,
            quantity     = datos.quantity,
        )

        self.carrito_repo.guardar(carrito)

        return CarritoResponse(
            success    = True,
            statusCode = 201,
            message    = "Producto agregado al carrito.",
            data       = CarritoData(
                cartId = carrito.cart_id,
                userId = carrito.user_id,
                items  = [
                    CarritoItemData(**item.to_response())
                    for item in carrito.items.values()
                ],
                total  = carrito.total,
            )
        )

    # ── GET carrito del usuario ───────────────────────────────
    def obtener_carrito(self, user_id: int,
                        usuario_token_id: int) -> CarritoResponse:
        if user_id != usuario_token_id:
            raise PermissionError("No puedes ver el carrito de otro usuario.")

        carrito = self.carrito_repo.obtener_por_usuario(user_id)
        if not carrito:
            raise ValueError(f"No existe carrito para el usuario {user_id}.")

        return CarritoResponse(
            success    = True,
            statusCode = 200,
            message    = "Carrito obtenido correctamente.",
            data       = CarritoData(
                cartId = carrito.cart_id,
                userId = carrito.user_id,
                items  = [
                    CarritoItemData(**item.to_response())
                    for item in carrito.items.values()
                ],
                total  = carrito.total,
            )
        )