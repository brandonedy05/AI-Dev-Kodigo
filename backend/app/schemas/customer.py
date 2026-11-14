from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import DocumentType

_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class CustomerCreate(BaseModel):
    """Datos para registrar un cliente en el directorio (El Salvador)."""

    full_name: str = Field(..., min_length=2, max_length=150, description="Nombre completo según documento.", examples=["Carlos Roberto Hernández Gómez"])
    customer_category: str = Field(default="PERSONAL", max_length=20, description="Clasificación: PERSONAL, TAXPAYER o FOREIGN.")
    country: str = Field(default="El Salvador", max_length=60, description="País de emisión del documento.")
    document_type: DocumentType = Field(default=DocumentType.DUI, description="Tipo de documento de identificación.")
    document_number: Optional[str] = Field(default=None, max_length=30, description="Número de DUI, NIT o pasaporte.", examples=["04512984-1"])

    nrc: Optional[str] = Field(default=None, max_length=30, description="NRC (Tarjeta de IVA).", examples=["284910-3"])
    business_name: Optional[str] = Field(default=None, max_length=150, description="Razón social según tarjeta de IVA.")
    economic_activity: Optional[str] = Field(default=None, max_length=200, description="Actividad económica o giro.")
    is_perception_agent: bool = Field(default=False, description="Aplica Percepción 1%.")
    is_retention_agent: bool = Field(default=False, description="Aplica Retención 1%.")

    department: Optional[str] = Field(default=None, max_length=60, description="Departamento (El Salvador).", examples=["San Salvador"])
    municipality: Optional[str] = Field(default=None, max_length=80, description="Municipio.", examples=["San Salvador Centro"])
    district: Optional[str] = Field(default=None, max_length=80, description="Distrito.", examples=["San Salvador"])
    address: Optional[str] = Field(default=None, max_length=255, description="Dirección detallada.")
    phone: Optional[str] = Field(default=None, max_length=30, description="Teléfono o WhatsApp.", examples=["+503 7890-1234"])
    email: Optional[str] = Field(
        default=None,
        max_length=150,
        pattern=_EMAIL_PATTERN,
        description="Correo electrónico opcional.",
        examples=["cliente@correo.com"],
    )

    credit_limit: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2, description="Límite de crédito en USD.")
    credit_days: int = Field(default=0, ge=0, description="Días plazo para pago.")

    @model_validator(mode="after")
    def validate_taxpayer_location(self) -> "CustomerCreate":
        if self.customer_category == "TAXPAYER":
            missing = [
                label
                for val, label in (
                    (self.department, "Departamento"),
                    (self.municipality, "Municipio"),
                    (self.district, "Distrito"),
                    (self.address, "Dirección detallada"),
                )
                if not val or not val.strip()
            ]
            if missing:
                raise ValueError(
                    f"Para clientes Contribuyentes la ubicación es obligatoria: falta {', '.join(missing)}."
                )
        return self


class CustomerUpdate(BaseModel):
    """Campos editables de un cliente."""

    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    customer_category: Optional[str] = Field(default=None, max_length=20)
    country: Optional[str] = Field(default=None, max_length=60)
    document_type: Optional[DocumentType] = None
    document_number: Optional[str] = Field(default=None, max_length=30)
    nrc: Optional[str] = Field(default=None, max_length=30)
    business_name: Optional[str] = Field(default=None, max_length=150)
    economic_activity: Optional[str] = Field(default=None, max_length=200)
    is_perception_agent: Optional[bool] = None
    is_retention_agent: Optional[bool] = None
    department: Optional[str] = Field(default=None, max_length=60)
    municipality: Optional[str] = Field(default=None, max_length=80)
    district: Optional[str] = Field(default=None, max_length=80)
    address: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=150, pattern=_EMAIL_PATTERN)
    credit_limit: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    credit_days: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class CustomerRead(BaseModel):
    """Representación pública de un cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    customer_category: str
    country: str
    document_type: DocumentType
    document_number: Optional[str]
    nrc: Optional[str]
    business_name: Optional[str]
    economic_activity: Optional[str]
    is_perception_agent: bool
    is_retention_agent: bool
    department: Optional[str]
    municipality: Optional[str]
    district: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    credit_limit: Decimal
    credit_days: int
    is_active: bool
    created_at: datetime
