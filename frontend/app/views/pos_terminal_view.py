from decimal import Decimal
from typing import Any, Callable, Optional

import flet as ft

from app.services.api_client import POSApiClient, POSApiError
from app.theme import CARD_SHADOW, Colors
from app.views import safe_update


class POSTerminalView(ft.Row):
    """Terminal POS (65% catálogo / 35% dock de ticket) basada en diseños 05 y 06."""

    def __init__(
        self,
        api: POSApiClient,
        on_notify: Callable[[str, str], None],
    ):
        super().__init__(expand=True, spacing=16)
        self.api = api
        self.on_notify = on_notify

        self.selected_category_id: Optional[int] = None
        self.categories_map: dict[int, str] = {}
        self.cart: dict[int, dict[str, Any]] = {}

        self.search_field = ft.TextField(
            hint_text="Buscar producto por nombre, SKU o código de barras...",
            prefix_icon=ft.Icons.QR_CODE_SCANNER,
            suffix=ft.Container(
                padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                bgcolor=Colors.SURFACE_ALT,
                border_radius=6,
                content=ft.Text("F2", size=11, weight=ft.FontWeight.BOLD, color=Colors.TEXT_MUTED),
            ),
            bgcolor=Colors.SURFACE,
            border_color=Colors.BORDER,
            focused_border_color=Colors.EMERALD,
            border_radius=12,
            height=50,
            on_submit=lambda _: self.load_products(),
            expand=True,
        )
        self.category_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=8)
        self.catalog_grid = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=220,
            child_aspect_ratio=0.78,
            spacing=12,
            run_spacing=12,
        )

        self.cart_list = ft.ListView(expand=True, spacing=6)
        self.items_count_text = ft.Text("0 artículos", size=12, color=Colors.TEXT_MUTED)
        self.customer_dropdown = ft.Dropdown(
            label="Cliente",
            value="0",
            options=[ft.dropdown.Option(key="0", text="Consumidor Final")],
            border_color=Colors.BORDER,
            border_radius=10,
            text_size=13,
        )
        self.customers_map: dict[str, str] = {"0": "Consumidor Final"}
        self.price_mode_selector = ft.SegmentedButton(
            selected=["RETAIL"],
            segments=[
                ft.Segment(value="RETAIL", label=ft.Text("Detalle"), icon=ft.Icon(ft.Icons.SELL_OUTLINED)),
                ft.Segment(value="WHOLESALE", label=ft.Text("Mayoreo"), icon=ft.Icon(ft.Icons.INVENTORY_OUTLINED)),
            ],
            on_change=lambda _: self._render_cart(),
        )
        self.payment_selector = ft.SegmentedButton(
            selected=["CASH"],
            segments=[
                ft.Segment(value="CASH", label=ft.Text("Efectivo"), icon=ft.Icon(ft.Icons.PAYMENTS)),
                ft.Segment(value="CARD", label=ft.Text("Tarjeta"), icon=ft.Icon(ft.Icons.CREDIT_CARD)),
            ],
            on_change=lambda _: self._recalculate_totals(),
        )
        self.amount_paid_field = ft.TextField(
            label="Efectivo recibido ($)",
            value="0.00",
            keyboard_type=ft.KeyboardType.NUMBER,
            bgcolor=Colors.SURFACE,
            border_color=Colors.BORDER,
            focused_border_color=Colors.EMERALD,
            border_radius=10,
            on_change=lambda _: self._recalculate_totals(),
        )
        self.quick_cash_row = ft.Row(
            spacing=6,
            controls=[
                self._quick_cash_pill("$5", Decimal("5.00")),
                self._quick_cash_pill("$10", Decimal("10.00")),
                self._quick_cash_pill("$20", Decimal("20.00")),
                self._quick_cash_pill("$50", Decimal("50.00")),
                self._quick_cash_pill("Exacto", None),
            ],
        )
        self.card_bank_field = ft.TextField(
            label="Banco emisor *",
            hint_text="Ej: Banco Agrícola, BAC, Davivienda",
            bgcolor=Colors.SURFACE,
            border_color=Colors.BORDER,
            border_radius=10,
            text_size=13,
        )
        self.card_type_dropdown = ft.Dropdown(
            label="Tipo de tarjeta *",
            value="CREDITO",
            options=[
                ft.dropdown.Option("CREDITO", "Crédito"),
                ft.dropdown.Option("DEBITO", "Débito"),
            ],
            border_color=Colors.BORDER,
            border_radius=10,
            text_size=13,
        )
        self.card_auth_field = ft.TextField(
            label="N° de autorización (Voucher) *",
            hint_text="Ej: 482910",
            bgcolor=Colors.SURFACE,
            border_color=Colors.BORDER,
            border_radius=10,
            text_size=13,
        )
        self.card_details_container = ft.Container(
            visible=False,
            padding=10,
            bgcolor=Colors.CANVAS,
            border=ft.Border.all(1, Colors.BORDER),
            border_radius=10,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text("Datos del Voucher de Tarjeta", size=12, weight=ft.FontWeight.BOLD, color=Colors.NAVY),
                    self.card_bank_field,
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Container(expand=True, content=self.card_type_dropdown),
                            ft.Container(expand=True, content=self.card_auth_field),
                        ],
                    ),
                ],
            ),
        )
        self.subtotal_text = ft.Text("$0.00", size=14, color=Colors.TEXT_SECONDARY)
        self.total_text = ft.Text("$0.00", size=30, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)
        self.change_text = ft.Text("Vuelto: $0.00", size=15, weight=ft.FontWeight.BOLD, color=Colors.EMERALD_DARK)
        self.checkout_btn = ft.Button(
            content="COBRAR  $0.00",
            icon=ft.Icons.CHECK_CIRCLE,
            bgcolor=Colors.EMERALD,
            color=Colors.ON_PRIMARY,
            height=58,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16)),
            on_click=lambda _: self._submit_sale(),
        )

        catalog_panel = ft.Container(
            expand=65,
            padding=16,
            bgcolor=Colors.CANVAS,
            content=ft.Column(
                expand=True,
                spacing=14,
                controls=[
                    ft.Row(
                        spacing=10,
                        controls=[
                            self.search_field,
                            ft.Container(
                                height=50,
                                width=50,
                                bgcolor=Colors.SURFACE,
                                border=ft.Border.all(1, Colors.BORDER),
                                border_radius=12,
                                alignment=ft.Alignment.CENTER,
                                tooltip="Recargar catálogo",
                                on_click=lambda _: self.refresh(),
                                content=ft.Icon(ft.Icons.REFRESH, color=Colors.TEXT_PRIMARY),
                            ),
                        ],
                    ),
                    self.category_row,
                    self.catalog_grid,
                ],
            ),
        )

        ticket_header = ft.Container(
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            bgcolor=Colors.NAVY,
            border_radius=ft.BorderRadius.only(top_left=16, top_right=16),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text("Ticket Activo", size=17, weight=ft.FontWeight.BOLD, color=Colors.ON_PRIMARY),
                            self.items_count_text,
                        ],
                    ),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                        bgcolor=Colors.CRIMSON_BG,
                        border_radius=99,
                        on_click=lambda _: self._clear_cart(),
                        content=ft.Text("Limpiar", size=12, weight=ft.FontWeight.BOLD, color=Colors.CRIMSON_TEXT),
                    ),
                ],
            ),
        )

        ticket_body = ft.Container(
            expand=True,
            padding=16,
            content=ft.Column(
                expand=True,
                spacing=10,
                controls=[
                    self.customer_dropdown,
                    self.price_mode_selector,
                    self.cart_list,
                    ft.Divider(height=1, color=Colors.BORDER),
                    self.payment_selector,
                    self.quick_cash_row,
                    self.amount_paid_field,
                    self.card_details_container,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[ft.Text("Subtotal", color=Colors.TEXT_SECONDARY), self.subtotal_text],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Total a pagar", size=16, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                            self.total_text,
                        ],
                    ),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                        bgcolor=Colors.EMERALD_SOFT,
                        border_radius=10,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("Cambio / Vuelto", size=13, color=Colors.EMERALD_DARK),
                                self.change_text,
                            ],
                        ),
                    ),
                    ft.Row(controls=[ft.Container(expand=True, content=self.checkout_btn)]),
                ],
            ),
        )

        ticket_panel = ft.Container(
            expand=35,
            bgcolor=Colors.SURFACE,
            border=ft.Border.all(1, Colors.BORDER),
            border_radius=16,
            shadow=CARD_SHADOW,
            content=ft.Column(expand=True, spacing=0, controls=[ticket_header, ticket_body]),
        )

        self.controls = [catalog_panel, ticket_panel]

    def _quick_cash_pill(self, label: str, value: Optional[Decimal]) -> ft.Control:
        return ft.Container(
            expand=True,
            padding=ft.Padding.symmetric(vertical=6),
            bgcolor=Colors.SURFACE_ALT,
            border=ft.Border.all(1, Colors.BORDER),
            border_radius=8,
            alignment=ft.Alignment.CENTER,
            on_click=lambda _: self._apply_quick_cash(value),
            content=ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
        )

    def _apply_quick_cash(self, value: Optional[Decimal]) -> None:
        if value is None:
            total = sum((self._effective_price(i) * i["quantity"] for i in self.cart.values()), Decimal("0.00"))
            self.amount_paid_field.value = f"{total:.2f}"
        else:
            self.amount_paid_field.value = f"{value:.2f}"
        self._recalculate_totals()

    def refresh(self) -> None:
        self.load_categories()
        self.load_customers()
        self.load_products()

    def load_customers(self) -> None:
        current = self.customer_dropdown.value or "0"
        options = [ft.dropdown.Option(key="0", text="Consumidor Final")]
        self.customers_map = {"0": "Consumidor Final"}
        try:
            for c in self.api.get_customers():
                cid = str(c["id"])
                label = c["full_name"]
                if c.get("document_number"):
                    label = f"{label} ({c['document_number']})"
                options.append(ft.dropdown.Option(key=cid, text=label))
                self.customers_map[cid] = c["full_name"]
        except POSApiError:
            pass
        self.customer_dropdown.options = options
        self.customer_dropdown.value = current if current in self.customers_map else "0"
        safe_update(self)

    def _category_pill(self, label: str, category_id: Optional[int], selected: bool) -> ft.Control:
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
            bgcolor=Colors.NAVY if selected else Colors.SURFACE,
            border=ft.Border.all(1, Colors.NAVY if selected else Colors.BORDER),
            border_radius=99,
            on_click=lambda _, cid=category_id: self._select_category(cid),
            content=ft.Text(
                label,
                size=13,
                weight=ft.FontWeight.W_600,
                color=Colors.ON_PRIMARY if selected else Colors.TEXT_SECONDARY,
            ),
        )

    def load_categories(self) -> None:
        self.category_row.controls.clear()
        self.category_row.controls.append(
            self._category_pill("Todas", None, self.selected_category_id is None)
        )
        try:
            self.categories_map.clear()
            for cat in self.api.get_categories():
                cat_id = cat["id"]
                self.categories_map[cat_id] = cat["name"]
                self.category_row.controls.append(
                    self._category_pill(cat["name"], cat_id, self.selected_category_id == cat_id)
                )
        except POSApiError as exc:
            self.on_notify(exc.detail, Colors.CRIMSON)
        safe_update(self)

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
                if stock == 0:
                    badge_bg, badge_fg, badge_txt = Colors.CRIMSON_BG, Colors.CRIMSON_TEXT, "Agotado"
                elif low_stock:
                    badge_bg, badge_fg, badge_txt = Colors.AMBER_BG, Colors.AMBER_TEXT, f"Bajo: {stock}"
                else:
                    badge_bg, badge_fg, badge_txt = Colors.SURFACE_ALT, Colors.TEXT_SECONDARY, f"Stock: {stock}"

                initials = "".join(w[0] for w in prod["name"].split()[:2]).upper() or "PR"
                img_url = self.api.resolve_media_url(prod.get("image_url"))
                cat_label = self.categories_map.get(prod.get("category_id"), prod["sku"]).upper()

                fallback_visual = ft.Container(
                    expand=True,
                    bgcolor=Colors.CANVAS,
                    border_radius=12,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                        controls=[
                            ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, size=34, color=Colors.EMERALD),
                            ft.Text(initials, size=14, weight=ft.FontWeight.BOLD, color=Colors.EMERALD_DARK),
                        ],
                    ),
                )
                product_visual = (
                    ft.Container(
                        expand=True,
                        bgcolor=Colors.SURFACE,
                        border_radius=12,
                        alignment=ft.Alignment.CENTER,
                        padding=4,
                        content=ft.Image(
                            src=img_url,
                            fit=ft.BoxFit.CONTAIN,
                            expand=True,
                            error_content=fallback_visual,
                        ),
                    )
                    if img_url
                    else fallback_visual
                )

                image_area = ft.Container(
                    expand=True,
                    content=ft.Stack(
                        expand=True,
                        controls=[
                            product_visual,
                            ft.Container(
                                top=0,
                                right=0,
                                padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                bgcolor=badge_bg,
                                border_radius=99,
                                content=ft.Text(badge_txt, size=10, weight=ft.FontWeight.BOLD, color=badge_fg),
                            ),
                        ],
                    ),
                )

                card = ft.Container(
                    padding=12,
                    bgcolor=Colors.SURFACE,
                    border=ft.Border.all(1, Colors.BORDER),
                    border_radius=16,
                    shadow=CARD_SHADOW,
                    on_click=lambda _, p=prod: self._add_to_cart(p),
                    content=ft.Column(
                        expand=True,
                        spacing=8,
                        controls=[
                            image_area,
                            ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.Text(
                                                f"${Decimal(str(prod['price'])):.2f}",
                                                size=20,
                                                weight=ft.FontWeight.BOLD,
                                                color=Colors.TEXT_PRIMARY,
                                            ),
                                            ft.Text(
                                                f"May: ${Decimal(str(prod['wholesale_price'])):.2f}" if prod.get("wholesale_price") is not None else "",
                                                size=11,
                                                weight=ft.FontWeight.W_600,
                                                color=Colors.AMBER_TEXT,
                                            ),
                                        ],
                                    ),
                                    ft.Text(
                                        prod["name"],
                                        size=13,
                                        weight=ft.FontWeight.W_600,
                                        color=Colors.TEXT_PRIMARY,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        cat_label,
                                        size=10,
                                        weight=ft.FontWeight.BOLD,
                                        color=Colors.EMERALD_DARK,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
                self.catalog_grid.controls.append(card)
        except POSApiError as exc:
            self.on_notify(exc.detail, Colors.CRIMSON)
        safe_update(self)

    def _add_to_cart(self, product: dict[str, Any]) -> None:
        pid = product["id"]
        stock = int(product["stock"])
        current_qty = self.cart.get(pid, {}).get("quantity", 0)
        if current_qty + 1 > stock:
            self.on_notify(f"Stock insuficiente para {product['name']} (disponible: {stock}).", Colors.AMBER_TEXT)
            return

        if pid in self.cart:
            self.cart[pid]["quantity"] += 1
        else:
            wp = product.get("wholesale_price")
            self.cart[pid] = {
                "product_id": pid,
                "name": product["name"],
                "price": Decimal(str(product["price"])),
                "wholesale_price": Decimal(str(wp)) if wp is not None else None,
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
            self.on_notify(f"Stock máximo alcanzado ({item['stock']}).", Colors.AMBER_TEXT)
            return
        else:
            item["quantity"] = new_qty
        self._render_cart()

    def _is_wholesale(self) -> bool:
        return next(iter(self.price_mode_selector.selected), "RETAIL") == "WHOLESALE"

    def _effective_price(self, item: dict[str, Any]) -> Decimal:
        if self._is_wholesale() and item.get("wholesale_price") is not None:
            return item["wholesale_price"]
        return item["price"]

    def _clear_cart(self) -> None:
        self.cart.clear()
        self.amount_paid_field.value = "0.00"
        self.customer_dropdown.value = "0"
        self.price_mode_selector.selected = ["RETAIL"]
        self.card_bank_field.value = ""
        self.card_auth_field.value = ""
        self.card_type_dropdown.value = "CREDITO"
        self._render_cart()

    def _render_cart(self) -> None:
        self.cart_list.controls.clear()
        total_units = sum(item["quantity"] for item in self.cart.values())
        self.items_count_text.value = f"{total_units} {'artículo' if total_units == 1 else 'artículos'}"
        wholesale_active = self._is_wholesale()

        for idx, (pid, item) in enumerate(self.cart.items()):
            unit_price = self._effective_price(item)
            using_wp = wholesale_active and item.get("wholesale_price") is not None
            line_total = unit_price * item["quantity"]
            row_bg = Colors.SURFACE if idx % 2 == 0 else Colors.CANVAS
            self.cart_list.controls.append(
                ft.Container(
                    padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                    bgcolor=row_bg,
                    border=ft.Border.all(1, Colors.BORDER),
                    border_radius=10,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                expand=True,
                                spacing=1,
                                controls=[
                                    ft.Text(item["name"], weight=ft.FontWeight.W_600, size=13, color=Colors.TEXT_PRIMARY),
                                    ft.Text(
                                        f"${unit_price:.2f} c/u" + (" (Mayoreo)" if using_wp else ""),
                                        size=11,
                                        color=Colors.AMBER_TEXT if using_wp else Colors.TEXT_MUTED,
                                    ),
                                ],
                            ),
                            ft.Row(
                                spacing=2,
                                controls=[
                                    ft.IconButton(ft.Icons.REMOVE_CIRCLE_OUTLINE, icon_size=18, on_click=lambda _, i=pid: self._update_qty(i, -1)),
                                    ft.Text(str(item["quantity"]), weight=ft.FontWeight.BOLD, size=13),
                                    ft.IconButton(ft.Icons.ADD_CIRCLE_OUTLINE, icon_size=18, on_click=lambda _, i=pid: self._update_qty(i, 1)),
                                ],
                            ),
                            ft.Text(f"${line_total:.2f}", weight=ft.FontWeight.BOLD, width=62, text_align=ft.TextAlign.RIGHT),
                            ft.IconButton(
                                ft.Icons.DELETE_OUTLINE,
                                icon_size=18,
                                icon_color=Colors.CRIMSON,
                                on_click=lambda _, i=pid: self._update_qty(i, -999999),
                            ),
                        ],
                    ),
                )
            )
        self._recalculate_totals()

    def _recalculate_totals(self) -> None:
        subtotal = sum((self._effective_price(i) * i["quantity"] for i in self.cart.values()), Decimal("0.00"))
        self.subtotal_text.value = f"${subtotal:.2f}"
        self.total_text.value = f"${subtotal:.2f}"
        self.checkout_btn.content = f"COBRAR  ${subtotal:.2f}"

        method = next(iter(self.payment_selector.selected), "CASH")
        is_card = method == "CARD"
        self.card_details_container.visible = is_card
        self.quick_cash_row.visible = not is_card
        self.amount_paid_field.visible = not is_card

        try:
            paid = Decimal(self.amount_paid_field.value or "0.00")
        except Exception:
            paid = Decimal("0.00")

        if is_card:
            paid = subtotal
            self.amount_paid_field.value = f"{subtotal:.2f}"

        change = max(Decimal("0.00"), paid - subtotal)
        self.change_text.value = f"${change:.2f}"
        safe_update(self)

    def _submit_sale(self) -> None:
        if not self.cart:
            self.on_notify("Agrega al menos un producto al ticket.", Colors.AMBER_TEXT)
            return

        method = next(iter(self.payment_selector.selected), "CASH")
        try:
            amount_paid = Decimal(self.amount_paid_field.value or "0.00")
        except Exception:
            self.on_notify("Ingresa un monto recibido válido.", Colors.CRIMSON)
            return

        card_bank = None
        card_type = None
        card_auth = None
        if method == "CARD":
            card_bank = (self.card_bank_field.value or "").strip()
            card_type = (self.card_type_dropdown.value or "").strip()
            card_auth = (self.card_auth_field.value or "").strip()
            if not card_bank or not card_type or not card_auth:
                self.on_notify(
                    "Para pagos con tarjeta ingresa Banco, Tipo (Crédito/Débito) y N° de autorización.",
                    Colors.CRIMSON,
                )
                return

        selected_cid = self.customer_dropdown.value or "0"
        customer_id = int(selected_cid) if selected_cid != "0" else None
        customer_name = self.customers_map.get(selected_cid, "Consumidor Final")

        use_wholesale = self._is_wholesale()
        items = [
            {"product_id": pid, "quantity": item["quantity"], "use_wholesale": use_wholesale}
            for pid, item in self.cart.items()
        ]
        try:
            sale = self.api.create_sale(
                items=items,
                payment_method=method,
                amount_paid=amount_paid,
                customer_id=customer_id,
                card_bank=card_bank,
                card_type=card_type,
                card_auth_number=card_auth,
            )
            self._clear_cart()
            self.load_products()
            self._show_receipt_dialog(sale, customer_name)
        except POSApiError as exc:
            self.on_notify(exc.detail, Colors.CRIMSON)

    def _show_receipt_dialog(self, sale: dict[str, Any], customer_name: str = "Consumidor Final") -> None:
        item_rows = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(f"{it['quantity']}x {it['product_name']}", size=13, color=Colors.TEXT_PRIMARY, expand=True),
                    ft.Text(f"${Decimal(str(it['line_total'])):.2f}", size=13, weight=ft.FontWeight.W_600),
                ],
            )
            for it in sale.get("items", [])
        ]

        def close_dlg(_: ft.ControlEvent) -> None:
            dlg.open = False
            safe_update(self.page)

        receipt_content = ft.Container(
            width=360,
            padding=16,
            bgcolor=Colors.CANVAS,
            border=ft.Border.all(1, Colors.BORDER),
            border_radius=12,
            content=ft.Column(
                tight=True,
                spacing=8,
                controls=[
                    ft.Text("MI TIENDITA FÁCIL", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Text(f"Ticket: {sale['ticket_number']}", size=12, color=Colors.TEXT_MUTED),
                    ft.Text(f"Cliente: {customer_name}", size=12, color=Colors.TEXT_PRIMARY, weight=ft.FontWeight.W_600),
                    ft.Text(f"Método de pago: {sale['payment_method']}", size=12, color=Colors.TEXT_MUTED),
                    *(
                        [
                            ft.Text(
                                f"Tarjeta {sale.get('card_type') or ''} · {sale.get('card_bank') or ''} (Auth: {sale.get('card_auth_number') or ''})",
                                size=11,
                                color=Colors.NAVY,
                                weight=ft.FontWeight.W_600,
                            )
                        ]
                        if sale.get("payment_method") == "CARD"
                        else []
                    ),
                    ft.Divider(height=1, color=Colors.BORDER),
                    *item_rows,
                    ft.Divider(height=1, color=Colors.BORDER),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[ft.Text("Subtotal"), ft.Text(f"${Decimal(str(sale['subtotal'])):.2f}")],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("TOTAL", size=16, weight=ft.FontWeight.BOLD),
                            ft.Text(f"${Decimal(str(sale['total'])):.2f}", size=18, weight=ft.FontWeight.BOLD, color=Colors.EMERALD_DARK),
                        ],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[ft.Text("Recibido"), ft.Text(f"${Decimal(str(sale['amount_paid'])):.2f}")],
                    ),
                    ft.Container(
                        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                        bgcolor=Colors.EMERALD_SOFT,
                        border_radius=8,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("Vuelto", weight=ft.FontWeight.BOLD, color=Colors.EMERALD_DARK),
                                ft.Text(f"${Decimal(str(sale['change_amount'])):.2f}", weight=ft.FontWeight.BOLD, color=Colors.EMERALD_DARK),
                            ],
                        ),
                    ),
                ],
            ),
        )

        dlg = ft.AlertDialog(
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=Colors.EMERALD),
                    ft.Text("Venta Completada", weight=ft.FontWeight.BOLD),
                ],
            ),
            content=receipt_content,
            actions=[
                ft.Button(
                    content="Nueva Venta",
                    bgcolor=Colors.EMERALD,
                    color=Colors.ON_PRIMARY,
                    on_click=close_dlg,
                )
            ],
        )
        try:
            self.page.show_dialog(dlg)
        except RuntimeError:
            pass
