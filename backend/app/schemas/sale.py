from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import PaymentMethod, SaleStatus


class SaleItemCreate(BaseModel):
    """Línea de producto incluida en una solicitud de venta."""

    product_id: int = Field(..., gt=0, description="ID del producto a vender.", examples=[1])
    quantity: int = Field(..., gt=0, description="Cantidad de unidades vendidas.", examples=[2])
    use_wholesale: bool = Field(default=False, description="Indica si se aplica precio de mayoreo (si está configurado).")


class SaleCreate(BaseModel):
    """Solicitud para registrar una nueva venta en el POS."""

    customer_id: Optional[int] = Field(default=None, description="ID del cliente (opcional; null para Consumidor Final).", examples=[1])
    payment_method: PaymentMethod = Field(default=PaymentMethod.CASH, description="Método de pago utilizado.")
    card_bank: Optional[str] = Field(default=None, max_length=80, description="Banco emisor de la tarjeta (obligatorio si payment_method=CARD).", examples=["Banco Agrícola"])
    card_type: Optional[str] = Field(default=None, max_length=20, description="Tipo de tarjeta: CREDITO o DEBITO (obligatorio si payment_method=CARD).", examples=["CREDITO"])
    card_auth_number: Optional[str] = Field(default=None, max_length=60, description="Número de autorización del voucher (obligatorio si payment_method=CARD).", examples=["482910"])
    discount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2, description="Descuento total aplicado a la venta.", examples=["0.00"])
    amount_paid: Decimal = Field(..., ge=0, decimal_places=2, description="Monto entregado por el cliente.", examples=["10.00"])
    items: list[SaleItemCreate] = Field(..., min_length=1, description="Lista de productos y cantidades de la venta.")

    @model_validator(mode="after")
    def validate_card_fields(self) -> "SaleCreate":
        if self.payment_method == PaymentMethod.CARD:
            missing = [
                label
                for val, label in (
                    (self.card_bank, "Banco de la tarjeta"),
                    (self.card_type, "Tipo de tarjeta (CREDITO/DEBITO)"),
                    (self.card_auth_number, "Número de autorización"),
                )
                if not val or not val.strip()
            ]
            if missing:
                raise ValueError(
                    f"Para pagos con tarjeta son obligatorios: {', '.join(missing)}."
                )
        return self


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
    card_bank: Optional[str] = None
    card_type: Optional[str] = None
    card_auth_number: Optional[str] = None
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    amount_paid: Decimal
    change_amount: Decimal
    status: SaleStatus
    created_at: datetime
    items: list[SaleItemRead] = []

