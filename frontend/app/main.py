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
    page.bgcolor = Colors.SURFACE
    page.theme = ft.Theme(font_family=FONT_FAMILY, color_scheme_seed=Colors.PRIMARY)
    page.padding = 0

    api = POSApiClient()

    def notify(message: str, color: str = Colors.PRIMARY) -> None:
        page.show_dialog(ft.SnackBar(content=ft.Text(message, color=Colors.ON_PRIMARY), bgcolor=color))

    cash_badge = ft.Container(
        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        border_radius=99,
        bgcolor=Colors.ERROR_CONTAINER,
        content=ft.Text("Caja cerrada", size=12, weight=ft.FontWeight.BOLD, color=Colors.ERROR),
    )

    def refresh_cash_badge() -> None:
        try:
            summary = api.get_current_cash_session()
            cashier = summary["session"]["cashier_name"]
            cash_badge.bgcolor = Colors.PRIMARY_CONTAINER
            cash_badge.content = ft.Text(f"Caja abierta: {cashier}", size=12, weight=ft.FontWeight.BOLD, color=Colors.ON_PRIMARY)
        except POSApiError:
            cash_badge.bgcolor = Colors.ERROR_CONTAINER
            cash_badge.content = ft.Text("Caja cerrada", size=12, weight=ft.FontWeight.BOLD, color=Colors.ERROR)
        page.update()

    pos_view = POSTerminalView(api=api, on_notify=notify)
    cash_view = CashRegisterView(api=api, on_notify=notify, on_session_changed=refresh_cash_badge)
    products_view = ProductsView(api=api)
    customers_view = CustomersView(api=api)
    reports_view = ReportsView(api=api)

    views = [pos_view, cash_view, products_view, customers_view, reports_view]
    body_host = ft.Container(expand=True, padding=16, content=pos_view)

    def on_nav_change(e: ft.ControlEvent) -> None:
        idx = e.control.selected_index
        body_host.content = views[idx]
        views[idx].refresh()
        page.update()

    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        bgcolor=Colors.SURFACE_CONTAINER_LOWEST,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.POINT_OF_SALE, label="Vender"),
            ft.NavigationRailDestination(icon=ft.Icons.ACCOUNT_BALANCE_WALLET, label="Caja"),
            ft.NavigationRailDestination(icon=ft.Icons.INVENTORY_2, label="Productos"),
            ft.NavigationRailDestination(icon=ft.Icons.PEOPLE, label="Clientes"),
            ft.NavigationRailDestination(icon=ft.Icons.BAR_CHART, label="Reportes"),
        ],
        on_change=on_nav_change,
    )

    header = ft.Container(
        height=56,
        padding=ft.Padding.symmetric(horizontal=20),
        bgcolor=Colors.SURFACE_CONTAINER_LOWEST,
        border=ft.Border.only(bottom=ft.BorderSide(1, Colors.OUTLINE_VARIANT)),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("Mi Tiendita Fácil", size=18, weight=ft.FontWeight.BOLD, color=Colors.ON_SURFACE),
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
                ft.Row(expand=True, spacing=0, controls=[rail, ft.VerticalDivider(width=1), body_host]),
            ],
        )
    )

    refresh_cash_badge()
    pos_view.refresh()


if __name__ == "__main__":
    ft.run(main)

