import sys
from pathlib import Path

import flet as ft

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.api_client import POSApiClient, POSApiError
from app.theme import Colors, FONT_FAMILY
from app.views.cash_register_view import CashRegisterView
from app.views.pos_terminal_view import POSTerminalView
from app.views.secondary_views import CustomersView, ProductsView, ReportsView


def main(page: ft.Page) -> None:
    page.title = "Mi Tiendita Fácil - POS"
    page.bgcolor = Colors.CANVAS
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(font_family=FONT_FAMILY, color_scheme_seed=Colors.EMERALD)
    page.padding = 0

    api = POSApiClient()

    def notify(message: str, color: str = Colors.EMERALD_DARK) -> None:
        page.show_dialog(ft.SnackBar(content=ft.Text(message, color=Colors.ON_PRIMARY), bgcolor=color))

    cash_badge = ft.Container(
        padding=ft.Padding.symmetric(horizontal=14, vertical=6),
        border_radius=99,
        bgcolor=Colors.CRIMSON_BG,
        content=ft.Text("Caja cerrada", size=12, weight=ft.FontWeight.BOLD, color=Colors.CRIMSON_TEXT),
    )

    def refresh_cash_badge() -> None:
        try:
            summary = api.get_current_cash_session()
            cashier = summary["session"]["cashier_name"]
            cash_badge.bgcolor = Colors.EMERALD
            cash_badge.content = ft.Text(
                f"Caja abierta · {cashier}",
                size=12,
                weight=ft.FontWeight.BOLD,
                color=Colors.ON_PRIMARY,
            )
        except POSApiError:
            cash_badge.bgcolor = Colors.CRIMSON_BG
            cash_badge.content = ft.Text("Caja cerrada", size=12, weight=ft.FontWeight.BOLD, color=Colors.CRIMSON_TEXT)
        page.update()

    pos_view = POSTerminalView(api=api, on_notify=notify)
    cash_view = CashRegisterView(api=api, on_notify=notify, on_session_changed=refresh_cash_badge)
    products_view = ProductsView(api=api, on_notify=notify)
    customers_view = CustomersView(api=api, on_notify=notify)
    reports_view = ReportsView(api=api)

    views = [pos_view, cash_view, products_view, customers_view, reports_view]
    body_host = ft.Container(expand=True, content=pos_view)

    nav_items = [
        ("Vender", ft.Icons.POINT_OF_SALE),
        ("Caja", ft.Icons.ACCOUNT_BALANCE_WALLET),
        ("Productos", ft.Icons.INVENTORY_2),
        ("Clientes", ft.Icons.PEOPLE),
        ("Reportes", ft.Icons.BAR_CHART),
    ]
    selected_idx = 0
    sidebar_col = ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def render_sidebar() -> None:
        sidebar_col.controls.clear()
        for idx, (label, icon) in enumerate(nav_items):
            active = idx == selected_idx
            sidebar_col.controls.append(
                ft.Container(
                    width=80,
                    padding=ft.Padding.symmetric(vertical=12, horizontal=6),
                    border_radius=12,
                    bgcolor=Colors.EMERALD if active else "#1E293B",
                    border=ft.Border.all(1, Colors.EMERALD if active else "#334155"),
                    on_click=lambda _, i=idx: select_tab(i),
                    content=ft.Column(
                        spacing=4,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(icon, size=22, color=Colors.ON_PRIMARY if active else "#E2E8F0"),
                            ft.Text(
                                label,
                                size=11,
                                weight=ft.FontWeight.BOLD if active else ft.FontWeight.W_600,
                                color=Colors.ON_PRIMARY if active else "#E2E8F0",
                            ),
                        ],
                    ),
                )
            )

    def select_tab(idx: int) -> None:
        nonlocal selected_idx
        selected_idx = idx
        render_sidebar()
        body_host.content = views[idx]
        page.update()
        views[idx].refresh()

    render_sidebar()
    sidebar = ft.Container(
        width=98,
        padding=ft.Padding.symmetric(vertical=14, horizontal=8),
        bgcolor=Colors.NAVY,
        border=ft.Border.only(top=ft.BorderSide(1, "#1E293B")),
        content=sidebar_col,
    )

    header = ft.Container(
        height=60,
        padding=ft.Padding.symmetric(horizontal=20),
        bgcolor=Colors.NAVY,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.Container(
                            width=34,
                            height=34,
                            border_radius=10,
                            bgcolor=Colors.EMERALD,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Icon(ft.Icons.STOREFRONT, color=Colors.ON_PRIMARY, size=20),
                        ),
                        ft.Text("Mi Tiendita Fácil", size=18, weight=ft.FontWeight.BOLD, color=Colors.ON_PRIMARY),
                        ft.Text("POS", size=12, weight=ft.FontWeight.BOLD, color=Colors.EMERALD),
                    ],
                ),
                cash_badge,
            ],
        ),
    )

    page.add(
        ft.Column(
            expand=True,
            spacing=0,
            controls=[
                header,
                ft.Row(
                    expand=True,
                    spacing=0,
                    controls=[sidebar, body_host],
                ),
            ],
        )
    )

    refresh_cash_badge()
    pos_view.refresh()


if __name__ == "__main__":
    ft.run(main)
