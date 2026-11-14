from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import LoginRequest, UserCreate, UserUpdate


def ensure_default_users(session: Session) -> None:
    """Crea los usuarios iniciales Encargado y Cajero si la tabla está vacía."""
    existing = session.exec(select(User.id).limit(1)).first()
    if existing is not None:
        return

    defaults = [
        User(
            name="Encargado",
            password_hash=hash_password("admin123"),
            role=UserRole.ENCARGADO,
            is_active=True,
        ),
        User(
            name="Cajero",
            password_hash=hash_password("cajero123"),
            role=UserRole.CAJERO,
            is_active=True,
        ),
    ]
    session.add_all(defaults)
    session.commit()


def list_users(session: Session, include_inactive: bool = True) -> list[User]:
    stmt = select(User).order_by(User.id.asc())
    if not include_inactive:
        stmt = stmt.where(User.is_active == True)  # noqa: E712
    return list(session.exec(stmt).all())


def list_login_options(session: Session) -> list[User]:
    ensure_default_users(session)
    stmt = (
        select(User)
        .where(User.is_active == True)  # noqa: E712
        .order_by(User.role.desc(), User.name.asc())
    )
    return list(session.exec(stmt).all())


def get_user_or_404(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con id={user_id} no encontrado.",
        )
    return user


def _count_active_managers(session: Session, exclude_user_id: Optional[int] = None) -> int:
    stmt = select(func.count()).select_from(User).where(
        User.is_active == True,  # noqa: E712
        User.role == UserRole.ENCARGADO,
    )
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    return int(session.exec(stmt).one())


def create_user(session: Session, payload: UserCreate) -> User:
    existing = session.exec(
        select(User).where(func.lower(User.name) == payload.name.lower())
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un usuario con el nombre '{payload.name}'.",
        )

    user = User(
        name=payload.name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user(
    session: Session,
    user_id: int,
    payload: UserUpdate,
    current_user_id: Optional[int] = None,
) -> User:
    user = get_user_or_404(session, user_id)
    updates = payload.model_dump(exclude_unset=True)

    if "name" in updates and updates["name"] is not None:
        conflict = session.exec(
            select(User).where(
                func.lower(User.name) == updates["name"].lower(),
                User.id != user_id,
            )
        ).first()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe otro usuario con el nombre '{updates['name']}'.",
            )
        user.name = updates["name"]

    new_role = updates.get("role", user.role)
    new_active = updates.get("is_active", user.is_active)

    if user.id == current_user_id and new_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propio usuario en sesión.",
        )

    if user.role == UserRole.ENCARGADO and (new_role != UserRole.ENCARGADO or not new_active):
        if _count_active_managers(session, exclude_user_id=user_id) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe existir al menos un usuario Encargado activo.",
            )

    if "role" in updates and updates["role"] is not None:
        user.role = updates["role"]
    if "is_active" in updates and updates["is_active"] is not None:
        user.is_active = updates["is_active"]
    if updates.get("password"):
        user.password_hash = hash_password(updates["password"])

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(
    session: Session,
    user_id: int,
    current_user_id: Optional[int] = None,
) -> User:
    user = get_user_or_404(session, user_id)
    if user.id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar o eliminar tu propio usuario en sesión.",
        )
    if user.role == UserRole.ENCARGADO and _count_active_managers(session, exclude_user_id=user_id) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe existir al menos un usuario Encargado activo.",
        )

    user.is_active = False
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, payload: LoginRequest) -> tuple[User, str]:
    ensure_default_users(session)

    user: Optional[User] = None
    if payload.user_id is not None:
        user = session.get(User, payload.user_id)
    elif payload.name and payload.name.strip():
        user = session.exec(
            select(User).where(func.lower(User.name) == payload.name.strip().lower())
        ).first()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes indicar el usuario o ID para iniciar sesión.",
        )

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este usuario se encuentra desactivado. Contacta al Encargado.",
        )

    token = create_access_token(user_id=user.id, name=user.name, role=user.role.value)
    return user, token

