from typing import Callable, Optional

import flet as ft

from app.services.api_client import POSApiClient, POSApiError
from app.theme import CARD_SHADOW, Colors
from app.views import safe_update


class LoginView(ft.Container):
    """Pantalla de inicio de sesión alineada a la plantilla Stitch de Mi Tiendita Fácil."""

    def __init__(
        self,
        api: POSApiClient,
        on_login_success: Callable[[dict], None],
    ):
        super().__init__(expand=True, bgcolor=Colors.CANVAS, padding=24)
        self.api = api
        self.on_login_success = on_login_success
        self.options: list[dict] = []
        self.selected_user_id: Optional[int] = None

        self.users_grid = ft.Row(wrap=True, spacing=10, run_spacing=10)
        self.username_field = ft.TextField(
            label="Usuario",
            hint_text="Selecciona una tarjeta o escribe tu nombre",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            border_radius=12,
        )
        self.password_field = ft.TextField(
            label="Contraseña",
            hint_text="Ingresa tu contraseña",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
            border_radius=12,
            on_submit=lambda _: self._handle_login(),
        )
        self.error_text = ft.Text("", size=12, weight=ft.FontWeight.W_600, color=Colors.CRIMSON_TEXT)
        self.error_banner = ft.Container(
            visible=False,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            bgcolor=Colors.CRIMSON_BG,
            border=ft.Border.all(1, Colors.CRIMSON),
            border_radius=10,
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=18, color=Colors.CRIMSON_TEXT),
                    self.error_text,
                ],
            ),
        )
        self.status_badge = ft.Container(
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            bgcolor="#1E293B",
            border_radius=99,
            border=ft.Border.all(1, "#334155"),
            content=ft.Row(
                tight=True,
                spacing=6,
                controls=[
                    ft.Icon(ft.Icons.CIRCLE, size=10, color=Colors.EMERALD),
                    ft.Text("Terminal Lista · Modo En Línea", size=11, weight=ft.FontWeight.W_600, color=Colors.ON_PRIMARY),
                ],
            ),
        )

        left_panel = ft.Container(
            width=340,
            padding=28,
            bgcolor=Colors.NAVY,
            border_radius=18,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        spacing=14,
                        controls=[
                            self.status_badge,
                            ft.Row(
                                spacing=10,
                                controls=[
                                    ft.Container(
                                        width=44,
                                        height=44,
                                        bgcolor=Colors.EMERALD,
                                        border_radius=12,
                                        alignment=ft.Alignment(0, 0),
                                        content=ft.Icon(ft.Icons.STOREFRONT, color=Colors.ON_PRIMARY, size=24),
                                    ),
                                    ft.Column(
                                        spacing=1,
                                        controls=[
                                            ft.Text("Mi Tiendita Fácil", size=20, weight=ft.FontWeight.BOLD, color=Colors.ON_PRIMARY),
                                            ft.Text("Sistema Punto de Venta", size=12, color="#94A3B8"),
                                        ],
                                    ),
                                ],
                            ),
                            ft.Divider(height=1, color="#1E293B"),
                            ft.Text(
                                "Control de Acceso por Rol",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=Colors.ON_PRIMARY,
                            ),
                            ft.Container(
                                padding=12,
                                bgcolor="#1E293B",
                                border_radius=12,
                                content=ft.Column(
                                    spacing=8,
                                    controls=[
                                        ft.Row(
                                            spacing=8,
                                            controls=[
                                                ft.Icon(ft.Icons.POINT_OF_SALE, size=16, color=Colors.EMERALD),
                                                ft.Text("Cajero: Ventas, Caja y Clientes", size=12, color="#E2E8F0"),
                                            ],
                                        ),
                                        ft.Row(
                                            spacing=8,
                                            controls=[
                                                ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=16, color=Colors.EMERALD),
                                                ft.Text("Encargado: Acceso completo y Usuarios", size=12, color="#E2E8F0"),
                                            ],
                                        ),
                                    ],
                                ),
                            ),
                        ],
                    ),
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text("Control de Turnos", size=11, weight=ft.FontWeight.W_600, color=Colors.EMERALD),
                            ft.Text(
                                "Inicia sesión con tu usuario asignado para operar la terminal.",
                                size=11,
                                color="#94A3B8",
                            ),
                        ],
                    ),
                ],
            ),
        )

        right_panel = ft.Container(
            expand=True,
            padding=28,
            bgcolor=Colors.SURFACE,
            border_radius=18,
            border=ft.Border.all(1, Colors.BORDER),
            shadow=CARD_SHADOW,
            content=ft.Column(
                spacing=14,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                expand=True,
                                controls=[
                                    ft.Text("Iniciar Turno de Trabajo", size=24, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                                    ft.Text(
                                        "Selecciona tu usuario e ingresa tu contraseña para comenzar.",
                                        size=13,
                                        color=Colors.TEXT_MUTED,
                                    ),
                                ],
                            ),
                            ft.IconButton(
                                ft.Icons.REFRESH,
                                tooltip="Recargar lista de usuarios",
                                icon_color=Colors.NAVY,
                                on_click=lambda _: self.refresh(),
                            ),
                        ],
                    ),
                    ft.Text("Usuarios disponibles", size=12, weight=ft.FontWeight.W_600, color=Colors.TEXT_SECONDARY),
                    self.users_grid,
                    ft.Divider(height=1, color=Colors.BORDER),
                    self.username_field,
                    self.password_field,
                    self.error_banner,
                    ft.Button(
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8,
                            controls=[
                                ft.Icon(ft.Icons.LOCK_OPEN, size=18, color=Colors.ON_PRIMARY),
                                ft.Text("Iniciar Sesión", size=15, weight=ft.FontWeight.BOLD, color=Colors.ON_PRIMARY),
                                ft.Icon(ft.Icons.ARROW_FORWARD, size=18, color=Colors.ON_PRIMARY),
                            ],
                        ),
                        height=48,
                        bgcolor=Colors.EMERALD_DARK,
                        color=Colors.ON_PRIMARY,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                        on_click=lambda _: self._handle_login(),
                    ),
                    ft.Text(
                        "Mi Tiendita Fácil POS",
                        size=11,
                        color=Colors.TEXT_MUTED,
                    ),
                ],
            ),
        )

        self.content = ft.Container(
            expand=True,
            alignment=ft.Alignment(0, 0),
            content=ft.Container(
                width=920,
                height=560,
                content=ft.Row(
                    expand=True,
                    spacing=18,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[left_panel, right_panel],
                ),
            ),
        )

    def _select_user_option(self, user_opt: dict) -> None:
        self.selected_user_id = user_opt["id"]
        self.username_field.value = user_opt["name"]
        self.error_banner.visible = False
        self._render_user_cards()
        safe_update(self)

    def _render_user_cards(self) -> None:
        self.users_grid.controls.clear()
        if not self.options:
            self.users_grid.controls.append(
                ft.Text("Ingresa tu usuario manualmente o verifica conexión con el backend.", size=12, color=Colors.TEXT_MUTED)
            )
            return

        for opt in self.options:
            is_selected = opt["id"] == self.selected_user_id
            is_manager = opt["role"] == "ENCARGADO"
            role_label = "Encargado" if is_manager else "Cajero"
            icon_data = ft.Icons.ADMIN_PANEL_SETTINGS if is_manager else ft.Icons.PERSON
            self.users_grid.controls.append(
                ft.Container(
                    width=168,
                    padding=12,
                    border_radius=12,
                    bgcolor=Colors.EMERALD_SOFT if is_selected else Colors.SURFACE_ALT,
                    border=ft.Border.all(
                        2 if is_selected else 1,
                        Colors.EMERALD_DARK if is_selected else Colors.BORDER,
                    ),
                    on_click=lambda _, u=opt: self._select_user_option(u),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=34,
                                height=34,
                                border_radius=10,
                                bgcolor=Colors.EMERALD_DARK if is_selected else Colors.NAVY,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon(icon_data, size=18, color=Colors.ON_PRIMARY),
                            ),
                            ft.Column(
                                spacing=1,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        opt["name"],
                                        size=13,
                                        weight=ft.FontWeight.BOLD,
                                        color=Colors.TEXT_PRIMARY,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        f"{role_label} · #{opt['id']}",
                                        size=11,
                                        color=Colors.EMERALD_DARK if is_selected else Colors.TEXT_MUTED,
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
            )

    def _show_error(self, message: str) -> None:
        self.error_text.value = message
        self.error_banner.visible = True
        safe_update(self)

    def _handle_login(self) -> None:
        username = (self.username_field.value or "").strip()
        password = self.password_field.value or ""

        if not username and self.selected_user_id is None:
            self._show_error("Selecciona un usuario o escribe tu nombre.")
            return
        if not password:
            self._show_error("Ingresa tu contraseña.")
            return

        selected_match = next(
            (opt for opt in self.options if opt["id"] == self.selected_user_id and opt["name"].lower() == username.lower()),
            None,
        )
        try:
            data = self.api.login(
                password=password,
                user_id=selected_match["id"] if selected_match else None,
                name=None if selected_match else username,
            )
            self.password_field.value = ""
            self.error_banner.visible = False
            self.on_login_success(data["user"])
        except POSApiError as exc:
            self._show_error(exc.detail)
        except Exception as exc:
            self._show_error(f"No se pudo conectar con el servidor: {exc}")

    def refresh(self) -> None:
        self.error_banner.visible = False
        self.password_field.value = ""
        try:
            self.options = self.api.get_login_options()
            if self.options and self.selected_user_id is None:
                self.selected_user_id = self.options[0]["id"]
                self.username_field.value = self.options[0]["name"]
        except Exception:
            self.options = []
        self._render_user_cards()
        safe_update(self)

