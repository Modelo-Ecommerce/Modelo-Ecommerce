# ─────────────────────────────────────────────────────────────
# DEPENDENCIAS COMPARTIDAS
# Instancias únicas compartidas entre todos los routers
# ─────────────────────────────────────────────────────────────

from app.repositories.usuarioRepository import usuario_repository
from app.services.usuarioService import UsuarioService

from app.repositories.productoRepository import producto_repository
from app.repositories.categoriaRepository import categoria_repository
from app.services.productoService import ProductoService, InventoryService

# ── Usuarios ──────────────────────────────────────────────────
usuario_service = UsuarioService(repo=usuario_repository)

# ── Productos ─────────────────────────────────────────────────
inventory_service = InventoryService(repo=producto_repository)
producto_service  = ProductoService(
    repo              = producto_repository,
    categoria_repo    = categoria_repository,
    inventory_service = inventory_service,
)