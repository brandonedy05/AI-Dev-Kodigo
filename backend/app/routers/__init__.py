from app.routers.cash_register import router as cash_register_router
from app.routers.customers import router as customers_router
from app.routers.products import router as products_router
from app.routers.reports import router as reports_router
from app.routers.sales import router as sales_router

__all__ = [
    "products_router",
    "customers_router",
    "cash_register_router",
    "sales_router",
    "reports_router",
]

