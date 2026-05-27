# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — orquesta dominio + repositorio
# Contiene las reglas de negocio complejas y el flujo.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.usuarioDomain import UsuarioCreate, UsuarioResponse, UsuarioData
from app.repositories.usuarioRepository import UsuarioRepository


class UsuarioService:

    def __init__(self, repo: UsuarioRepository):
        # Inyección de dependencia: recibe el repositorio desde afuera
        self.repo = repo

    def registrar(self, datos: UsuarioCreate) -> UsuarioResponse:
        # Regla de aplicación: email no duplicado
        if self.repo.obtener_por_email(datos.email):
            raise ValueError(
                f"El correo {datos.email} ya está registrado"
            )

        # El repositorio encripta la contraseña con bcrypt
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