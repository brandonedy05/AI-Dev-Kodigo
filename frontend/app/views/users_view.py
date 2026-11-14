from typing import Callable, Optional

import flet as ft

from app.services.api_client import POSApiClient, POSApiError
from app.theme import CARD_SHADOW, Colors
from app.views import safe_update


class UsersView(ft.Container):
    """Vista de mantenimiento CRUD de usuarios y roles (exclusiva para Encargado)."""

    def __init__(self, api: POSApiClient, on_notify: Callable[[str, str], None]):
        super().__init__(expand=True, padding=20)
        self.api = api
        self.on_notify = on_notify
        self.users: list[dict] = []

        self.search_field = ft.TextField(
            hint_text="Buscar usuario por nombre o ID...",
            prefix_icon=ft.Icons.SEARCH,
            expand=True,
            border_radius=12,
            on_change=lambda _: self._render_table(),
        )
        self.stats_text = ft.Text("0 usuarios", size=12, color=Colors.TEXT_MUTED)
        self.users_table = ft.DataTable(
            heading_row_color=Colors.SURFACE_ALT,
            column_spacing=22,
            columns=[
                ft.DataColumn(ft.Text("ID", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Nombre", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Rol", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
            ],
            rows=[],
        )

        self.content = ft.Column(
            expand=True,
            spacing=16,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("Mantenimiento de Usuarios", size=24, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                                ft.Text(
                                    "Administra perfiles de Cajero y Encargado con contraseñas salteadas y control de acceso.",
                                    size=13,
                                    color=Colors.TEXT_MUTED,
                                ),
                            ],
                        ),
                        ft.Button(
                            content=ft.Row(
                                spacing=6,
                                controls=[
                                    ft.Icon(ft.Icons.PERSON_ADD_ALT_1, size=18, color=Colors.ON_PRIMARY),
                                    ft.Text("Nuevo Usuario", weight=ft.FontWeight.BOLD, color=Colors.ON_PRIMARY),
                                ],
                            ),
                            bgcolor=Colors.EMERALD_DARK,
                            color=Colors.ON_PRIMARY,
                            height=42,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                            on_click=lambda _: self._open_user_dialog(None),
                        ),
                    ],
                ),
                ft.Row(
                    spacing=12,
                    controls=[
                        self.search_field,
                        self.stats_text,
                    ],
                ),
                ft.Container(
                    expand=True,
                    padding=16,
                    bgcolor=Colors.SURFACE,
                    border=ft.Border.all(1, Colors.BORDER),
                    border_radius=16,
                    shadow=CARD_SHADOW,
                    content=ft.Column(
                        expand=True,
                        scroll=ft.ScrollMode.AUTO,
                        controls=[
                            ft.Row(
                                scroll=ft.ScrollMode.AUTO,
                                controls=[self.users_table],
                            )
                        ],
                    ),
                ),
            ],
        )

    def _open_user_dialog(self, user: Optional[dict]) -> None:
        if not self.page:
            return
        is_edit = user is not None
        name_field = ft.TextField(
            label="Nombre de usuario *",
            value=user["name"] if is_edit else "",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
        )
        role_dd = ft.Dropdown(
            label="Rol *",
            value=user["role"] if is_edit else "CAJERO",
            options=[
                ft.dropdown.Option("CAJERO", "Cajero (Ventas, Caja y Clientes)"),
                ft.dropdown.Option("ENCARGADO", "Encargado (Acceso total)"),
            ],
        )
        password_field = ft.TextField(
            label="Contraseña *" if not is_edit else "Nueva contraseña (opcional)",
            hint_text="Mínimo 4 caracteres" if not is_edit else "Dejar vacío para conservar la actual",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_OUTLINE,
        )
        confirm_field = ft.TextField(
            label="Confirmar contraseña",
            password=True,
            can_reveal_password=True,
            prefix_icon=ft.Icons.LOCK_RESET,
        )
        active_switch = ft.Switch(
            label="Usuario activo",
            value=bool(user.get("is_active", True)) if is_edit else True,
            visible=is_edit,
        )

        def save(_):
            name = (name_field.value or "").strip()
            role = role_dd.value or "CAJERO"
            pwd = password_field.value or ""
            confirm = confirm_field.value or ""

            if len(name) < 2:
                self.on_notify("El nombre debe tener al menos 2 caracteres.", Colors.CRIMSON)
                return
            if not is_edit and len(pwd) < 4:
                self.on_notify("La contraseña debe tener al menos 4 caracteres.", Colors.CRIMSON)
                return
            if pwd and len(pwd) < 4:
                self.on_notify("La nueva contraseña debe tener al menos 4 caracteres.", Colors.CRIMSON)
                return
            if pwd != confirm:
                self.on_notify("Las contraseñas no coinciden.", Colors.CRIMSON)
                return

            try:
                if is_edit:
                    payload: dict = {
                        "name": name,
                        "role": role,
                        "is_active": bool(active_switch.value),
                    }
                    if pwd:
                        payload["password"] = pwd
                    self.api.update_user(user["id"], payload)
                    self.on_notify(f"Usuario '{name}' actualizado.", Colors.EMERALD_DARK)
                else:
                    self.api.create_user(name=name, password=pwd, role=role)
                    self.on_notify(f"Usuario '{name}' creado.", Colors.EMERALD_DARK)
                self.page.pop_dialog()
                self.refresh()
            except POSApiError as exc:
                self.on_notify(exc.detail, Colors.CRIMSON)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                f"Editar Usuario #{user['id']}" if is_edit else "Registrar Nuevo Usuario",
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    tight=True,
                    spacing=12,
                    controls=[
                        name_field,
                        role_dd,
                        password_field,
                        confirm_field,
                        active_switch,
                    ],
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: self.page.pop_dialog()),
                ft.Button(
                    content=ft.Text("Guardar", color=Colors.ON_PRIMARY, weight=ft.FontWeight.BOLD),
                    bgcolor=Colors.EMERALD_DARK,
                    on_click=save,
                ),
            ],
        )
        self.page.show_dialog(dlg)

    def _toggle_user_status(self, user: dict) -> None:
        try:
            if user.get("is_active", True):
                self.api.delete_user(user["id"])
                self.on_notify(f"Usuario '{user['name']}' desactivado.", Colors.AMBER_TEXT)
            else:
                self.api.update_user(user["id"], {"is_active": True})
                self.on_notify(f"Usuario '{user['name']}' reactivado.", Colors.EMERALD_DARK)
            self.refresh()
        except POSApiError as exc:
            self.on_notify(exc.detail, Colors.CRIMSON)

    def _render_table(self) -> None:
        self.users_table.rows.clear()
        term = (self.search_field.value or "").strip().lower()
        filtered = [
            u for u in self.users
            if not term or term in u["name"].lower() or term == str(u["id"])
        ]
        active_count = sum(1 for u in self.users if u.get("is_active", True))
        self.stats_text.value = f"{len(filtered)} mostrados · {active_count} activos"

        for u in filtered:
            is_manager = u["role"] == "ENCARGADO"
            is_active = bool(u.get("is_active", True))
            role_badge = ft.Container(
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                border_radius=8,
                bgcolor=Colors.EMERALD_SOFT if is_manager else Colors.SURFACE_ALT,
                content=ft.Text(
                    "Encargado" if is_manager else "Cajero",
                    size=11,
                    weight=ft.FontWeight.W_600,
                    color=Colors.EMERALD_DARK if is_manager else Colors.NAVY,
                ),
            )
            status_badge = ft.Container(
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                border_radius=8,
                bgcolor=Colors.EMERALD_SOFT if is_active else Colors.CRIMSON_BG,
                content=ft.Text(
                    "Activo" if is_active else "Inactivo",
                    size=11,
                    weight=ft.FontWeight.W_600,
                    color=Colors.EMERALD_DARK if is_active else Colors.CRIMSON_TEXT,
                ),
            )
            self.users_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(f"#{u['id']}", weight=ft.FontWeight.W_600, size=12, color=Colors.TEXT_MUTED)),
                        ft.DataCell(ft.Text(u["name"], weight=ft.FontWeight.W_600, size=13, color=Colors.TEXT_PRIMARY)),
                        ft.DataCell(role_badge),
                        ft.DataCell(status_badge),
                        ft.DataCell(
                            ft.Row(
                                spacing=4,
                                controls=[
                                    ft.IconButton(
                                        ft.Icons.EDIT_OUTLINED,
                                        icon_size=18,
                                        icon_color=Colors.NAVY,
                                        tooltip="Editar usuario",
                                        on_click=lambda _, usr=u: self._open_user_dialog(usr),
                                    ),
                                    ft.IconButton(
                                        ft.Icons.PERSON_OFF_OUTLINED if is_active else ft.Icons.RESTORE,
                                        icon_size=18,
                                        icon_color=Colors.CRIMSON if is_active else Colors.EMERALD_DARK,
                                        tooltip="Desactivar usuario" if is_active else "Reactivar usuario",
                                        on_click=lambda _, usr=u: self._toggle_user_status(usr),
                                    ),
                                ],
                            )
                        ),
                    ]
                )
            )
        safe_update(self)

    def refresh(self) -> None:
        try:
            self.users = self.api.get_users(include_inactive=True)
        except POSApiError as exc:
            self.users = []
            self.on_notify(exc.detail, Colors.CRIMSON)
        self._render_table()

