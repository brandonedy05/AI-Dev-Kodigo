from datetime import date, datetime, time, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.enums import SaleStatus
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.schemas.report import (
    LowStockProductItem,
    PaymentMethodBreakdown,
    SalesSummaryReport,
    TopProductReportItem,
)


def _date_range_utc(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    return start_dt, end_dt


def get_sales_summary(
    session: Session, start_date: date, end_date: date
) -> SalesSummaryReport:
    """Agrega ventas completadas en el rango de fechas indicado."""
    start_dt, end_dt = _date_range_utc(start_date, end_date)

    stmt = (
        select(
            Sale.payment_method,
            func.count(Sale.id),
            func.coalesce(func.sum(Sale.total), Decimal("0.00")),
        )
        .where(Sale.status == SaleStatus.COMPLETED)
        .where(Sale.created_at >= start_dt)
        .where(Sale.created_at <= end_dt)
        .group_by(Sale.payment_method)
    )
    rows = session.exec(stmt).all()

    breakdown: list[PaymentMethodBreakdown] = []
    total_transactions = 0
    total_revenue = Decimal("0.00")

    for payment_method, count, amount in rows:
        amount_dec = Decimal(amount).quantize(Decimal("0.01"))
        breakdown.append(
            PaymentMethodBreakdown(
                payment_method=payment_method,
                transactions_count=int(count),
                total_amount=amount_dec,
            )
        )
        total_transactions += int(count)
        total_revenue += amount_dec

    average_ticket = (
        (total_revenue / total_transactions).quantize(Decimal("0.01"))
        if total_transactions > 0
        else Decimal("0.00")
    )

    return SalesSummaryReport(
        start_date=start_date,
        end_date=end_date,
        total_transactions=total_transactions,
        total_revenue=total_revenue.quantize(Decimal("0.01")),
        average_ticket=average_ticket,
        by_payment_method=breakdown,
    )


def get_top_products(
    session: Session, start_date: date, end_date: date, limit: int = 10
) -> list[TopProductReportItem]:
    """Calcula los productos más vendidos por unidades e ingresos."""
    start_dt, end_dt = _date_range_utc(start_date, end_date)

    stmt = (
        select(
            SaleItem.product_id,
            SaleItem.product_name,
            func.sum(SaleItem.quantity).label("units_sold"),
            func.sum(SaleItem.line_total).label("total_revenue"),
        )
        .join(Sale, Sale.id == SaleItem.sale_id)
        .where(Sale.status == SaleStatus.COMPLETED)
        .where(Sale.created_at >= start_dt)
        .where(Sale.created_at <= end_dt)
        .group_by(SaleItem.product_id, SaleItem.product_name)
        .order_by(func.sum(SaleItem.quantity).desc())
        .limit(limit)
    )

    rows = session.exec(stmt).all()
    return [
        TopProductReportItem(
            product_id=int(product_id),
            product_name=str(product_name),
            units_sold=int(units_sold),
            total_revenue=Decimal(total_revenue).quantize(Decimal("0.01")),
        )
        for product_id, product_name, units_sold, total_revenue in rows
    ]


def get_low_stock_products(session: Session) -> list[LowStockProductItem]:
    """Lista productos activos con stock igual o inferior a su umbral mínimo."""
    stmt = (
        select(Product)
        .where(Product.is_active.is_(True))
        .where(Product.stock <= Product.min_stock)
        .order_by(Product.stock.asc(), Product.name.asc())
    )
    products = session.exec(stmt).all()
    return [
        LowStockProductItem(
            product_id=p.id,  # type: ignore[arg-type]
            sku=p.sku,
            name=p.name,
            stock=p.stock,
            min_stock=p.min_stock,
            price=p.price,
        )
        for p in products
    ]

