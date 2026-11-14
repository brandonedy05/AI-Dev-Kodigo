from collections.abc import Generator
from sqlalchemy import inspect, text
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
    """Crea las tablas declaradas en SQLModel si no existen y sincroniza columnas nuevas."""
    # Importar modelos asegura que SQLModel.metadata conozca todas las tablas.
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    if "products" in tables:
        columns = {col["name"] for col in inspector.get_columns("products")}
        if "image_url" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE products ADD COLUMN image_url VARCHAR(500)"))

    if "customers" in tables:
        existing_cols = {col["name"] for col in inspector.get_columns("customers")}
        customer_migrations = {
            "customer_category": "VARCHAR(20) NOT NULL DEFAULT 'PERSONAL'",
            "country": "VARCHAR(60) NOT NULL DEFAULT 'El Salvador'",
            "nrc": "VARCHAR(30)",
            "business_name": "VARCHAR(150)",
            "economic_activity": "VARCHAR(200)",
            "is_perception_agent": "BOOLEAN NOT NULL DEFAULT FALSE",
            "is_retention_agent": "BOOLEAN NOT NULL DEFAULT FALSE",
            "department": "VARCHAR(60)",
            "municipality": "VARCHAR(80)",
            "district": "VARCHAR(80)",
            "credit_limit": "NUMERIC(12, 2) NOT NULL DEFAULT 0.00",
            "credit_days": "INTEGER NOT NULL DEFAULT 0",
        }
        with engine.begin() as conn:
            for col_name, col_def in customer_migrations.items():
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE customers ADD COLUMN {col_name} {col_def}"))


def get_session() -> Generator[Session, None, None]:
    """Dependencia FastAPI que provee una sesión de base de datos por petición."""
    with Session(engine) as session:
        yield session

