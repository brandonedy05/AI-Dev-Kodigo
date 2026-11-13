from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.common import ErrorResponse
from app.schemas.sale import SaleCreate, SaleRead
from app.services import sale_service

router = APIRouter(prefix="/sales", tags=["Ventas"])


@router.post(
    "",
    response_model=SaleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar venta",
    description=(
        "Registra una nueva venta validando que exista una sesión de caja abierta, "
        "que haya stock suficiente para cada producto, calculando totales y vuelto, "
        "y descontando el inventario de forma atómica."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Descuento inválido o monto pagado insuficiente."},
        404: {"model": ErrorResponse, "description": "Producto o cliente no encontrado."},
        409: {"model": ErrorResponse, "description": "Caja cerrada o stock insuficiente."},
    },
)
def create_sale(
    payload: SaleCreate,
    session: Session = Depends(get_session),
):
    return sale_service.create_sale(session, payload)


@router.get(
    "",
    response_model=list[SaleRead],
    summary="Listar ventas recientes",
    description="Obtiene las ventas más recientes registradas en el POS junto con sus líneas.",
)
def list_sales(
    limit: int = Query(default=50, ge=1, le=200, description="Cantidad máxima de ventas a listar."),
    session: Session = Depends(get_session),
):
    return sale_service.list_sales(session, limit=limit)


@router.get(
    "/{sale_id}",
    response_model=SaleRead,
    summary="Obtener detalle de venta",
    description="Devuelve una venta específica con su desglose de productos.",
    responses={404: {"model": ErrorResponse, "description": "Venta no encontrada."}},
)
def get_sale(
    sale_id: int,
    session: Session = Depends(get_session),
):
    return sale_service.get_sale_or_404(session, sale_id)

