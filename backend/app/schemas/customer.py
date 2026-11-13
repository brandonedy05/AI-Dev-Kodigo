from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentType

_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class CustomerCreate(BaseModel):
    """Datos para registrar un cliente en el directorio."""

    full_name: str = Field(..., min_length=2, max_length=150, description="Nombre completo o razón social.", examples=["María Elena Hernández"])
    document_type: DocumentType = Field(default=DocumentType.DUI, description="Tipo de documento de identificación.")
    document_number: Optional[str] = Field(default=None, max_length=30, description="Número de DUI, NIT o pasaporte.", examples=["04512984-1"])
    phone: Optional[str] = Field(default=None, max_length=30, description="Teléfono de contacto.", examples=["7890-1234"])
    email: Optional[str] = Field(
        default=None,
        max_length=150,
        pattern=_EMAIL_PATTERN,
        description="Correo electrónico opcional.",
        examples=["maria@ejemplo.com"],
    )
    address: Optional[str] = Field(default=None, max_length=255, description="Dirección física opcional.")


class CustomerUpdate(BaseModel):
    """Campos editables de un cliente."""

    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    document_type: Optional[DocumentType] = None
    document_number: Optional[str] = Field(default=None, max_length=30)
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=150, pattern=_EMAIL_PATTERN)
    address: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class CustomerRead(BaseModel):
    """Representación pública de un cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    document_type: DocumentType
    document_number: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    is_active: bool
    created_at: datetime

