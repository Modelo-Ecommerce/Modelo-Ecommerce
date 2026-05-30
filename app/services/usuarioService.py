# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.usuarioDomain import UsuarioCreate, UsuarioLogin, UsuarioResponse, UsuarioData, TokenData
from app.repositories.usuarioRepository import UsuarioRepository


class UsuarioService:

    def __init__(self, repo: UsuarioRepository):
        # Inyección de dependencia: recibe el repositorio desde afuera
        self.repo = repo

    def listar(self) -> list[UsuarioResponse]:
        return [UsuarioResponse(
            success    = True,
            statusCode = 200,
            message    = "Lista de usuarios.",
            data       = UsuarioData(**u.to_response())
        ) for u in self.repo.obtener_todos()]

    def obtener(self, id: int) -> UsuarioResponse:
        u = self.repo.obtener_por_id(id)
        if not u:
            raise ValueError(f"Usuario con id {id} no encontrado")
        return UsuarioResponse(
            success    = True,
            statusCode = 200,
            message    = "Usuario encontrado.",
            data       = UsuarioData(**u.to_response())
        )

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

            # Retorna respuesta estándar con datos del usuario (sin contraseña)
            return UsuarioResponse(
                success    = True,
                statusCode = 201,
                message    = "Usuario registrado correctamente.",
                data       = UsuarioData(**u.to_response())
            )

    def login(self, datos: UsuarioLogin) -> UsuarioResponse:
        u = self.repo.obtener_por_email(datos.email)

        # Regla de negocio: credenciales inválidas
        if not u or not self.repo.verificar_password(datos.password, u.password):
            raise ValueError("Credenciales inválidas")

        # Regla de negocio: InactiveUserException
        if not u.esta_activo():
            raise PermissionError(
                "El usuario se encuentra inactivo y no puede iniciar sesión."
            )

        return UsuarioResponse(
            success    = True,
            statusCode = 200,
            message    = "Inicio de sesión exitoso.",
            data       = TokenData(
                userId = u.id,
                name   = u.name,
                email  = u.email,
                role   = u.role,
                token  = "jwt-token-simulado",
            )
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

    def actualizar(self, id: int, data: dict) -> UsuarioResponse:
        if "email" in data:
            existente = self.repo.obtener_por_email(data["email"])
            if existente and existente.id != id:
                raise ValueError(
                    f"El correo {data['email']} ya está registrado por otro usuario"
                )
        u = self.repo.actualizar(id, data)
        if not u:
            raise ValueError(f"Usuario con id {id} no encontrado")
        return UsuarioResponse(
            success    = True,
            statusCode = 200,
            message    = "Usuario actualizado correctamente.",
            data       = UsuarioData(**u.to_response())
        )