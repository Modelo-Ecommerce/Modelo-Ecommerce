# ─────────────────────────────────────────────────────────────
# DEPENDENCIAS COMPARTIDAS
# Instancias únicas compartidas entre todos los routers
# ─────────────────────────────────────────────────────────────

from app.repositories.usuarioRepository import usuario_repository
from app.services.usuarioService import UsuarioService

# Instancia única del servicio compartida entre todos los routers
usuario_service = UsuarioService(repo=usuario_repository)