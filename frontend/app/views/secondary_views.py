import flet as ft

from app.services.api_client import POSApiClient, POSApiError
from app.theme import Colors


class ProductsView(ft.Container):
    """Planteamiento de vista de gestión de catálogo y productos (/api/v1/products)."""

    def __init__(self, api: POSApiClient):
        super().__init__(expand=True, padding=24)
        self.api = api
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("SKU")),
                ft.DataColumn(ft.Text("Producto")),
                ft.DataColumn(ft.Text("Precio")),
                ft.DataColumn(ft.Text("Stock")),
            ],
            rows=[],
        )
        self.content = ft.Column(
            spacing=12,
            controls=[
                ft.Text("Gestión de Productos", size=24, weight=ft.FontWeight.BOLD, color=Colors.ON_SURFACE),
                ft.Text("Conectado a GET /api/v1/products (CRUD extensible según diseño 02 y 03)."),
                ft.Column([self.table], scroll=ft.ScrollMode.AUTO, expand=True),
            ],
        )

    def refresh(self) -> None:
        self.table.rows.clear()
        try:
            for p in self.api.get_products():
                self.table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(p["sku"])),
                            ft.DataCell(ft.Text(p["name"])),
                            ft.DataCell(ft.Text(f"${p['price']}")),
                            ft.DataCell(ft.Text(str(p["stock"]))),
                        ]
                    )
                )
        except POSApiError:
            pass
        self.update()


class CustomersView(ft.Container):
    """Planteamiento de directorio de clientes (/api/v1/customers)."""

    def __init__(self, api: POSApiClient):
        super().__init__(expand=True, padding=24)
        self.api = api
        self.list_view = ft.ListView(expand=True, spacing=8)
        self.content = ft.Column(
            spacing=12,
            controls=[
                ft.Text("Directorio de Clientes", size=24, weight=ft.FontWeight.BOLD, color=Colors.ON_SURFACE),
                ft.Text("Conectado a GET /api/v1/customers (DUI/NIT según diseño 04)."),
                self.list_view,
            ],
        )

    def refresh(self) -> None:
        self.list_view.controls.clear()
        try:
            for c in self.api.get_customers():
                self.list_view.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.PERSON),
                        title=ft.Text(c["full_name"]),
                        subtitle=ft.Text(f"{c['document_type']}: {c.get('document_number') or 'N/A'}"),
                    )
                )
        except POSApiError:
            pass
        self.update()


class ReportsView(ft.Container):
    """Vista de reportes de ventas del día y alertas de stock bajo."""

    def __init__(self, api: POSApiClient):
        super().__init__(expand=True, padding=24)
        self.api = api
        self.summary_text = ft.Text("", size=16)
        self.low_stock_list = ft.ListView(expand=True, spacing=6)
        self.content = ft.Column(
            spacing=12,
            controls=[
                ft.Text("Reportes del Día", size=24, weight=ft.FontWeight.BOLD, color=Colors.ON_SURFACE),
                self.summary_text,
                ft.Text("Alertas de Stock Bajo", size=18, weight=ft.FontWeight.W_600, color=Colors.TERTIARY),
                self.low_stock_list,
            ],
        )

    def refresh(self) -> None:
        self.low_stock_list.controls.clear()
        try:
            summary = self.api.get_sales_summary()
            self.summary_text.value = (
                f"Ventas hoy: {summary['total_transactions']} | "
                f"Ingresos: ${summary['total_revenue']} | "
                f"Ticket promedio: ${summary['average_ticket']}"
            )
            for item in self.api.get_low_stock():
                self.low_stock_list.controls.append(
                    ft.Text(f"• {item['name']} ({item['sku']}): {item['stock']} uds (mín: {item['min_stock']})")
                )
        except POSApiError:
            self.summary_text.value = "No se pudo conectar con el servidor de reportes."
        self.update()

