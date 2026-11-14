import base64
from decimal import Decimal
from typing import Any, Optional
from urllib.parse import urlparse

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
        parsed = urlparse(self.base_url)
        self.origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""
        self._client = httpx.Client(base_url=self.base_url, timeout=10.0)

    def resolve_media_url(self, path_or_url: Optional[str]) -> Optional[str]:
        if not path_or_url:
            return None
        if path_or_url.startswith("/"):
            return f"{self.origin}{path_or_url}"
        return path_or_url

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

    def create_category(self, name: str, description: Optional[str] = None) -> dict[str, Any]:
        return self._request("POST", "/categories", json={"name": name, "description": description or None})

    def update_category(self, category_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/categories/{category_id}", json=payload)

    def delete_category(self, category_id: int) -> dict[str, Any]:
        return self._request("DELETE", f"/categories/{category_id}")

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

    def create_product(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/products", json=payload)

    def update_product(self, product_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/products/{product_id}", json=payload)

    def delete_product(self, product_id: int) -> dict[str, Any]:
        return self._request("DELETE", f"/products/{product_id}")

    def upload_product_image(self, filename: str, raw_bytes: bytes) -> str:
        encoded = base64.b64encode(raw_bytes).decode("ascii")
        res = self._request(
            "POST",
            "/products/upload-image",
            json={"filename": filename, "content_base64": encoded},
        )
        return str(res["image_url"])

    # --- Clientes ---
    def get_customers(self, search: Optional[str] = None) -> list[dict[str, Any]]:
        params = {"search": search} if search else {}
        return self._request("GET", "/customers", params=params)

    def create_customer(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/customers", json=payload)

    def update_customer(self, customer_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/customers/{customer_id}", json=payload)

    def delete_customer(self, customer_id: int) -> dict[str, Any]:
        return self._request("DELETE", f"/customers/{customer_id}")

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
        card_bank: Optional[str] = None,
        card_type: Optional[str] = None,
        card_auth_number: Optional[str] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "items": items,
            "payment_method": payment_method,
            "amount_paid": str(amount_paid),
            "discount": str(discount),
            "customer_id": customer_id,
            "card_bank": card_bank,
            "card_type": card_type,
            "card_auth_number": card_auth_number,
        }
        return self._request("POST", "/sales", json=payload)

    # --- Reportes ---
    def get_sales(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._request("GET", "/sales", params={"limit": limit})

    def get_sales_summary(self) -> dict[str, Any]:
        return self._request("GET", "/reports/sales-summary")

    def get_top_products(self) -> list[dict[str, Any]]:
        return self._request("GET", "/reports/top-products")

    def get_low_stock(self) -> list[dict[str, Any]]:
        return self._request("GET", "/reports/low-stock")

