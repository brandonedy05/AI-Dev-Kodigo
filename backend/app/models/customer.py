from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import DocumentType

if TYPE_CHECKING:
    from app.models.sale import Sale


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Customer(SQLModel, table=True):
    """Cliente registrado en el directorio de la tienda."""

    __tablename__ = "customers"

    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str = Field(max_length=150, index=True)
    document_type: DocumentType = Field(default=DocumentType.DUI, max_length=20)
    document_number: Optional[str] = Field(default=None, max_length=30, unique=True, index=True)
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default=None, max_length=150)
    address: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    sales: list["Sale"] = Relationship(back_populates="customer")

