from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import Session, col, or_, select

from app.models.product import Category, Product
from app.schemas.product import CategoryCreate, ProductCreate, ProductUpdate


def list_categories(session: Session, active_only: bool = True) -> list[Category]:
    """Lista las categorías registradas."""
    stmt = select(Category).order_by(Category.name)
    if active_only:
        stmt = stmt.where(Category.is_active.is_(True))
    return list(session.exec(stmt).all())


def create_category(session: Session, payload: CategoryCreate) -> Category:
    """Crea una categoría verificando que su nombre sea único."""
    existing = session.exec(select(Category).where(Category.name == payload.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una categoría con el nombre '{payload.name}'.",
        )
    category = Category.model_validate(payload)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def list_products(
    session: Session,
    *,
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    active_only: bool = True,
    low_stock_only: bool = False,
) -> list[Product]:
    """Lista productos con filtros de búsqueda, categoría y stock bajo."""
    stmt = select(Product).order_by(Product.name)
    if active_only:
        stmt = stmt.where(Product.is_active.is_(True))
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if low_stock_only:
        stmt = stmt.where(Product.stock <= Product.min_stock)
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                col(Product.name).ilike(pattern),
                col(Product.sku).ilike(pattern),
                col(Product.barcode).ilike(pattern),
            )
        )
    return list(session.exec(stmt).all())


def get_product_or_404(session: Session, product_id: int) -> Product:
    """Obtiene un producto por ID o lanza HTTP 404."""
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con ID {product_id} no encontrado.",
        )
    return product


def create_product(session: Session, payload: ProductCreate) -> Product:
    """Crea un nuevo producto validando SKU único y categoría existente."""
    existing_sku = session.exec(select(Product).where(Product.sku == payload.sku)).first()
    if existing_sku:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un producto con el SKU '{payload.sku}'.",
        )
    if payload.category_id is not None and not session.get(Category, payload.category_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoría con ID {payload.category_id} no encontrada.",
        )

    product = Product.model_validate(payload)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def update_product(session: Session, product_id: int, payload: ProductUpdate) -> Product:
    """Actualiza parcialmente un producto existente."""
    product = get_product_or_404(session, product_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "sku" in update_data and update_data["sku"] != product.sku:
        dup = session.exec(select(Product).where(Product.sku == update_data["sku"])).first()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe otro producto con el SKU '{update_data['sku']}'.",
            )

    if update_data.get("category_id") is not None:
        if not session.get(Category, update_data["category_id"]):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoría con ID {update_data['category_id']} no encontrada.",
            )

    for key, value in update_data.items():
        setattr(product, key, value)
    product.updated_at = datetime.now(timezone.utc)

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def deactivate_product(session: Session, product_id: int) -> Product:
    """Desactiva lógicamente un producto (soft delete) para preservar historial de ventas."""
    product = get_product_or_404(session, product_id)
    product.is_active = False
    product.updated_at = datetime.now(timezone.utc)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

