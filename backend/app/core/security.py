"""Utilidades de seguridad: hashing/salting de contraseñas y tokens HMAC-SHA256."""

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session

from app.core.config import get_settings
from app.core.database import get_session
from app.models.enums import UserRole
from app.models.user import User

_PBKDF2_ALGORITHM = "pbkdf2_sha256"
_PBKDF2_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    """Genera un hash PBKDF2-HMAC-SHA256 con sal criptográfica única por usuario."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return f"{_PBKDF2_ALGORITHM}${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Verifica una contraseña contra su hash salteado usando comparación en tiempo constante."""
    try:
        algorithm, iter_str, salt_hex, digest_hex = stored_hash.split("$", 3)
        if algorithm != _PBKDF2_ALGORITHM:
            return False
        iterations = int(iter_str)
        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(digest_hex)
    except (ValueError, TypeError):
        return False

    computed_digest = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(computed_digest, expected_digest)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(user_id: int, name: str, role: str) -> str:
    """Crea un token firmado con HMAC-SHA256 y expiración configurable."""
    settings = get_settings()
    now = int(time.time())
    payload = {
        "sub": user_id,
        "name": name,
        "role": role,
        "iat": now,
        "exp": now + (settings.AUTH_TOKEN_TTL_MINUTES * 60),
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        settings.AUTH_SECRET_KEY.encode("utf-8"),
        payload_b64.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{payload_b64}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    """Valida firma HMAC-SHA256 y expiración de un token de sesión."""
    settings = get_settings()
    try:
        payload_b64, sig_b64 = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sesión inválido.",
        ) from exc

    expected_sig = hmac.new(
        settings.AUTH_SECRET_KEY.encode("utf-8"),
        payload_b64.encode("ascii"),
        hashlib.sha256,
    ).digest()
    try:
        provided_sig = _b64url_decode(sig_b64)
        if not hmac.compare_digest(provided_sig, expected_sig):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Firma de sesión inválida.",
            )
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sesión malformado.",
        ) from exc

    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión ha expirado. Inicia sesión nuevamente.",
        )
    return payload


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Esquema de autorización inválido. Use Bearer <token>.",
        )
    return parts[1].strip()


def get_optional_current_user(
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
) -> Optional[User]:
    """Obtiene el usuario autenticado si se envió Authorization Bearer."""
    token = _extract_bearer_token(authorization)
    if not token:
        return None
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    user = session.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo o no encontrado.",
        )
    return user


def get_current_user(
    user: Optional[User] = Depends(get_optional_current_user),
) -> User:
    """Exige un usuario autenticado válido."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida.",
        )
    return user


def require_manager(
    current_user: User = Depends(get_current_user),
) -> User:
    """Exige que el usuario autenticado tenga rol ENCARGADO."""
    if current_user.role != UserRole.ENCARGADO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido. Solo el Encargado puede realizar esta acción.",
        )
    return current_user


def require_manager_if_authenticated(
    user: Optional[User] = Depends(get_optional_current_user),
) -> Optional[User]:
    """Si la petición viene autenticada, bloquea el acceso a usuarios que no sean ENCARGADO."""
    if user is not None and user.role != UserRole.ENCARGADO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes para el rol Cajero.",
        )
    return user

