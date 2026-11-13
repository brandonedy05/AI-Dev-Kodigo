from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.common import ErrorResponse
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.services import customer_service

router = APIRouter(prefix="/customers", tags=["Clientes"])


@router.get(
    "",
    response_model=list[CustomerRead],
    summary="Listar clientes",
    description="Obtiene el directorio de clientes con búsqueda por nombre, DUI/NIT o teléfono.",
)
def list_customers(
    search: Optional[str] = Query(default=None, description="Texto de búsqueda."),
    active_only: bool = Query(default=True, description="Filtrar solo clientes activos."),
    session: Session = Depends(get_session),
):
    return customer_service.list_customers(session, search=search, active_only=active_only)


@router.get(
    "/{customer_id}",
    response_model=CustomerRead,
    summary="Obtener cliente",
    description="Consulta los datos de un cliente por su ID.",
    responses={404: {"model": ErrorResponse, "description": "Cliente no encontrado."}},
)
def get_customer(
    customer_id: int,
    session: Session = Depends(get_session),
):
    return customer_service.get_customer_or_404(session, customer_id)


@router.post(
    "",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar cliente",
    description="Crea un nuevo cliente validando que el número de documento no esté repetido.",
    responses={409: {"model": ErrorResponse, "description": "Documento duplicado."}},
)
def create_customer(
    payload: CustomerCreate,
    session: Session = Depends(get_session),
):
    return customer_service.create_customer(session, payload)


@router.patch(
    "/{customer_id}",
    response_model=CustomerRead,
    summary="Actualizar cliente",
    description="Actualiza parcialmente la información de un cliente.",
    responses={
        404: {"model": ErrorResponse, "description": "Cliente no encontrado."},
        409: {"model": ErrorResponse, "description": "Documento duplicado."},
    },
)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    session: Session = Depends(get_session),
):
    return customer_service.update_customer(session, customer_id, payload)


@router.delete(
    "/{customer_id}",
    response_model=CustomerRead,
    summary="Desactivar cliente",
    description="Desactiva un cliente del directorio sin borrar sus ventas históricas.",
    responses={404: {"model": ErrorResponse, "description": "Cliente no encontrado."}},
)
def delete_customer(
    customer_id: int,
    session: Session = Depends(get_session),
):
    return customer_service.deactivate_customer(session, customer_id)

