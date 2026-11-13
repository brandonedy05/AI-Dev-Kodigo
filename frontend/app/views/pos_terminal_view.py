from decimal import Decimal
from typing import Any, Callable, Optional

import flet as ft

from app.services.api_client import POSApiClient, POSApiError
from app.theme import Colors


class POSTerminalView(ft.Row):
    """Terminal de ventas (65% catálogo / 35% dock de ticket activo) conectada a la API."""

    def __init__(
        self,
        api: POSApiClient,
        on_notify: Callable[[str, str], None],
    ):
        super().__init__(expand=True, spacing=16)
        self.api = api
        self.on_notify = on_notify

        self.selected_category_id: Optional[int] = None
        self.cart: dict[int, dict[str, Any]] = {}

        self.search_field = ft.TextField(
            hint_text="Buscar producto por nombre, SKU o código de barras...",
            prefix_icon=ft.Icons.SEARCH,
            bgcolor=Colors.SURFACE_CONTAINER_LOWEST,
            border_color=Colors.OUTLINE_VARIANT,
            border_radius=12,
            on_submit=lambda _: self.load_products(),
            expand=True,
        )
        self.category_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=8)
        self.catalog_grid = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=230,
            child_aspect_ratio=1.1,
            spacing=12,
            run_spacing=12,
        )

        self.cart_list = ft.ListView(expand=True, spacing=8)
        self.payment_selector = ft.SegmentedButton(
            selected=["CASH"],
            segments=[
                ft.Segment(value="CASH", label=ft.Text("Efectivo"), icon=ft.Icon(ft.Icons.PAYMENTS)),
                ft.Segment(value="CARD", label=ft.Text("Tarjeta"), icon=ft.Icon(ft.Icons.CREDIT_CARD)),
            ],
            on_change=lambda _: self._recalculate_totals(),
        )
        self.amount_paid_field = ft.TextField(
            label="Efectivo / Monto recibido ($)",
            value="0.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor=Colors.SURFACE_CONTAINER_LOWEST,
            on_change=lambda _: self._recalculate_totals(),
        )
        self.subtotal_text = ft.Text("$0.00", size=14, color=Colors.ON_SURFACE_VARIANT)
        self.total_text = ft.Text("$0.00", size=28, weight=ft.FontWeight.BOLD, color=Colors.ON_SURFACE)
        self.change_text = ft.Text("Vuelto: $0.00", size=15, weight=ft.FontWeight.W_600, color=Colors.PRIMARY)
        self.checkout_btn = ft.Button(
            content="COBRAR",
            icon=ft.Icons.CHECK_CIRCLE,
            bgcolor=Colors.PRIMARY_CONTAINER,
            color=Colors.ON_PRIMARY,
            height=52,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            on_click=lambda _: self._submit_sale(),
        )

        catalog_panel = ft.Container(
            expand=65,
            padding=16,
            bgcolor=Colors.SURFACE_CONTAINER_LOW,
            border_radius=16,
            content=ft.Column(
                expand=True,
                spacing=12,
                controls=[
                    ft.Row(
                        controls=[
                            self.search_field,
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                tooltip="Recargar catálogo",
                                on_click=lambda _: self.refresh(),
                            ),
                        ]
                    ),
                    self.category_row,
                    self.catalog_grid,
                ],
            ),
        )

        ticket_panel = ft.Container(
            expand=35,
            padding=16,
            bgcolor=Colors.SURFACE_CONTAINER_LOWEST,
            border=ft.Border.all(1, Colors.OUTLINE_VARIANT),
            border_radius=16,
            content=ft.Column(
                expand=True,
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Ticket Activo", size=20, weight=ft.FontWeight.BOLD, color=Colors.ON_SURFACE),
                            ft.TextButton(content="Limpiar", on_click=lambda _: self._clear_cart()),
                        ],
                    ),
                    ft.Divider(height=1, color=Colors.OUTLINE_VARIANT),
                    self.cart_list,
                    ft.Divider(height=1, color=Colors.OUTLINE_VARIANT),
                    self.payment_selector,
                    self.amount_paid_field,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[ft.Text("Subtotal", color=Colors.ON_SURFACE_VARIANT), self.subtotal_text],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[ft.Text("Total", size=18, weight=ft.FontWeight.BOLD), self.total_text],
                    ),
                    self.change_text,
                    ft.Row(controls=[ft.Container(expand=True, content=self.checkout_btn)]),
                ],
            ),
        )

        self.controls = [catalog_panel, ticket_panel]

    def refresh(self) -> None:
        self.load_categories()
        self.load_products()

    def load_categories(self) -> None:
        self.category_row.controls.clear()
        self.category_row.controls.append(
            ft.Chip(
                label=ft.Text("Todas"),
                selected=self.selected_category_id is None,
                on_select=lambda _: self._select_category(None),
            )
        )
        try:
            for cat in self.api.get_categories():
                cat_id = cat["id"]
                self.category_row.controls.append(
                    ft.Chip(
                        label=ft.Text(cat["name"]),
                        selected=self.selected_category_id == cat_id,
                        on_select=lambda _, cid=cat_id: self._select_category(cid),
                    )
                )
        except POSApiError as exc:
            self.on_notify(exc.detail, Colors.ERROR)
        self.update()

    def _select_category(self, category_id: Optional[int]) -> None:
        self.selected_category_id = category_id
        self.load_categories()
        self.load_products()

    def load_products(self) -> None:
        self.catalog_grid.controls.clear()
        try:
            products = self.api.get_products(
                search=self.search_field.value or None,
                category_id=self.selected_category_id,
            )
            for prod in products:
                stock = int(prod["stock"])
                low_stock = stock <= int(prod["min_stock"])
                badge_color = Colors.ERROR if stock == 0 else (Colors.TERTIARY if low_stock else Colors.PRIMARY)

                card = ft.Container(
                    padding=12,
                    bgcolor=Colors.SURFACE_CONTAINER_LOWEST,
                    border=ft.Border.all(1, Colors.OUTLINE_VARIANT),
                    border_radius=12,
                    on_click=lambda _, p=prod: self._add_to_cart(p),
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(prod["sku"], size=11, color=Colors.ON_SURFACE_VARIANT),
                                    ft.Text(
                                        prod["name"],
                                        size=15,
                                        weight=ft.FontWeight.W_600,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(
                                        f"${Decimal(str(prod['price'])):.2f}",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=Colors.PRIMARY,
                                    ),
                                    ft.Container(
                                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                                        bgcolor=Colors.SURFACE_CONTAINER,
                                        border_radius=99,
                                        content=ft.Text(f"Stock: {stock}", size=11, color=badge_color),
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
                self.catalog_grid.controls.append(card)
        except POSApiError as exc:
            self.on_notify(exc.detail, Colors.ERROR)
        self.update()

    def _add_to_cart(self, product: dict[str, Any]) -> None:
        pid = product["id"]
        stock = int(product["stock"])
        current_qty = self.cart.get(pid, {}).get("quantity", 0)
        if current_qty + 1 > stock:
            self.on_notify(f"Stock insuficiente para {product['name']} (disponible: {stock}).", Colors.TERTIARY)
            return

        if pid in self.cart:
            self.cart[pid]["quantity"] += 1
        else:
            self.cart[pid] = {
                "product_id": pid,
                "name": product["name"],
                "price": Decimal(str(product["price"])),
                "stock": stock,
                "quantity": 1,
            }
        self._render_cart()

    def _update_qty(self, product_id: int, delta: int) -> None:
        item = self.cart.get(product_id)
        if not item:
            return
        new_qty = item["quantity"] + delta
        if new_qty <= 0:
            del self.cart[product_id]
        elif new_qty > item["stock"]:
            self.on_notify(f"Stock máximo alcanzado ({item['stock']}).", Colors.TERTIARY)
            return
        else:
            item["quantity"] = new_qty
        self._render_cart()

    def _clear_cart(self) -> None:
        self.cart.clear()
        self.amount_paid_field.value = "0.00"
        self._render_cart()

    def _render_cart(self) -> None:
        self.cart_list.controls.clear()
        for pid, item in self.cart.items():
            line_total = item["price"] * item["quantity"]
            self.cart_list.controls.append(
                ft.Container(
                    padding=8,
                    bgcolor=Colors.SURFACE_CONTAINER_LOW,
                    border_radius=8,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                expand=True,
                                spacing=2,
                                controls=[
                                    ft.Text(item["name"], weight=ft.FontWeight.W_600, size=13),
                                    ft.Text(f"${item['price']:.2f} c/u", size=11, color=Colors.ON_SURFACE_VARIANT),
                                ],
                            ),
                            ft.Row(
                                spacing=2,
                                controls=[
                                    ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_size=18, on_click=lambda _, i=pid: self._update_qty(i, -1)),
                                    ft.Text(str(item["quantity"]), weight=ft.FontWeight.BOLD),
                                    ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_size=18, on_click=lambda _, i=pid: self._update_qty(i, 1)),
                                ],
                            ),
                            ft.Text(f"${line_total:.2f}", weight=ft.FontWeight.BOLD, width=65, text_align=ft.TextAlign.RIGHT),
                        ],
                    ),
                )
            )
        self._recalculate_totals()

    def _recalculate_totals(self) -> None:
        subtotal = sum((i["price"] * i["quantity"] for i in self.cart.values()), Decimal("0.00"))
        self.subtotal_text.value = f"${subtotal:.2f}"
        self.total_text.value = f"${subtotal:.2f}"

        method = next(iter(self.payment_selector.selected), "CASH")
        try:
            paid = Decimal(self.amount_paid_field.value or "0.00")
        except Exception:
            paid = Decimal("0.00")

        if method == "CARD":
            paid = subtotal
            self.amount_paid_field.value = f"{subtotal:.2f}"

        change = max(Decimal("0.00"), paid - subtotal)
        self.change_text.value = f"Vuelto: ${change:.2f}"
        self.update()

    def _submit_sale(self) -> None:
        if not self.cart:
            self.on_notify("Agrega al menos un producto al ticket.", Colors.TERTIARY)
            return

        method = next(iter(self.payment_selector.selected), "CASH")
        try:
            amount_paid = Decimal(self.amount_paid_field.value or "0.00")
        except Exception:
            self.on_notify("Ingresa un monto recibido válido.", Colors.ERROR)
            return

        items = [{"product_id": pid, "quantity": item["quantity"]} for pid, item in self.cart.items()]
        try:
            sale = self.api.create_sale(items=items, payment_method=method, amount_paid=amount_paid)
            self.on_notify(
                f"Venta {sale['ticket_number']} completada. Total: ${sale['total']} | Vuelto: ${sale['change_amount']}",
                Colors.PRIMARY,
            )
            self._clear_cart()
            self.load_products()
        except POSApiError as exc:
            self.on_notify(exc.detail, Colors.ERROR)

