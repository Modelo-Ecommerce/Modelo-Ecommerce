# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.usuarioDomain import UsuarioCreate, UsuarioLogin, UsuarioResponse, TokenResponse
from app.repositories.usuarioRepository import UsuarioRepository


class UsuarioService:

    def __init__(self, repo: UsuarioRepository):
        # Inyección de dependencia: recibe el repositorio desde afuera
        self.repo = repo

    def listar(self) -> list[UsuarioResponse]:
        return [UsuarioResponse(**u.to_response())
                for u in self.repo.obtener_todos()]

    def obtener(self, id: int) -> UsuarioResponse:
        u = self.repo.obtener_por_id(id)
        if not u:
            raise ValueError(f"Usuario con id {id} no encontrado")
        return UsuarioResponse(**u.to_response())

    def registrar(self, datos: UsuarioCreate) -> UsuarioResponse:
        # Regla de aplicación: email no duplicado
        if self.repo.obtener_por_email(datos.email):
            raise ValueError(f"El correo {datos.email} ya está registrado")

        u = self.repo.crear(
            name     = datos.name,
            email    = datos.email,
            phone    = datos.phone,
            role     = datos.role,
            password = datos.password,
        )
        return UsuarioResponse(**u.to_response())

    def login(self, datos: UsuarioLogin) -> TokenResponse:
        u = self.repo.obtener_por_email(datos.email)

        # Regla de negocio: credenciales inválidas
        if not u or not u.verificar_password(datos.password):
            raise ValueError("Credenciales inválidas")

        # Regla de negocio: InactiveUserException
        if not u.esta_activo():
            raise PermissionError(
                "El usuario se encuentra inactivo y no puede iniciar sesión."
            )

        return TokenResponse(
            userId = u.id,
            name   = u.name,
            email  = u.email,
            role   = u.role,
            token  = "jwt-token-simulado",
        )

    def actualizar(self, id: int, data: dict) -> UsuarioResponse:
        # Regla de aplicación: email no duplicado en otro usuario
        if "email" in data:
            existente = self.repo.obtener_por_email(data["email"])
            if existente and existente.id != id:
                raise ValueError(
                    f"El correo {data['email']} ya está registrado por otro usuario"
                )

        u = self.repo.actualizar(id, data)
        if not u:
            raise ValueError(f"Usuario con id {id} no encontrado")
        return UsuarioResponse(**u.to_response())

    def eliminar(self, id: int) -> dict:
        ok = self.repo.eliminar(id)
        if not ok:
            raise ValueError(f"Usuario con id {id} no encontrado")
        return {"mensaje": f"Usuario {id} eliminado correctamente"}