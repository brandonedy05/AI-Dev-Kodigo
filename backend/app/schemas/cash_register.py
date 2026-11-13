from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CashMovementType, CashSessionStatus


class CashOpenRequest(BaseModel):
    """Solicitud para abrir un turno de caja."""

    cashier_name: str = Field(..., min_length=2, max_length=100, description="Nombre del cajero responsable.", examples=["Carlos Mendoza"])
    opening_amount: Decimal = Field(..., ge=0, decimal_places=2, description="Fondo inicial de efectivo en caja.", examples=["100.00"])
    notes: Optional[str] = Field(default=None, max_length=255, description="Observaciones iniciales del turno.")


class CashMovementCreate(BaseModel):
    """Solicitud para registrar un ingreso o egreso manual de efectivo."""

    movement_type: CashMovementType = Field(..., description="Tipo de movimiento (INCOME o EXPENSE).")
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Monto del movimiento en USD.", examples=["25.00"])
    reason: str = Field(..., min_length=3, max_length=255, description="Motivo o concepto del movimiento.", examples=["Pago a proveedor de pan"])


class CashCloseRequest(BaseModel):
    """Solicitud para cerrar la sesión de caja activa."""

    closing_amount: Decimal = Field(..., ge=0, decimal_places=2, description="Efectivo físico contado al cierre.", examples=["345.50"])
    notes: Optional[str] = Field(default=None, max_length=255, description="Notas de cierre o explicación de diferencia.")


class CashMovementRead(BaseModel):
    """Representación de un movimiento de caja."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    movement_type: CashMovementType
    amount: Decimal
    reason: str
    reference_sale_id: Optional[int]
    created_at: datetime


class CashSessionRead(BaseModel):
    """Representación de una sesión de caja."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cashier_name: str
    opening_amount: Decimal
    closing_amount: Optional[Decimal]
    expected_amount: Optional[Decimal]
    difference: Optional[Decimal]
    status: CashSessionStatus
    notes: Optional[str]
    opened_at: datetime
    closed_at: Optional[datetime]


class CashSessionSummary(BaseModel):
    """Resumen en tiempo real de la sesión de caja abierta."""

    session: CashSessionRead
    cash_sales_total: Decimal
    income_total: Decimal
    expense_total: Decimal
    expected_cash_in_drawer: Decimal
    movements: list[CashMovementRead]

