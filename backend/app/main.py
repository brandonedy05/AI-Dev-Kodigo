from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import init_db
from app.routers import (
    cash_register_router,
    customers_router,
    products_router,
    reports_router,
    sales_router,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Inicializa las tablas en la base de datos al arrancar la API."""
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API REST para el Sistema de Punto de Venta (POS) **Mi Tiendita Fácil**, "
        "construida con FastAPI + SQLModel sobre PostgreSQL (Supabase)."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Sistema"], summary="Raíz de la API")
def root():
    """Punto de entrada con enlaces a documentación y prefijo de la API."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "api_prefix": settings.API_V1_PREFIX,
    }


@app.get("/health", tags=["Sistema"], summary="Estado de la API")
def health_check():
    """Endpoint ligero de verificación de salud del servicio."""
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


app.include_router(products_router, prefix=settings.API_V1_PREFIX)
app.include_router(customers_router, prefix=settings.API_V1_PREFIX)
app.include_router(cash_register_router, prefix=settings.API_V1_PREFIX)
app.include_router(sales_router, prefix=settings.API_V1_PREFIX)
app.include_router(reports_router, prefix=settings.API_V1_PREFIX)

