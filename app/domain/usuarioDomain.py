# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — define la entidad y sus reglas de negocio
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from datetime import date


# ── Schema de ENTRADA: Registrar usuario ─────────────────────
class UsuarioCreate(BaseModel):
    name:     str = Field(..., min_length=3, description="Nombre completo")
    email:    str = Field(..., description="Correo electrónico único")
    password: str = Field(..., min_length=8, description="Mínimo 8 caracteres")
    role:     str = Field(default="client", description="client o admin")
    phone:    str = Field(..., min_length=10, max_length=10)

    # ── REGLA DE NEGOCIO: teléfono colombiano ────────────────
    @field_validator("phone")
    @classmethod
    def telefono_colombiano(cls, v):
        if not v.isdigit() or not v.startswith("3") or len(v) != 10:
            raise ValueError(
                "El teléfono debe ser colombiano: 10 dígitos e iniciar en 3"
            )
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

# ── Schema de ENTRADA: Actualizar perfil ─────────────────────
class UsuarioUpdate(BaseModel):
    name:  Optional[str] = Field(None, min_length=3, description="Nombre completo")
    email: Optional[str] = Field(None, description="Correo electrónico")
    phone: Optional[str] = Field(None, min_length=10, max_length=10)


# ── Schema de datos del usuario en la respuesta ───────────────
class UsuarioData(BaseModel):
    id:        int
    name:      str
    email:     str
    role:      str
    status:    str = "active"
    createdAt: str

    class Config:
        from_attributes = True

# ── Schema de datos del usuario actualizado en la respuesta ──
class UsuarioUpdateData(BaseModel):
    id:        int
    name:      str
    email:     str
    phone:     str
    role:      str
    updatedAt: str
 
    class Config:
        from_attributes = True


# ── Schema de datos del token en la respuesta ─────────────────
class TokenData(BaseModel):
    userId: int
    name:   str
    email:  str
    role:   str
    token:  str


# ── Schema de SALIDA: Respuesta estándar ─────────────────────
class UsuarioResponse(BaseModel):
    success:    bool
    statusCode: int
    message:    str
    data:       Optional[Any] = None


# ── Modelo interno del dominio (la "entidad real") ────────────
class Usuario:
    def __init__(self, id: int, name: str, email: str,
                 phone: str, role: str, password: str):
        self.id        = id
        self.name      = name
        self.email     = email
        self.phone     = phone
        self.role      = role
        self.password  = password
        self.status    = "active"
        self.createdAt = str(date.today())

    # REGLA DE NEGOCIO: usuario activo puede iniciar sesión
    def esta_activo(self) -> bool:
        return self.status == "active"

    def to_response(self) -> dict:
        return {
            "id":        self.id,
            "name":      self.name,
            "email":     self.email,
            "role":      self.role,
            "status":    self.status,
            "createdAt": self.createdAt,
        }
 
    def to_update_response(self) -> dict:
        return {
            "id":        self.id,
            "name":      self.name,
            "email":     self.email,
            "phone":     self.phone,
            "role":      self.role,
            "updatedAt": str(date.today()),
        }