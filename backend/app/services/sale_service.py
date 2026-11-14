from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.models.cash_register import CashMovement
from app.models.customer import Customer
from app.models.enums import CashMovementType, PaymentMethod, SaleStatus
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.schemas.sale import SaleCreate
from app.services.cash_register_service import require_open_session


def _generate_ticket_number() -> str:
    """Genera un número de ticket legible y único."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = uuid4().hex[:6].upper()
    return f"TKT-{stamp}-{suffix}"


def create_sale(session: Session, payload: SaleCreate) -> Sale:
    """Registra una venta validando caja abierta, stock suficiente y montos de pago."""
    cash_session = require_open_session(session)

    if payload.customer_id is not None:
        customer = session.get(Customer, payload.customer_id)
        if not customer or not customer.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente con ID {payload.customer_id} no encontrado o inactivo.",
            )

    # Agrupar cantidades por producto para validar stock acumulado si hay líneas repetidas.
    requested_qty: dict[int, int] = defaultdict(int)
    for item in payload.items:
        requested_qty[item.product_id] += item.quantity

    stmt = (
        select(Product)
        .where(Product.id.in_(list(requested_qty.keys())))  # type: ignore[union-attr]
        .with_for_update()
    )
    products_by_id = {p.id: p for p in session.exec(stmt).all()}

    subtotal = Decimal("0.00")
    sale_items: list[SaleItem] = []

    for product_id, total_qty in requested_qty.items():
        product = products_by_id.get(product_id)
        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {product_id} no encontrado o inactivo.",
            )
        if product.stock < total_qty:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Stock insuficiente para '{product.name}' (SKU {product.sku}): "
                    f"solicitado {total_qty}, disponible {product.stock}."
                ),
            )

    now = datetime.now(timezone.utc)
    for item in payload.items:
        product = products_by_id[item.product_id]
        unit_price = (
            product.wholesale_price
            if item.use_wholesale and product.wholesale_price is not None
            else product.price
        )
        line_total = (unit_price * item.quantity).quantize(Decimal("0.01"))
        subtotal += line_total
        product.stock -= item.quantity
        product.updated_at = now

        sale_items.append(
            SaleItem(
                product_id=product.id,  # type: ignore[arg-type]
                product_name=product.name,
                quantity=item.quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )

    if payload.discount > subtotal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El descuento ({payload.discount}) no puede superar el subtotal ({subtotal}).",
        )

    total = (subtotal - payload.discount).quantize(Decimal("0.01"))
    if payload.amount_paid < total:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El monto pagado ({payload.amount_paid}) es menor al total ({total}).",
        )

    change_amount = (
        (payload.amount_paid - total).quantize(Decimal("0.01"))
        if payload.payment_method == PaymentMethod.CASH
        else Decimal("0.00")
    )

    is_card = payload.payment_method == PaymentMethod.CARD
    sale = Sale(
        ticket_number=_generate_ticket_number(),
        session_id=cash_session.id,  # type: ignore[arg-type]
        customer_id=payload.customer_id,
        payment_method=payload.payment_method,
        card_bank=payload.card_bank.strip() if is_card and payload.card_bank else None,
        card_type=payload.card_type.strip().upper() if is_card and payload.card_type else None,
        card_auth_number=payload.card_auth_number.strip() if is_card and payload.card_auth_number else None,
        subtotal=subtotal,
        discount=payload.discount,
        total=total,
        amount_paid=payload.amount_paid,
        change_amount=change_amount,
        status=SaleStatus.COMPLETED,
        items=sale_items,
    )
    session.add(sale)
    session.flush()

    if payload.payment_method == PaymentMethod.CASH and total > Decimal("0.00"):
        cash_movement = CashMovement(
            session_id=cash_session.id,  # type: ignore[arg-type]
            movement_type=CashMovementType.SALE,
            amount=total,
            reason=f"Venta {sale.ticket_number}",
            reference_sale_id=sale.id,
        )
        session.add(cash_movement)

    session.commit()
    return get_sale_or_404(session, sale.id)  # type: ignore[arg-type]


def list_sales(session: Session, limit: int = 50) -> list[Sale]:
    """Lista las ventas más recientes con su detalle."""
    stmt = (
        select(Sale)
        .options(selectinload(Sale.items))  # type: ignore[arg-type]
        .order_by(Sale.created_at.desc())
        .limit(limit)
    )
    return list(session.exec(stmt).all())


def get_sale_or_404(session: Session, sale_id: int) -> Sale:
    """Obtiene una venta por ID con sus líneas o lanza HTTP 404."""
    stmt = (
        select(Sale)
        .where(Sale.id == sale_id)
        .options(selectinload(Sale.items))  # type: ignore[arg-type]
    )
    sale = session.exec(stmt).first()
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Venta con ID {sale_id} no encontrada.",
        )
    return sale

