from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core import database as db_module
from app.core.database import get_session
from app.main import app


@pytest.fixture(name="client")
def client_fixture(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr(db_module, "engine", engine)
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_full_pos_flow(client: TestClient):
    # 1. Subir imagen de producto, crear categoría y producto
    import base64

    tiny_png = base64.b64encode(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    ).decode("ascii")
    up_res = client.post(
        "/api/v1/products/upload-image",
        json={"filename": "coca.png", "content_base64": tiny_png},
    )
    assert up_res.status_code == 201
    uploaded_url = up_res.json()["image_url"]
    assert uploaded_url.startswith("/uploads/products/")
    assert client.get(uploaded_url).status_code == 200

    cat_res = client.post("/api/v1/categories", json={"name": "Bebidas"})
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["id"]

    prod_res = client.post(
        "/api/v1/products",
        json={
            "sku": "BEB-001",
            "name": "Coca-Cola 600ml",
            "image_url": uploaded_url,
            "price": "1.25",
            "stock": 10,
            "min_stock": 3,
            "category_id": cat_id,
        },
    )
    assert prod_res.status_code == 201
    assert prod_res.json()["image_url"] == uploaded_url
    prod_id = prod_res.json()["id"]

    # 2. Registrar cliente (con campos de El Salvador)
    cust_res = client.post(
        "/api/v1/customers",
        json={
            "full_name": "María Hernández",
            "customer_category": "TAXPAYER",
            "document_type": "DUI",
            "document_number": "04512984-1",
            "nrc": "284910-3",
            "business_name": "Comercial Hernández S.A. de C.V.",
            "department": "San Salvador",
            "municipality": "San Salvador Centro",
            "district": "San Salvador",
            "address": "Col. Escalón, Calle El Mirador #14",
            "phone": "+503 7890-1234",
            "credit_limit": "500.00",
            "credit_days": 30,
        },
    )
    assert cust_res.status_code == 201
    assert cust_res.json()["nrc"] == "284910-3"
    cust_id = cust_res.json()["id"]

    # 3. Intentar vender con caja cerrada debe fallar con 409
    closed_sale = client.post(
        "/api/v1/sales",
        json={
            "customer_id": cust_id,
            "payment_method": "CASH",
            "amount_paid": "5.00",
            "items": [{"product_id": prod_id, "quantity": 2}],
        },
    )
    assert closed_sale.status_code == 409

    # 4. Abrir caja
    open_res = client.post(
        "/api/v1/cash-register/open",
        json={"cashier_name": "Carlos", "opening_amount": "50.00"},
    )
    assert open_res.status_code == 201

    # 5. Intentar vender más del stock disponible debe fallar con 409
    over_stock = client.post(
        "/api/v1/sales",
        json={
            "payment_method": "CASH",
            "amount_paid": "50.00",
            "items": [{"product_id": prod_id, "quantity": 20}],
        },
    )
    assert over_stock.status_code == 409

    # 6. Registrar venta válida (2 unidades * 1.25 = 2.50, paga con 5.00 -> vuelto 2.50)
    sale_res = client.post(
        "/api/v1/sales",
        json={
            "customer_id": cust_id,
            "payment_method": "CASH",
            "amount_paid": "5.00",
            "items": [{"product_id": prod_id, "quantity": 2}],
        },
    )
    assert sale_res.status_code == 201
    sale_data = sale_res.json()
    assert Decimal(sale_data["total"]) == Decimal("2.50")
    assert Decimal(sale_data["change_amount"]) == Decimal("2.50")

    # Verificar descuento de stock (10 - 2 = 8)
    prod_after = client.get(f"/api/v1/products/{prod_id}").json()
    assert prod_after["stock"] == 8

    # 7. Movimiento manual y cierre de caja
    mov_res = client.post(
        "/api/v1/cash-register/movements",
        json={"movement_type": "EXPENSE", "amount": "10.00", "reason": "Compra de bolsas"},
    )
    assert mov_res.status_code == 201

    # Efectivo esperado: 50.00 + 2.50 - 10.00 = 42.50
    summary = client.get("/api/v1/cash-register/current").json()
    assert Decimal(summary["expected_cash_in_drawer"]) == Decimal("42.50")

    close_res = client.post(
        "/api/v1/cash-register/close",
        json={"closing_amount": "42.50"},
    )
    assert close_res.status_code == 200
    assert Decimal(close_res.json()["difference"]) == Decimal("0.00")

    # 8. Reportes
    rep_summary = client.get("/api/v1/reports/sales-summary").json()
    assert rep_summary["total_transactions"] == 1
    assert Decimal(rep_summary["total_revenue"]) == Decimal("2.50")

    top_prods = client.get("/api/v1/reports/top-products").json()
    assert len(top_prods) == 1
    assert top_prods[0]["units_sold"] == 2

