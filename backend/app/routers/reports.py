from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import require_manager_if_authenticated
from app.schemas.common import ErrorResponse
from app.schemas.report import (
    LowStockProductItem,
    SalesSummaryReport,
    TopProductReportItem,
)
from app.services import report_service

router = APIRouter(
    prefix="/reports",
    tags=["Reportes"],
    dependencies=[Depends(require_manager_if_authenticated)],
)


def _resolve_dates(start_date: Optional[date], end_date: Optional[date]) -> tuple[date, date]:
    today = datetime.now(timezone.utc).date()
    start = start_date or today
    end = end_date or today
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date no puede ser posterior a end_date.",
        )
    return start, end


@router.get(
    "/sales-summary",
    response_model=SalesSummaryReport,
    summary="Resumen de ventas",
    description="Calcula ingresos totales, cantidad de ventas, ticket promedio y desglose por método de pago.",
    responses={400: {"model": ErrorResponse, "description": "Rango de fechas inválido."}},
)
def sales_summary(
    start_date: Optional[date] = Query(default=None, description="Fecha inicial (YYYY-MM-DD). Por defecto hoy."),
    end_date: Optional[date] = Query(default=None, description="Fecha final (YYYY-MM-DD). Por defecto hoy."),
    session: Session = Depends(get_session),
):
    start, end = _resolve_dates(start_date, end_date)
    return report_service.get_sales_summary(session, start, end)


@router.get(
    "/top-products",
    response_model=list[TopProductReportItem],
    summary="Productos más vendidos",
    description="Lista los productos con mayor cantidad de unidades vendidas en el rango de fechas.",
    responses={400: {"model": ErrorResponse, "description": "Rango de fechas inválido."}},
)
def top_products(
    start_date: Optional[date] = Query(default=None, description="Fecha inicial (YYYY-MM-DD). Por defecto hoy."),
    end_date: Optional[date] = Query(default=None, description="Fecha final (YYYY-MM-DD). Por defecto hoy."),
    limit: int = Query(default=10, ge=1, le=50, description="Cantidad máxima de productos."),
    session: Session = Depends(get_session),
):
    start, end = _resolve_dates(start_date, end_date)
    return report_service.get_top_products(session, start, end, limit=limit)


@router.get(
    "/low-stock",
    response_model=list[LowStockProductItem],
    summary="Alertas de stock bajo",
    description="Devuelve los productos activos cuyo stock actual es menor o igual a su stock mínimo.",
)
def low_stock(session: Session = Depends(get_session)):
    return report_service.get_low_stock_products(session)

