# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status
from app.domain.usuarioDomain import UsuarioLogin, UsuarioResponse
from app.services.usuarioService import UsuarioService
from app.services.dependencies import usuario_service as service

# Router con prefijo /api/v1/auth
router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


# ── POST /api/v1/auth/login — Iniciar sesión ──────────────────
@router.post("/login", response_model=UsuarioResponse,
             status_code=status.HTTP_200_OK)
def login(datos: UsuarioLogin):
    """Inicia sesión y retorna token JWT."""
    try:
        return service.login(datos)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success":    False,
                "statusCode": 403,
                "message":    str(e),
                "error": {
                    "error_code": "INACTIVE_USER",
                    "details":    str(e),
                    "timestamp":  "2026-03-17"
                }
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success":    False,
                "statusCode": 401,
                "message":    "Credenciales inválidas.",
                "error": {
                    "error_code": "INVALID_CREDENTIALS",
                    "details":    "El correo o la contraseña son incorrectos.",
                    "timestamp":  "2026-03-17"
                }
            }
        )