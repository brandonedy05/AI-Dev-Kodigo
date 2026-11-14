from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Column, DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import PaymentMethod, SaleStatus

if TYPE_CHECKING:
    from app.models.cash_register import CashRegisterSession
    from app.models.customer import Customer
    from app.models.product import Product


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Sale(SQLModel, table=True):
    """Cabecera de una venta registrada en el POS."""

    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="ck_sales_subtotal_non_negative"),
        CheckConstraint("discount >= 0", name="ck_sales_discount_non_negative"),
        CheckConstraint("total >= 0", name="ck_sales_total_non_negative"),
        CheckConstraint("amount_paid >= 0", name="ck_sales_amount_paid_non_negative"),
        CheckConstraint("change_amount >= 0", name="ck_sales_change_non_negative"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_number: str = Field(max_length=32, unique=True, index=True)
    session_id: int = Field(foreign_key="cash_register_sessions.id", index=True)
    customer_id: Optional[int] = Field(default=None, foreign_key="customers.id", index=True)
    payment_method: PaymentMethod = Field(default=PaymentMethod.CASH, max_length=20, index=True)
    card_bank: Optional[str] = Field(default=None, max_length=80)
    card_type: Optional[str] = Field(default=None, max_length=20)
    card_auth_number: Optional[str] = Field(default=None, max_length=60)
    subtotal: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    discount: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(12, 2), nullable=False))
    total: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    amount_paid: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    change_amount: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(12, 2), nullable=False))
    status: SaleStatus = Field(default=SaleStatus.COMPLETED, max_length=20, index=True)
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )

    session: Optional["CashRegisterSession"] = Relationship(back_populates="sales")
    customer: Optional["Customer"] = Relationship(back_populates="sales")
    items: list["SaleItem"] = Relationship(back_populates="sale")


class SaleItem(SQLModel, table=True):
    """Línea de detalle de una venta."""

    __tablename__ = "sale_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sale_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_sale_items_unit_price_non_negative"),
        CheckConstraint("line_total >= 0", name="ck_sale_items_line_total_non_negative"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    sale_id: int = Field(foreign_key="sales.id", index=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    product_name: str = Field(max_length=150)
    quantity: int = Field(nullable=False)
    unit_price: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    line_total: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))

    sale: Optional[Sale] = Relationship(back_populates="items")
    product: Optional["Product"] = Relationship(back_populates="sale_items")

