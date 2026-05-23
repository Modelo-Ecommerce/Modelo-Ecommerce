# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad y sus reglas de negocio
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field, field_validator
from typing import Optional


# ── Schema de ENTRADA: Registrar usuario ─────────────────────
class UsuarioCreate(BaseModel):
    name:     str = Field(..., min_length=3, description="Nombre completo")
    email:    str = Field(..., description="Correo electrónico único")
    password: str = Field(..., min_length=8, description="Mínimo 8 caracteres")
    role:     str = Field(..., description="client o admin")
    phone:    str = Field(..., min_length=10, max_length=10)

    # ── REGLA DE NEGOCIO: teléfono colombiano ────────────────
    @field_validator("phone")
    @classmethod
    def telefono_colombiano(cls, v):
        if not v.isdigit() or not v.startswith("3") or len(v) != 10:
            raise ValueError("El teléfono debe ser colombiano: 10 dígitos e iniciar en 3")
        return v

    # ── REGLA DE NEGOCIO: rol válido ─────────────────────────
    @field_validator("role")
    @classmethod
    def rol_valido(cls, v):
        if v not in ["client", "admin"]:
            raise ValueError("El rol debe ser 'client' o 'admin'")
        return v


# ── Schema de ENTRADA: Login ──────────────────────────────────
class UsuarioLogin(BaseModel):
    email:    str = Field(..., description="Correo electrónico")
    password: str = Field(..., description="Contraseña")


# ── Schema de SALIDA: Respuesta de usuario ────────────────────
class UsuarioResponse(BaseModel):
    id:    int
    name:  str
    email: str
    role:  str
    createdAt: str = "2026-03-17"

    class Config:
        from_attributes = True


# ── Schema de SALIDA: Respuesta de login ──────────────────────
class TokenResponse(BaseModel):
    userId: int
    name:   str
    email:  str
    role:   str
    token:  str


# ── Modelo interno del dominio (la "entidad real") ────────────
class Usuario:
    def __init__(self, id: int, name: str, email: str,
                 phone: str, role: str, password: str):
        self.id       = id
        self.name     = name
        self.email    = email
        self.phone    = phone
        self.role     = role
        self.password = password
        self.status   = "active"
        self.createdAt = "2026-03-17"

    # REGLA DE NEGOCIO: usuario activo puede iniciar sesión
    def esta_activo(self) -> bool:
        return self.status == "active"

    # REGLA DE NEGOCIO: verificar contraseña
    def verificar_password(self, password: str) -> bool:
        return self.password == password

    def to_response(self) -> dict:
        return {
            "id":        self.id,
            "name":      self.name,
            "email":     self.email,
            "role":      self.role,
            "createdAt": self.createdAt,
        }