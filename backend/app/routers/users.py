from fastapi import APIRouter, Depends, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import require_manager
from app.models.user import User
from app.schemas.common import ErrorResponse
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.get(
    "",
    response_model=list[UserRead],
    summary="Listar usuarios del sistema (solo Encargado)",
)
def list_users(
    include_inactive: bool = Query(default=True),
    _: User = Depends(require_manager),
    session: Session = Depends(get_session),
):
    return user_service.list_users(session, include_inactive=include_inactive)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario (solo Encargado)",
    responses={409: {"model": ErrorResponse, "description": "Nombre duplicado."}},
)
def create_user(
    payload: UserCreate,
    _: User = Depends(require_manager),
    session: Session = Depends(get_session),
):
    return user_service.create_user(session, payload)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Obtener detalle de usuario (solo Encargado)",
    responses={404: {"model": ErrorResponse, "description": "Usuario no encontrado."}},
)
def get_user(
    user_id: int,
    _: User = Depends(require_manager),
    session: Session = Depends(get_session),
):
    return user_service.get_user_or_404(session, user_id)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Actualizar usuario o contraseña (solo Encargado)",
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(require_manager),
    session: Session = Depends(get_session),
):
    return user_service.update_user(session, user_id, payload, current_user_id=current_user.id)


@router.delete(
    "/{user_id}",
    response_model=UserRead,
    summary="Desactivar usuario (soft-delete, solo Encargado)",
    responses={404: {"model": ErrorResponse}},
)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_manager),
    session: Session = Depends(get_session),
):
    return user_service.delete_user(session, user_id, current_user_id=current_user.id)

