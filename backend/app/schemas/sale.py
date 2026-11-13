from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PaymentMethod, SaleStatus


class SaleItemCreate(BaseModel):
    """Línea de producto incluida en una solicitud de venta."""

    product_id: int = Field(..., gt=0, description="ID del producto a vender.", examples=[1])
    quantity: int = Field(..., gt=0, description="Cantidad de unidades vendidas.", examples=[2])


class SaleCreate(BaseModel):
    """Solicitud para registrar una nueva venta en el POS."""

    customer_id: Optional[int] = Field(default=None, description="ID del cliente (opcional; null para Consumidor Final).", examples=[1])
    payment_method: PaymentMethod = Field(default=PaymentMethod.CASH, description="Método de pago utilizado.")
    discount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2, description="Descuento total aplicado a la venta.", examples=["0.00"])
    amount_paid: Decimal = Field(..., ge=0, decimal_places=2, description="Monto entregado por el cliente.", examples=["10.00"])
    items: list[SaleItemCreate] = Field(..., min_length=1, description="Lista de productos y cantidades de la venta.")


class SaleItemRead(BaseModel):
    """Detalle de una línea de venta registrada."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class SaleRead(BaseModel):
    """Representación completa de una venta con sus líneas de detalle."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_number: str
    session_id: int
    customer_id: Optional[int]
    payment_method: PaymentMethod
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    amount_paid: Decimal
    change_amount: Decimal
    status: SaleStatus
    created_at: datetime
    items: list[SaleItemRead] = []

