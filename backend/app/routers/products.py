from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.common import ErrorResponse
from app.schemas.product import (
    CategoryCreate,
    CategoryRead,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)
from app.services import product_service

router = APIRouter(tags=["Catálogo y Productos"])


@router.get(
    "/categories",
    response_model=list[CategoryRead],
    summary="Listar categorías",
    description="Obtiene las categorías de productos registradas en la tienda.",
)
def list_categories(
    active_only: bool = Query(default=True, description="Filtrar solo categorías activas."),
    session: Session = Depends(get_session),
):
    return product_service.list_categories(session, active_only=active_only)


@router.post(
    "/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear categoría",
    description="Registra una nueva categoría de productos.",
    responses={409: {"model": ErrorResponse, "description": "Nombre de categoría duplicado."}},
)
def create_category(
    payload: CategoryCreate,
    session: Session = Depends(get_session),
):
    return product_service.create_category(session, payload)


@router.get(
    "/products",
    response_model=list[ProductRead],
    summary="Listar productos",
    description="Lista productos del catálogo con filtros opcionales por búsqueda, categoría o stock bajo.",
)
def list_products(
    search: Optional[str] = Query(default=None, description="Buscar por nombre, SKU o código de barras."),
    category_id: Optional[int] = Query(default=None, description="Filtrar por ID de categoría."),
    active_only: bool = Query(default=True, description="Incluir solo productos activos."),
    low_stock_only: bool = Query(default=False, description="Incluir solo productos con stock <= stock mínimo."),
    session: Session = Depends(get_session),
):
    return product_service.list_products(
        session,
        search=search,
        category_id=category_id,
        active_only=active_only,
        low_stock_only=low_stock_only,
    )


@router.get(
    "/products/{product_id}",
    response_model=ProductRead,
    summary="Obtener producto",
    description="Obtiene el detalle de un producto por su ID.",
    responses={404: {"model": ErrorResponse, "description": "Producto no encontrado."}},
)
def get_product(
    product_id: int,
    session: Session = Depends(get_session),
):
    return product_service.get_product_or_404(session, product_id)


@router.post(
    "/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear producto",
    description="Registra un nuevo producto en el catálogo validando SKU único.",
    responses={
        404: {"model": ErrorResponse, "description": "Categoría asociada no encontrada."},
        409: {"model": ErrorResponse, "description": "SKU duplicado."},
    },
)
def create_product(
    payload: ProductCreate,
    session: Session = Depends(get_session),
):
    return product_service.create_product(session, payload)


@router.patch(
    "/products/{product_id}",
    response_model=ProductRead,
    summary="Actualizar producto",
    description="Actualiza parcialmente los datos, precio o stock de un producto.",
    responses={
        404: {"model": ErrorResponse, "description": "Producto o categoría no encontrada."},
        409: {"model": ErrorResponse, "description": "SKU duplicado."},
    },
)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    session: Session = Depends(get_session),
):
    return product_service.update_product(session, product_id, payload)


@router.delete(
    "/products/{product_id}",
    response_model=ProductRead,
    summary="Desactivar producto",
    description="Desactiva un producto del catálogo (soft delete) preservando el historial de ventas.",
    responses={404: {"model": ErrorResponse, "description": "Producto no encontrado."}},
)
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
):
    return product_service.deactivate_product(session, product_id)

