from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Column, DateTime, Numeric
from sqlmodel import Field, Relationship, SQLModel

from app.models.enums import CashMovementType, CashSessionStatus

if TYPE_CHECKING:
    from app.models.sale import Sale


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CashRegisterSession(SQLModel, table=True):
    """Turno o sesión de caja (apertura, movimientos y cierre)."""

    __tablename__ = "cash_register_sessions"
    __table_args__ = (
        CheckConstraint("opening_amount >= 0", name="ck_cash_session_opening_non_negative"),
        CheckConstraint(
            "closing_amount IS NULL OR closing_amount >= 0",
            name="ck_cash_session_closing_non_negative",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    cashier_name: str = Field(max_length=100, index=True)
    opening_amount: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    closing_amount: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(12, 2), nullable=True),
    )
    expected_amount: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(12, 2), nullable=True),
    )
    difference: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(12, 2), nullable=True),
    )
    status: CashSessionStatus = Field(default=CashSessionStatus.OPEN, index=True, max_length=20)
    notes: Optional[str] = Field(default=None, max_length=255)
    opened_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    closed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    movements: list["CashMovement"] = Relationship(back_populates="session")
    sales: list["Sale"] = Relationship(back_populates="session")


class CashMovement(SQLModel, table=True):
    """Movimiento individual de efectivo dentro de una sesión de caja."""

    __tablename__ = "cash_movements"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_cash_movement_amount_positive"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="cash_register_sessions.id", index=True)
    movement_type: CashMovementType = Field(max_length=20, index=True)
    amount: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    reason: str = Field(max_length=255)
    reference_sale_id: Optional[int] = Field(default=None, foreign_key="sales.id", index=True)
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )

    session: Optional[CashRegisterSession] = Relationship(back_populates="movements")

