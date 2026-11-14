from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import UserRole


class UserCreate(BaseModel):
    """Datos requeridos para registrar un usuario del POS."""

    name: str = Field(min_length=2, max_length=120, description="Nombre completo o usuario.")
    password: str = Field(min_length=4, max_length=128, description="Contraseña de acceso.")
    role: UserRole = Field(default=UserRole.CAJERO, description="Rol asignado (CAJERO o ENCARGADO).")

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("El nombre de usuario debe tener al menos 2 caracteres.")
        return cleaned


class UserUpdate(BaseModel):
    """Datos opcionales para actualizar un usuario."""

    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    password: Optional[str] = Field(default=None, max_length=128)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("El nombre de usuario debe tener al menos 2 caracteres.")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_optional_password(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if len(v) < 4:
            raise ValueError("La contraseña debe tener al menos 4 caracteres.")
        return v


class UserRead(BaseModel):
    """Representación pública de un usuario (sin hash de contraseña)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class LoginUserOption(BaseModel):
    """Opción resumida de usuario activo para selección rápida en pantalla de login."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    role: UserRole


class LoginRequest(BaseModel):
    """Credenciales de inicio de sesión."""

    user_id: Optional[int] = Field(default=None, description="ID del usuario seleccionado.")
    name: Optional[str] = Field(default=None, description="Nombre del usuario.")
    password: str = Field(min_length=1, description="Contraseña o PIN de acceso.")


class LoginResponse(BaseModel):
    """Respuesta de autenticación exitosa con token de sesión."""

    access_token: str
    token_type: str = "bearer"
    user: UserRead

