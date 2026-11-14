from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.common import ErrorResponse
from app.schemas.user import LoginRequest, LoginResponse, LoginUserOption, UserRead
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.get(
    "/options",
    response_model=list[LoginUserOption],
    summary="Listar usuarios activos para pantalla de inicio",
)
def get_login_options(session: Session = Depends(get_session)):
    return user_service.list_login_options(session)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Iniciar sesión en el POS",
    responses={
        401: {"model": ErrorResponse, "description": "Credenciales inválidas."},
        403: {"model": ErrorResponse, "description": "Usuario inactivo."},
    },
)
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user, token = user_service.authenticate_user(session, payload)
    return LoginResponse(access_token=token, user=UserRead.model_validate(user))


@router.get(
    "/me",
    response_model=UserRead,
    summary="Obtener usuario conectado en la sesión actual",
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}},
)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

