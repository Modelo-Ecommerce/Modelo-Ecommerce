# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — única responsabilidad: guardar y recuperar
# Solo manipula datos. Sin lógica de negocio aquí.
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.usuarioDomain import Usuario
from typing import Optional
import bcrypt



class UsuarioRepository:

    def __init__(self):
        # Almacén en memoria: diccionario de objetos Usuario
        self._datos: dict[int, Usuario] = {}
        self._siguiente_id: int = 1

    # ── CRUD básico ───────────────────────────────────────────

    def obtener_todos(self) -> list[Usuario]:
        return list(self._datos.values())

    def obtener_por_id(self, id: int) -> Optional[Usuario]:
        return self._datos.get(id)

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        return next(
            (u for u in self._datos.values() if u.email == email),
            None
        )

    def crear(self, name: str, email: str, phone: str,
            role: str, password: str) -> Usuario:
        # Encripta la contraseña con bcrypt antes de guardar
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        nuevo = Usuario(
            id       = self._siguiente_id,
            name     = name,
            email    = email,
            phone    = phone,
            role     = role,
            password = password_hash,
        )
        self._datos[self._siguiente_id] = nuevo
        self._siguiente_id += 1
        return nuevo

    def actualizar(self, id: int, data: dict) -> Optional[Usuario]:
        usuario = self._datos.get(id)
        if not usuario:
            return None
        for key, value in data.items():
            if hasattr(usuario, key):
                setattr(usuario, key, value)
        return usuario

    def eliminar(self, id: int) -> bool:
        if id in self._datos:
            del self._datos[id]
            return True
        return False
    
    def verificar_password(self, password: str, hash: str) -> bool:
        # Verifica la contraseña ingresada contra el hash almacenado (bcrypt)
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hash.encode("utf-8")
        )


# Instancia única compartida (Singleton simple)
usuario_repository = UsuarioRepository()