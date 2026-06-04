# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.pedidoDomain import (
    PedidoCreate, PedidoResponse, PedidoData, PedidoItemData,
    PedidoItem, Pedido,
    MinimumOrderAmountException, MinimumQuantityException,
    PaymentGatewayException, MIN_ORDER_AMOUNT, MIN_CART_QUANTITY
)
from app.domain.carritoDomain import InsufficientStockException
from app.repositories.pedidoRepository import PedidoRepository
from app.repositories.carritoRepository import CarritoRepository
from app.repositories.productoRepository import ProductoRepository


class PaymentService:
    """
    Servicio de pago — simula integración con Wompi.
    En producción llamaría a la API real de Wompi.
    """
    def procesar_pago(self, order_id: int, total: float,
                      payment_method: str) -> str:
        """
        Simula el inicio del pago y retorna la URL de checkout.
        Lanza PaymentGatewayException si falla.
        """
        # Simulación: siempre exitoso en desarrollo
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

        # Regla de negocio: userId debe coincidir con el token
        if datos.userId != usuario_token_id:
            raise PermissionError(
                "No puedes crear un pedido en nombre de otro usuario."
            )

        # Obtener el carrito
        carrito = self.carrito_repo.obtener_por_usuario(datos.userId)
        if not carrito or carrito.cart_id != datos.cartId:
            raise ValueError("El carrito no existe o no pertenece al usuario.")

        # Regla de dominio: mínimo de unidades
        if not carrito.cumple_minimo():
            raise MinimumQuantityException()

        # Regla de dominio: monto mínimo
        if carrito.total < MIN_ORDER_AMOUNT:
            raise MinimumOrderAmountException()

        # Verificar stock de todos los productos
        stock_reducido = []
        try:
            for item in carrito.items.values():
                producto = self.producto_repo.obtener_por_id(item.product_id)
                if not producto or producto.stock < item.quantity:
                    raise InsufficientStockException(
                        item.product_name,
                        producto.stock if producto else 0
                    )
                # Descontar stock
                producto.stock -= item.quantity
                stock_reducido.append((producto, item.quantity))

            # Crear ítems del pedido
            items_pedido = [
                PedidoItem(
                    product_id   = item.product_id,
                    product_name = item.product_name,
                    quantity     = item.quantity,
                    unit_price   = item.unit_price,
                )
                for item in carrito.items.values()
            ]

            # Crear el pedido con id temporal
            pedido = Pedido(
                order_id    = 0,
                user_id     = datos.userId,
                items       = items_pedido,
                payment_url = "",
            )
            pedido = self.pedido_repo.crear(pedido)

            # Iniciar pago vía PaymentService
            try:
                payment_url = self.payment_service.procesar_pago(
                    order_id       = pedido.order_id,
                    total          = pedido.total,
                    payment_method = datos.paymentMethod,
                )
                pedido.payment_url = payment_url
            except Exception:
                # Revertir stock y marcar pedido como fallido
                for producto, qty in stock_reducido:
                    producto.stock += qty
                pedido.marcar_fallido()
                self.pedido_repo.guardar(pedido)
                raise PaymentGatewayException()

            # Vaciar carrito automáticamente
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
            # Re-lanzar excepciones de dominio sin revertir stock
            # (el stock solo se revierte si ya fue descontado)
            raise
        except InsufficientStockException:
            # Revertir stock parcialmente descontado
            for producto, qty in stock_reducido:
                producto.stock += qty
            raise