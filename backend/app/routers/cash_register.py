from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.schemas.cash_register import (
    CashCloseRequest,
    CashMovementCreate,
    CashMovementRead,
    CashOpenRequest,
    CashSessionRead,
    CashSessionSummary,
)
from app.schemas.common import ErrorResponse
from app.services import cash_register_service

router = APIRouter(prefix="/cash-register", tags=["Caja"])


@router.post(
    "/open",
    response_model=CashSessionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir caja",
    description="Inicia un nuevo turno de caja con el fondo inicial de efectivo.",
    responses={409: {"model": ErrorResponse, "description": "Ya existe una sesión de caja abierta."}},
)
def open_cash_register(
    payload: CashOpenRequest,
    session: Session = Depends(get_session),
):
    return cash_register_service.open_cash_register(session, payload)


@router.get(
    "/current",
    response_model=CashSessionSummary,
    summary="Consultar caja actual",
    description="Devuelve la sesión de caja abierta, sus movimientos y el efectivo esperado en gaveta.",
    responses={409: {"model": ErrorResponse, "description": "No hay una sesión de caja abierta."}},
)
def get_current_cash_register(
    session: Session = Depends(get_session),
):
    return cash_register_service.get_current_session_summary(session)


@router.post(
    "/movements",
    response_model=CashMovementRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar movimiento de caja",
    description="Registra un ingreso (INCOME) o retiro (EXPENSE) manual de efectivo en la sesión abierta.",
    responses={
        400: {"model": ErrorResponse, "description": "Tipo de movimiento inválido para registro manual."},
        409: {"model": ErrorResponse, "description": "No hay una sesión de caja abierta."},
    },
)
def create_cash_movement(
    payload: CashMovementCreate,
    session: Session = Depends(get_session),
):
    return cash_register_service.register_cash_movement(session, payload)


@router.post(
    "/close",
    response_model=CashSessionRead,
    summary="Cerrar caja",
    description="Cierra la sesión de caja abierta comparando el efectivo contado contra el esperado.",
    responses={409: {"model": ErrorResponse, "description": "No hay una sesión de caja abierta."}},
)
def close_cash_register(
    payload: CashCloseRequest,
    session: Session = Depends(get_session),
):
    return cash_register_service.close_cash_register(session, payload)


@router.get(
    "/sessions",
    response_model=list[CashSessionRead],
    summary="Historial de sesiones de caja",
    description="Lista los turnos de caja recientes (abiertos y cerrados).",
)
def list_cash_sessions(
    limit: int = Query(default=20, ge=1, le=100, description="Cantidad máxima de sesiones a devolver."),
    session: Session = Depends(get_session),
):
    return cash_register_service.list_cash_sessions(session, limit=limit)

