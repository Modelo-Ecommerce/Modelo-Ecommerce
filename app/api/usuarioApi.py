# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# HU-002: Registrar usuario
# HU-003: Gestión de perfil de usuario
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional
from app.domain.usuarioDomain import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from app.services.usuarioService import UsuarioService
from app.services.dependencies import usuario_service as service

router = APIRouter(prefix="/api/v1/users", tags=["Usuarios"])


def get_usuario_token(authorization: Optional[str] = None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False, "statusCode": 401,
                "message": "Token requerido.",
                "error": {"error_code": "UNAUTHORIZED"}
            }
        )
    token = authorization.replace("Bearer ", "").strip()
    try:
        user_id, role = token.split(":")
        return {"id": int(user_id), "role": role}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False, "statusCode": 401,
                "message": "Token inválido.",
                "error": {"error_code": "INVALID_TOKEN"}
            }
        )


# ── POST /api/v1/users ────────────────────────────────────────
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
                "success": False, "statusCode": 409,
                "message": "El correo electrónico ya está registrado.",
                "error": {
                    "error_code": "EMAIL_ALREADY_EXISTS",
                    "details": str(e),
                    "timestamp": "2026-03-17"
                }
            }
        )


# ── POST /api/v1/users/register — Alias ──────────────────────
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
                "success": False, "statusCode": 409,
                "message": "El correo electrónico ya está registrado.",
                "error": {
                    "error_code": "EMAIL_ALREADY_EXISTS",
                    "details": str(e),
                    "timestamp": "2026-03-17"
                }
            }
        )


# ── GET /api/v1/users/{id} ────────────────────────────────────
@router.get("/{id}", response_model=UsuarioResponse,
            status_code=status.HTTP_200_OK)
def obtener_usuario(id: int, authorization: Optional[str] = Header(None)):
    """Consulta los datos de un usuario. Requiere JWT."""
    get_usuario_token(authorization)
    try:
        return service.obtener(id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False, "statusCode": 404,
                "message": "Usuario no encontrado.",
                "error": {
                    "error_code": "USER_NOT_FOUND",
                    "details": str(e),
                    "timestamp": "2026-03-17"
                }
            }
        )


# ── PUT /api/v1/users/{id} ────────────────────────────────────
@router.put("/{id}", response_model=UsuarioResponse,
            status_code=status.HTTP_200_OK)
def actualizar_usuario(id: int, datos: UsuarioUpdate,
                       authorization: Optional[str] = Header(None)):
    """Actualiza nombre, email o teléfono. Requiere JWT."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.actualizar(
            id                  = id,
            datos               = datos,
            usuario_actual_id   = usuario_actual["id"],
            usuario_actual_role = usuario_actual["role"]
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False, "statusCode": 403,
                "message": str(e),
                "error": {"error_code": "FORBIDDEN"}
            }
        )
    except ValueError as e:
        error_str = str(e)
        if "no encontrado" in error_str:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False, "statusCode": 404,
                    "message": "Usuario no encontrado.",
                    "error": {"error_code": "USER_NOT_FOUND", "details": error_str}
                }
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False, "statusCode": 409,
                "message": "El correo ya está registrado.",
                "error": {"error_code": "EMAIL_ALREADY_EXISTS", "details": error_str}
            }
        )


# ── DELETE /api/v1/users/{id} ─────────────────────────────────
@router.delete("/{id}", response_model=UsuarioResponse,
               status_code=status.HTTP_200_OK)
def eliminar_usuario(id: int, authorization: Optional[str] = Header(None)):
    """Elimina un usuario. Solo administradores."""
    usuario_actual = get_usuario_token(authorization)
    try:
        return service.eliminar(
            id                  = id,
            usuario_actual_role = usuario_actual["role"]
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False, "statusCode": 403,
                "message": str(e),
                "error": {"error_code": "FORBIDDEN"}
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False, "statusCode": 404,
                "message": "Usuario no encontrado.",
                "error": {"error_code": "USER_NOT_FOUND", "details": str(e)}
            }
        )