from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import DocumentType

if TYPE_CHECKING:
    from app.models.sale import Sale


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Customer(SQLModel, table=True):
    """Cliente registrado en el directorio de la tienda (El Salvador)."""

    __tablename__ = "customers"

    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str = Field(max_length=150, index=True)
    customer_category: str = Field(default="PERSONAL", max_length=20, index=True)
    country: str = Field(default="El Salvador", max_length=60)
    document_type: DocumentType = Field(default=DocumentType.DUI, max_length=20)
    document_number: Optional[str] = Field(default=None, max_length=30, unique=True, index=True)

    # Datos fiscales (Tarjeta de IVA / Contribuyente)
    nrc: Optional[str] = Field(default=None, max_length=30, index=True)
    business_name: Optional[str] = Field(default=None, max_length=150)
    economic_activity: Optional[str] = Field(default=None, max_length=200)
    is_perception_agent: bool = Field(default=False)
    is_retention_agent: bool = Field(default=False)

    # Ubicación (El Salvador) y contacto
    department: Optional[str] = Field(default=None, max_length=60)
    municipality: Optional[str] = Field(default=None, max_length=80)
    district: Optional[str] = Field(default=None, max_length=80)
    address: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=150)

    # Crédito / Fiado
    credit_limit: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(12, 2), nullable=False))
    credit_days: int = Field(default=0)

    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    sales: list["Sale"] = Relationship(back_populates="customer")
