from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import Session, col, or_, select

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


def list_customers(
    session: Session,
    *,
    search: Optional[str] = None,
    active_only: bool = True,
) -> list[Customer]:
    """Lista clientes con búsqueda por nombre, documento o teléfono."""
    stmt = select(Customer).order_by(Customer.full_name)
    if active_only:
        stmt = stmt.where(Customer.is_active.is_(True))
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                col(Customer.full_name).ilike(pattern),
                col(Customer.document_number).ilike(pattern),
                col(Customer.nrc).ilike(pattern),
                col(Customer.business_name).ilike(pattern),
                col(Customer.phone).ilike(pattern),
            )
        )
    return list(session.exec(stmt).all())


def get_customer_or_404(session: Session, customer_id: int) -> Customer:
    """Obtiene un cliente por ID o lanza HTTP 404."""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {customer_id} no encontrado.",
        )
    return customer


def create_customer(session: Session, payload: CustomerCreate) -> Customer:
    """Registra un nuevo cliente validando que el número de documento no esté duplicado."""
    if payload.document_number:
        existing = session.exec(
            select(Customer).where(Customer.document_number == payload.document_number)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un cliente con el documento '{payload.document_number}'.",
            )

    customer = Customer.model_validate(payload)
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


def update_customer(session: Session, customer_id: int, payload: CustomerUpdate) -> Customer:
    """Actualiza los datos de un cliente."""
    customer = get_customer_or_404(session, customer_id)
    update_data = payload.model_dump(exclude_unset=True)

    new_doc = update_data.get("document_number")
    if new_doc and new_doc != customer.document_number:
        dup = session.exec(select(Customer).where(Customer.document_number == new_doc)).first()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe otro cliente con el documento '{new_doc}'.",
            )

    for key, value in update_data.items():
        setattr(customer, key, value)

    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


def deactivate_customer(session: Session, customer_id: int) -> Customer:
    """Desactiva un cliente sin eliminar su historial."""
    customer = get_customer_or_404(session, customer_id)
    customer.is_active = False
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer

