# ─────────────────────────────────────────────────────────────
# CAPA API — rutas HTTP con FastAPI
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status
from app.domain.usuarioDomain import UsuarioCreate, UsuarioLogin, UsuarioResponse, TokenResponse
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
            detail=str(e)
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
            detail=str(e)
        )


# ── POST /api/v1/users/login — Iniciar sesión ─────────────────
@router.post("/login", response_model=TokenResponse,
             status_code=status.HTTP_200_OK)
def login(datos: UsuarioLogin):
    """Inicia sesión y retorna token JWT."""
    try:
        return service.login(datos)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


# ── GET /api/v1/users — Listar usuarios ───────────────────────
@router.get("/", response_model=list[UsuarioResponse],
            status_code=status.HTTP_200_OK)
def listar_usuarios():
    """Retorna todos los usuarios registrados."""
    return service.listar()


# ── GET /api/v1/users/{id} — Consultar usuario ────────────────
@router.get("/{id}", response_model=UsuarioResponse,
            status_code=status.HTTP_200_OK)
def obtener_usuario(id: int):
    """Retorna un usuario por su ID."""
    try:
        return service.obtener(id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ── PUT /api/v1/users/{id} — Actualizar usuario ───────────────
@router.put("/{id}", response_model=UsuarioResponse,
            status_code=status.HTTP_200_OK)
def actualizar_usuario(id: int, datos: dict):
    """Actualiza los datos de un usuario."""
    try:
        return service.actualizar(id, datos)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ── DELETE /api/v1/users/{id} — Eliminar usuario ─────────────
@router.delete("/{id}", status_code=status.HTTP_200_OK)
def eliminar_usuario(id: int):
    """Elimina un usuario por ID. Solo administrador."""
    try:
        return service.eliminar(id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )