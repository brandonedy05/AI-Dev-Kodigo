from decimal import Decimal
from typing import Any, Optional

import httpx


class POSApiError(Exception):
    """Error devuelto por la API REST del POS."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{status_code}] {detail}")


class POSApiClient:
    """Cliente HTTP síncrono para consumir la API FastAPI de Mi Tiendita Fácil."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000/api/v1"):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=10.0)

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._client.request(method, path, **kwargs)
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise POSApiError(response.status_code, str(detail))
        return response.json()

    # --- Catálogo y Productos ---
    def get_categories(self) -> list[dict[str, Any]]:
        return self._request("GET", "/categories")

    def get_products(
        self,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if search:
            params["search"] = search
        if category_id is not None:
            params["category_id"] = category_id
        return self._request("GET", "/products", params=params)

    # --- Clientes ---
    def get_customers(self, search: Optional[str] = None) -> list[dict[str, Any]]:
        params = {"search": search} if search else {}
        return self._request("GET", "/customers", params=params)

    # --- Caja ---
    def get_current_cash_session(self) -> dict[str, Any]:
        return self._request("GET", "/cash-register/current")

    def open_cash_session(self, cashier_name: str, opening_amount: Decimal) -> dict[str, Any]:
        return self._request(
            "POST",
            "/cash-register/open",
            json={"cashier_name": cashier_name, "opening_amount": str(opening_amount)},
        )

    def close_cash_session(self, closing_amount: Decimal) -> dict[str, Any]:
        return self._request(
            "POST",
            "/cash-register/close",
            json={"closing_amount": str(closing_amount)},
        )

    # --- Ventas ---
    def create_sale(
        self,
        items: list[dict[str, Any]],
        payment_method: str,
        amount_paid: Decimal,
        customer_id: Optional[int] = None,
        discount: Decimal = Decimal("0.00"),
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "items": items,
            "payment_method": payment_method,
            "amount_paid": str(amount_paid),
            "discount": str(discount),
            "customer_id": customer_id,
        }
        return self._request("POST", "/sales", json=payload)

    # --- Reportes ---
    def get_sales_summary(self) -> dict[str, Any]:
        return self._request("GET", "/reports/sales-summary")

    def get_top_products(self) -> list[dict[str, Any]]:
        return self._request("GET", "/reports/top-products")

    def get_low_stock(self) -> list[dict[str, Any]]:
        return self._request("GET", "/reports/low-stock")

