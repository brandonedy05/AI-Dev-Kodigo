import sys
from pathlib import Path

import flet as ft

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.api_client import POSApiClient, POSApiError
from app.theme import Colors, FONT_FAMILY
from app.views.cash_register_view import CashRegisterView
from app.views.login_view import LoginView
from app.views.pos_terminal_view import POSTerminalView
from app.views.secondary_views import CustomersView, ProductsView, ReportsView
from app.views.users_view import UsersView


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

    session_badge_text = ft.Text("Sin sesión", size=12, weight=ft.FontWeight.W_600, color=Colors.ON_PRIMARY)
    session_badge_icon = ft.Icon(ft.Icons.PERSON_OUTLINE, size=16, color=Colors.EMERALD)
    session_badge = ft.Container(
        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        border_radius=99,
        bgcolor="#1E293B",
        border=ft.Border.all(1, "#334155"),
        content=ft.Row(
            tight=True,
            spacing=6,
            controls=[session_badge_icon, session_badge_text],
        ),
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
    users_view = UsersView(api=api, on_notify=notify)

    all_nav_defs = [
        ("Vender", ft.Icons.POINT_OF_SALE, pos_view, {"CAJERO", "ENCARGADO"}),
        ("Caja", ft.Icons.ACCOUNT_BALANCE_WALLET, cash_view, {"CAJERO", "ENCARGADO"}),
        ("Productos", ft.Icons.INVENTORY_2, products_view, {"ENCARGADO"}),
        ("Clientes", ft.Icons.PEOPLE, customers_view, {"CAJERO", "ENCARGADO"}),
        ("Reportes", ft.Icons.BAR_CHART, reports_view, {"ENCARGADO"}),
        ("Usuarios", ft.Icons.MANAGE_ACCOUNTS, users_view, {"ENCARGADO"}),
    ]

    active_tabs: list[tuple[str, ft.IconData, ft.Control]] = []
    selected_idx = 0
    body_host = ft.Container(expand=True, content=pos_view)

    def render_sidebar() -> None:
        nav_controls: list[ft.Control] = []
        for idx, (label, icon, _) in enumerate(active_tabs):
            active = idx == selected_idx
            nav_controls.append(
                ft.Container(
                    key=f"nav-{label}-{idx}",
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
        sidebar.content = ft.Column(
            key=f"sidebar-{len(active_tabs)}-{selected_idx}",
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=nav_controls,
        )

    def select_tab(idx: int) -> None:
        nonlocal selected_idx
        if idx < 0 or idx >= len(active_tabs):
            return
        selected_idx = idx
        render_sidebar()
        _, _, target_view = active_tabs[idx]
        body_host.content = target_view
        page.update()
        target_view.refresh()

    sidebar = ft.Container(
        width=98,
        padding=ft.Padding.symmetric(vertical=14, horizontal=8),
        bgcolor=Colors.NAVY,
        border=ft.Border.only(top=ft.BorderSide(1, "#1E293B")),
        content=ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
    )

    root_host = ft.Container(expand=True)

    def handle_logout(_=None) -> None:
        nonlocal active_tabs, selected_idx
        api.logout()
        active_tabs = []
        selected_idx = 0
        sidebar.content = ft.Column(spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        body_host.content = ft.Container()
        login_view.selected_user_id = None
        root_host.content = login_view
        page.update()
        login_view.refresh()
        notify("Sesión cerrada correctamente.", Colors.NAVY)

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
                ft.Row(
                    spacing=10,
                    controls=[
                        session_badge,
                        cash_badge,
                        ft.IconButton(
                            ft.Icons.LOGOUT,
                            icon_color="#E2E8F0",
                            tooltip="Cerrar sesión",
                            on_click=handle_logout,
                        ),
                    ],
                ),
            ],
        ),
    )

    app_shell = ft.Column(
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

    def handle_login_success(user: dict) -> None:
        nonlocal active_tabs, selected_idx
        role = user.get("role", "CAJERO")
        role_label = "Encargado" if role == "ENCARGADO" else "Cajero"
        session_badge_icon.name = ft.Icons.ADMIN_PANEL_SETTINGS if role == "ENCARGADO" else ft.Icons.PERSON
        session_badge_text.value = f"{user.get('name', 'Usuario')} · {role_label}"

        if hasattr(cash_view, "cashier_field"):
            cash_view.cashier_field.value = user.get("name", "")

        active_tabs = [
            (label, icon, view)
            for label, icon, view, allowed_roles in all_nav_defs
            if role in allowed_roles
        ]
        selected_idx = 0
        render_sidebar()
        body_host.content = active_tabs[0][2]
        root_host.content = app_shell
        page.update()
        refresh_cash_badge()
        active_tabs[0][2].refresh()
        notify(f"Bienvenido, {user.get('name', '')} ({role_label}).", Colors.EMERALD_DARK)

    login_view = LoginView(api=api, on_login_success=handle_login_success)
    root_host.content = login_view
    page.add(root_host)
    login_view.refresh()


if __name__ == "__main__":
    ft.run(main)
