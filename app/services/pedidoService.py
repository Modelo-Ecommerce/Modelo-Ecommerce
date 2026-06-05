# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.pedidoDomain import (
    PedidoCreate, PedidoResponse, PedidoData, PedidoItemData,
    PedidoDetalleData, PagoData, DireccionEnvio,
    PedidoItem, Pedido,
    MinimumOrderAmountException, MinimumQuantityException,
    PaymentGatewayException, MIN_ORDER_AMOUNT
)
from app.domain.carritoDomain import InsufficientStockException
from app.repositories.pedidoRepository import PedidoRepository
from app.repositories.carritoRepository import CarritoRepository
from app.repositories.productoRepository import ProductoRepository


class PaymentService:
    """Simula integración con Wompi."""
    def procesar_pago(self, order_id: int, total: float,
                      payment_method: str) -> str:
        return (
            f"https://checkout.wompi.co/p/"
            f"?public-key=pub_test_demo"
            f"&currency=COP"
            f"&amount-in-cents={int(total * 100)}"
            f"&reference=ORDER-{order_id}"
            f"&payment-method={payment_method}"
        )


class OrderService:

    def __init__(self, pedido_repo: PedidoRepository,
                 carrito_repo: CarritoRepository,
                 producto_repo: ProductoRepository,
                 payment_service: PaymentService):
        self.pedido_repo     = pedido_repo
        self.carrito_repo    = carrito_repo
        self.producto_repo   = producto_repo
        self.payment_service = payment_service

    # ── HU-009: POST /api/v1/orders ──────────────────────────
    def crear_pedido(self, datos: PedidoCreate,
                     usuario_token_id: int) -> PedidoResponse:

        if datos.userId != usuario_token_id:
            raise PermissionError(
                "No puedes crear un pedido en nombre de otro usuario."
            )

        carrito = self.carrito_repo.obtener_por_usuario(datos.userId)
        if not carrito or carrito.cart_id != datos.cartId:
            raise ValueError("El carrito no existe o no pertenece al usuario.")

        if not carrito.cumple_minimo():
            raise MinimumQuantityException()

        if carrito.total < MIN_ORDER_AMOUNT:
            raise MinimumOrderAmountException()

        stock_reducido = []
        try:
            for item in carrito.items.values():
                producto = self.producto_repo.obtener_por_id(item.product_id)
                if not producto or producto.stock < item.quantity:
                    raise InsufficientStockException(
                        item.product_name,
                        producto.stock if producto else 0
                    )
                producto.stock -= item.quantity
                stock_reducido.append((producto, item.quantity))

            items_pedido = [
                PedidoItem(
                    product_id   = item.product_id,
                    product_name = item.product_name,
                    quantity     = item.quantity,
                    unit_price   = item.unit_price,
                )
                for item in carrito.items.values()
            ]

            # Guardar dirección de envío en el pedido
            shipping = datos.shippingAddress.model_dump()

            pedido = Pedido(
                order_id         = 0,
                user_id          = datos.userId,
                items            = items_pedido,
                payment_url      = "",
                shipping_address = shipping,
            )
            pedido = self.pedido_repo.crear(pedido)

            try:
                payment_url = self.payment_service.procesar_pago(
                    order_id       = pedido.order_id,
                    total          = pedido.total,
                    payment_method = datos.paymentMethod,
                )
                pedido.payment_url = payment_url
            except Exception:
                for producto, qty in stock_reducido:
                    producto.stock += qty
                pedido.marcar_fallido()
                self.pedido_repo.guardar(pedido)
                raise PaymentGatewayException()

            carrito.vaciar()
            self.carrito_repo.guardar(carrito)
            self.pedido_repo.guardar(pedido)

            return PedidoResponse(
                success    = True,
                statusCode = 201,
                message    = "Pedido creado correctamente.",
                data       = PedidoData(
                    orderId    = pedido.order_id,
                    userId     = pedido.user_id,
                    status     = pedido.status,
                    total      = pedido.total,
                    paymentUrl = pedido.payment_url,
                    createdAt  = pedido.createdAt,
                    items      = [PedidoItemData(**i.to_response())
                                  for i in pedido.items],
                )
            )

        except (MinimumOrderAmountException, MinimumQuantityException,
                PermissionError, ValueError, PaymentGatewayException):
            raise
        except InsufficientStockException:
            for producto, qty in stock_reducido:
                producto.stock += qty
            raise

    # ── HU-010: GET /api/v1/orders/{id} ──────────────────────
    def obtener_pedido(self, order_id: int,
                       usuario_token_id: int,
                       usuario_role: str) -> PedidoResponse:

        pedido = self.pedido_repo.obtener_por_id(order_id)
        if not pedido:
            raise ValueError(f"El pedido con id {order_id} no existe en el sistema.")

        # Regla de negocio: cliente solo ve sus propios pedidos
        if usuario_role == "client" and pedido.user_id != usuario_token_id:
            raise PermissionError(
                "No tienes permiso para ver este pedido."
            )

        return PedidoResponse(
            success    = True,
            statusCode = 200,
            message    = "Pedido encontrado.",
            data       = PedidoDetalleData(
                orderId         = pedido.order_id,
                userId          = pedido.user_id,
                status          = pedido.status,
                total           = pedido.total,
                payment         = PagoData(
                    paymentId = pedido.payment_id,
                    status    = pedido.payment_status,
                ),
                shippingAddress = DireccionEnvio(
                    **pedido.shipping_address
                ),
                items           = [PedidoItemData(**i.to_response())
                                   for i in pedido.items],
                createdAt       = pedido.createdAt,
            )
        )