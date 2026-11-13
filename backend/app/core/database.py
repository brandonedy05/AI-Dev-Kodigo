from collections.abc import Generator
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings

settings = get_settings()

# Configuración del engine adaptada a PostgreSQL (Supabase) y SQLite en pruebas locales.
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
_engine_kwargs: dict = {
    "echo": settings.DB_ECHO,
    "pool_pre_ping": True,
}

if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    _engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)


def init_db() -> None:
    """Crea las tablas declaradas en SQLModel si no existen."""
    # Importar modelos asegura que SQLModel.metadata conozca todas las tablas.
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependencia FastAPI que provee una sesión de base de datos por petición."""
    with Session(engine) as session:
        yield session

