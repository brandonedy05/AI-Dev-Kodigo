from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import PaymentMethod


class PaymentMethodBreakdown(BaseModel):
    """Totales agrupados por método de pago."""

    payment_method: PaymentMethod
    transactions_count: int
    total_amount: Decimal


class SalesSummaryReport(BaseModel):
    """Reporte agregado de ventas para un rango de fechas."""

    start_date: date
    end_date: date
    total_transactions: int
    total_revenue: Decimal
    average_ticket: Decimal
    by_payment_method: list[PaymentMethodBreakdown]


class TopProductReportItem(BaseModel):
    """Producto más vendido dentro del período consultado."""

    product_id: int
    product_name: str
    units_sold: int
    total_revenue: Decimal


class LowStockProductItem(BaseModel):
    """Producto cuyo stock actual es menor o igual al stock mínimo."""

    product_id: int
    sku: str
    name: str
    stock: int
    min_stock: int
    price: Decimal = Field(..., description="Precio unitario actual.")

