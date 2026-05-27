# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status
from app.domain.usuarioDomain import UsuarioCreate, UsuarioResponse
from app.services.usuarioService import UsuarioService
from app.repositories.usuarioRepository import usuario_repository

# Instanciar el servicio con inyección del repositorio
service = UsuarioService(repo=usuario_repository)

# Router con prefijo y etiqueta para la documentación
router = APIRouter(prefix="/api/v1/users", tags=["Usuarios"])


# ── POST /api/v1/users — Registrar usuario ────────────────────
@router.post("/", response_model=UsuarioResponse,
             status_code=status.HTTP_201_CREATED)
def registrar_usuario(datos: UsuarioCreate):
    """Registra un nuevo usuario en el sistema."""
    try:
        return service.registrar(datos)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success":    False,
                "statusCode": 409,
                "message":    "El correo electrónico ya está registrado.",
                "error": {
                    "error_code": "EMAIL_ALREADY_EXISTS",
                    "details":    str(e),
                    "timestamp":  "2026-03-17"
                }
            }
        )


# ── POST /api/v1/users/register — Alias del parcial ──────────
@router.post("/register", response_model=UsuarioResponse,
             status_code=status.HTTP_201_CREATED)
def registrar_usuario_alias(datos: UsuarioCreate):
    """Alias de /api/v1/users — mismo controlador."""
    try:
        return service.registrar(datos)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success":    False,
                "statusCode": 409,
                "message":    "El correo electrónico ya está registrado.",
                "error": {
                    "error_code": "EMAIL_ALREADY_EXISTS",
                    "details":    str(e),
                    "timestamp":  "2026-03-17"
                }
            }
        )