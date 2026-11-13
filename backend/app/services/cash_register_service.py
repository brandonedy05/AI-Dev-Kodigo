from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.cash_register import CashMovement, CashRegisterSession
from app.models.enums import CashMovementType, CashSessionStatus
from app.schemas.cash_register import (
    CashCloseRequest,
    CashMovementCreate,
    CashMovementRead,
    CashOpenRequest,
    CashSessionRead,
    CashSessionSummary,
)


def get_open_session(session: Session) -> CashRegisterSession | None:
    """Devuelve la sesión de caja actualmente abierta, si existe."""
    stmt = (
        select(CashRegisterSession)
        .where(CashRegisterSession.status == CashSessionStatus.OPEN)
        .order_by(CashRegisterSession.opened_at.desc())
    )
    return session.exec(stmt).first()


def require_open_session(session: Session) -> CashRegisterSession:
    """Devuelve la sesión de caja abierta o lanza HTTP 409."""
    current = get_open_session(session)
    if not current:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No hay una sesión de caja abierta. Abre caja antes de operar.",
        )
    return current


def open_cash_register(session: Session, payload: CashOpenRequest) -> CashRegisterSession:
    """Abre un nuevo turno de caja si no existe otro abierto."""
    if get_open_session(session):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una sesión de caja abierta. Ciérrala antes de abrir una nueva.",
        )

    cash_session = CashRegisterSession(
        cashier_name=payload.cashier_name,
        opening_amount=payload.opening_amount,
        notes=payload.notes,
        status=CashSessionStatus.OPEN,
    )
    session.add(cash_session)
    session.commit()
    session.refresh(cash_session)
    return cash_session


def register_cash_movement(
    session: Session,
    payload: CashMovementCreate,
) -> CashMovement:
    """Registra un ingreso o retiro manual de efectivo en la sesión activa."""
    if payload.movement_type == CashMovementType.SALE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los movimientos de tipo SALE se registran automáticamente al completar una venta.",
        )

    current = require_open_session(session)
    movement = CashMovement(
        session_id=current.id,  # type: ignore[arg-type]
        movement_type=payload.movement_type,
        amount=payload.amount,
        reason=payload.reason,
    )
    session.add(movement)
    session.commit()
    session.refresh(movement)
    return movement


def _compute_session_totals(
    session: Session, cash_session: CashRegisterSession
) -> tuple[Decimal, Decimal, Decimal, Decimal, list[CashMovement]]:
    """Calcula totales de ventas en efectivo, ingresos, egresos y efectivo esperado."""
    movements = list(
        session.exec(
            select(CashMovement)
            .where(CashMovement.session_id == cash_session.id)
            .order_by(CashMovement.created_at.desc())
        ).all()
    )

    cash_sales_total = sum(
        (m.amount for m in movements if m.movement_type == CashMovementType.SALE),
        Decimal("0.00"),
    )
    income_total = sum(
        (m.amount for m in movements if m.movement_type == CashMovementType.INCOME),
        Decimal("0.00"),
    )
    expense_total = sum(
        (m.amount for m in movements if m.movement_type == CashMovementType.EXPENSE),
        Decimal("0.00"),
    )
    expected = cash_session.opening_amount + cash_sales_total + income_total - expense_total
    return cash_sales_total, income_total, expense_total, expected, movements


def get_current_session_summary(session: Session) -> CashSessionSummary:
    """Obtiene el resumen completo de la sesión de caja abierta."""
    current = require_open_session(session)
    cash_sales, incomes, expenses, expected, movements = _compute_session_totals(session, current)
    return CashSessionSummary(
        session=CashSessionRead.model_validate(current),
        cash_sales_total=cash_sales,
        income_total=incomes,
        expense_total=expenses,
        expected_cash_in_drawer=expected,
        movements=[CashMovementRead.model_validate(m) for m in movements],
    )


def close_cash_register(session: Session, payload: CashCloseRequest) -> CashRegisterSession:
    """Cierra la sesión de caja activa calculando el efectivo esperado y la diferencia."""
    current = require_open_session(session)
    _, _, _, expected, _ = _compute_session_totals(session, current)

    current.closing_amount = payload.closing_amount
    current.expected_amount = expected
    current.difference = payload.closing_amount - expected
    current.status = CashSessionStatus.CLOSED
    current.closed_at = datetime.now(timezone.utc)
    if payload.notes:
        current.notes = payload.notes

    session.add(current)
    session.commit()
    session.refresh(current)
    return current


def list_cash_sessions(session: Session, limit: int = 20) -> list[CashRegisterSession]:
    """Lista el historial reciente de sesiones de caja."""
    stmt = (
        select(CashRegisterSession)
        .order_by(CashRegisterSession.opened_at.desc())
        .limit(limit)
    )
    return list(session.exec(stmt).all())

