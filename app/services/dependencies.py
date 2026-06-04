# ─────────────────────────────────────────────────────────────
# DEPENDENCIAS COMPARTIDAS
# Instancias únicas compartidas entre todos los routers
# ─────────────────────────────────────────────────────────────

from app.repositories.usuarioRepository import usuario_repository
from app.services.usuarioService import UsuarioService

from app.repositories.productoRepository import producto_repository
from app.repositories.categoriaRepository import categoria_repository
from app.repositories.pedidoRepository import pedido_repository
from app.services.productoService import ProductoService, InventoryService

from app.repositories.carritoRepository import carrito_repository
from app.services.carritoService import CartService

from app.services.pedidoService import OrderService, PaymentService

# ── Usuarios ──────────────────────────────────────────────────
usuario_service = UsuarioService(repo=usuario_repository)

# ── Productos ─────────────────────────────────────────────────
inventory_service = InventoryService(repo=producto_repository)
producto_service  = ProductoService(
    repo              = producto_repository,
    categoria_repo    = categoria_repository,
    pedido_repo       = pedido_repository,
    inventory_service = inventory_service,
)

# ── Carrito ───────────────────────────────────────────────────
cart_service = CartService(
    carrito_repo  = carrito_repository,
    producto_repo = producto_repository,
)

# ── Pedidos ───────────────────────────────────────────────────
payment_service = PaymentService()
order_service   = OrderService(
    pedido_repo     = pedido_repository,
    carrito_repo    = carrito_repository,
    producto_repo   = producto_repository,
    payment_service = payment_service,
)