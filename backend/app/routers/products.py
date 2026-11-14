import base64
import binascii
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import require_manager_if_authenticated
from app.schemas.common import ErrorResponse
from app.schemas.product import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    ProductCreate,
    ProductImageUploadRequest,
    ProductImageUploadResponse,
    ProductRead,
    ProductUpdate,
)
from app.services import product_service

router = APIRouter(tags=["Catálogo y Productos"])

_ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
_MAX_IMAGE_BYTES = 5 * 1024 * 1024
_UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads" / "products"


@router.post(
    "/products/upload-image",
    response_model=ProductImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_manager_if_authenticated)],
    summary="Subir imagen de producto",
    description="Recibe una imagen en base64, la guarda localmente en el servidor y devuelve su ruta pública.",
    responses={400: {"model": ErrorResponse, "description": "Formato o tamaño de imagen inválido."}},
)
def upload_product_image(payload: ProductImageUploadRequest):
    ext = Path(payload.filename).suffix.lower()
    if ext not in _ALLOWED_IMAGE_EXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de imagen no soportado ({ext or 'sin extensión'}). Usa PNG, JPG, WEBP o GIF.",
        )

    raw_b64 = payload.content_base64.split(",", 1)[-1]
    try:
        data = base64.b64decode(raw_b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El contenido base64 de la imagen no es válido.",
        ) from exc

    if len(data) == 0 or len(data) > _MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La imagen debe pesar entre 1 byte y 5 MB.",
        )

    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved_name = f"{uuid4().hex}{ext}"
    (_UPLOAD_DIR / saved_name).write_bytes(data)
    return ProductImageUploadResponse(image_url=f"/uploads/products/{saved_name}")


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
    dependencies=[Depends(require_manager_if_authenticated)],
    summary="Crear categoría",
    description="Registra una nueva categoría de productos.",
    responses={409: {"model": ErrorResponse, "description": "Nombre de categoría duplicado."}},
)
def create_category(
    payload: CategoryCreate,
    session: Session = Depends(get_session),
):
    return product_service.create_category(session, payload)


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryRead,
    dependencies=[Depends(require_manager_if_authenticated)],
    summary="Actualizar categoría",
    description="Actualiza el nombre o descripción de una categoría existente.",
    responses={
        404: {"model": ErrorResponse, "description": "Categoría no encontrada."},
        409: {"model": ErrorResponse, "description": "Nombre de categoría duplicado."},
    },
)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    session: Session = Depends(get_session),
):
    return product_service.update_category(session, category_id, payload)


@router.delete(
    "/categories/{category_id}",
    response_model=CategoryRead,
    dependencies=[Depends(require_manager_if_authenticated)],
    summary="Desactivar categoría",
    description="Desactiva una categoría (soft delete) sin borrar los productos vinculados.",
    responses={404: {"model": ErrorResponse, "description": "Categoría no encontrada."}},
)
def delete_category(
    category_id: int,
    session: Session = Depends(get_session),
):
    return product_service.deactivate_category(session, category_id)


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
    dependencies=[Depends(require_manager_if_authenticated)],
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
    dependencies=[Depends(require_manager_if_authenticated)],
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
    dependencies=[Depends(require_manager_if_authenticated)],
    summary="Desactivar producto",
    description="Desactiva un producto del catálogo (soft delete) preservando el historial de ventas.",
    responses={404: {"model": ErrorResponse, "description": "Producto no encontrado."}},
)
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
):
    return product_service.deactivate_product(session, product_id)

