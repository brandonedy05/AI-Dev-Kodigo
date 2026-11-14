from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Column, DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.sale import SaleItem


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Category(SQLModel, table=True):
    """Categoría de productos de la tienda."""

    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=80, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    products: list["Product"] = Relationship(back_populates="category")


class Product(SQLModel, table=True):
    """Producto vendible en el catálogo del POS."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_products_price_non_negative"),
        CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),
        CheckConstraint("min_stock >= 0", name="ck_products_min_stock_non_negative"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(max_length=40, unique=True, index=True)
    barcode: Optional[str] = Field(default=None, max_length=64, index=True)
    name: str = Field(max_length=150, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    image_url: Optional[str] = Field(default=None, max_length=500)
    unit_of_measure: str = Field(default="Unidad", max_length=30)
    price: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    cost_price: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    wholesale_price: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(12, 2), nullable=True),
    )
    applies_iva: bool = Field(default=True)
    stock: int = Field(default=0)
    min_stock: int = Field(default=5)
    location: Optional[str] = Field(default=None, max_length=80)
    supplier_name: Optional[str] = Field(default=None, max_length=120)
    supplier_code: Optional[str] = Field(default=None, max_length=60)
    is_active: bool = Field(default=True, index=True)
    category_id: Optional[int] = Field(
        default=None,
        foreign_key="categories.id",
        index=True,
    )
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    category: Optional[Category] = Relationship(back_populates="products")
    sale_items: list["SaleItem"] = Relationship(back_populates="product")

