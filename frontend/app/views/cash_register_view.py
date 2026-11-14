from decimal import Decimal
from typing import Callable

import flet as ft

from app.services.api_client import POSApiClient, POSApiError
from app.theme import CARD_SHADOW, Colors
from app.views import safe_update


class CashRegisterView(ft.Container):
    """Vista de apertura, resumen de turno y cierre de caja (diseño 01)."""

    def __init__(
        self,
        api: POSApiClient,
        on_notify: Callable[[str, str], None],
        on_session_changed: Callable[[], None],
    ):
        super().__init__(expand=True, padding=24, alignment=ft.Alignment.CENTER)
        self.api = api
        self.on_notify = on_notify
        self.on_session_changed = on_session_changed

        self.cashier_field = ft.TextField(
            label="Nombre del cajero",
            value="Cajero Principal",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            border_color=Colors.BORDER,
            focused_border_color=Colors.EMERALD,
            border_radius=12,
        )
        self.opening_field = ft.TextField(
            label="Fondo inicial de caja ($)",
            value="100.00",
            prefix_icon=ft.Icons.ATTACH_MONEY,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=Colors.BORDER,
            focused_border_color=Colors.EMERALD,
            border_radius=12,
        )
        self.closing_field = ft.TextField(
            label="Efectivo físico contado al cierre ($)",
            value="0.00",
            prefix_icon=ft.Icons.ATTACH_MONEY,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=Colors.BORDER,
            focused_border_color=Colors.EMERALD,
            border_radius=12,
        )
        self.card_body = ft.Column(spacing=16, tight=True)
        self.content = ft.Container(
            width=540,
            padding=28,
            bgcolor=Colors.SURFACE,
            border=ft.Border.all(1, Colors.BORDER),
            border_radius=20,
            shadow=CARD_SHADOW,
            content=self.card_body,
        )

    def _kpi_box(self, title: str, value: str, accent: str = Colors.TEXT_PRIMARY) -> ft.Control:
        return ft.Container(
            expand=True,
            padding=14,
            bgcolor=Colors.CANVAS,
            border=ft.Border.all(1, Colors.BORDER),
            border_radius=12,
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Text(title, size=11, weight=ft.FontWeight.W_600, color=Colors.TEXT_MUTED),
                    ft.Text(value, size=18, weight=ft.FontWeight.BOLD, color=accent),
                ],
            ),
        )

    def refresh(self) -> None:
        self.card_body.controls.clear()
        try:
            summary = self.api.get_current_cash_session()
            sess = summary["session"]
            self.card_body.controls.extend(
                [
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Turno de Caja Activo", size=22, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                                    ft.Text(f"Cajero responsable: {sess['cashier_name']}", size=13, color=Colors.TEXT_MUTED),
                                ],
                            ),
                            ft.Container(
                                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                                bgcolor=Colors.EMERALD_SOFT,
                                border_radius=99,
                                content=ft.Text("ABIERTA", size=12, weight=ft.FontWeight.BOLD, color=Colors.EMERALD_DARK),
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=10,
                        controls=[
                            self._kpi_box("Fondo Inicial", f"${sess['opening_amount']}"),
                            self._kpi_box("Ventas Efectivo", f"${summary['cash_sales_total']}", Colors.EMERALD_DARK),
                            self._kpi_box("Esperado Gaveta", f"${summary['expected_cash_in_drawer']}", Colors.NAVY),
                        ],
                    ),
                    ft.Divider(height=1, color=Colors.BORDER),
                    self.closing_field,
                    ft.Row(
                        controls=[
                            ft.Container(
                                expand=True,
                                content=ft.Button(
                                    content="Realizar Arqueo y Cerrar Caja",
                                    icon=ft.Icons.LOCK,
                                    bgcolor=Colors.CRIMSON,
                                    color=Colors.ON_PRIMARY,
                                    height=52,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14)),
                                    on_click=lambda _: self._close_cash(),
                                ),
                            )
                        ]
                    ),
                ]
            )
        except POSApiError:
            quick_amounts = ft.Row(
                spacing=8,
                controls=[
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(vertical=8),
                        bgcolor=Colors.SURFACE_ALT,
                        border=ft.Border.all(1, Colors.BORDER),
                        border_radius=10,
                        alignment=ft.Alignment.CENTER,
                        on_click=lambda _, v=amt: self._set_opening(v),
                        content=ft.Text(f"${amt}", weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                    )
                    for amt in ("50.00", "100.00", "200.00")
                ],
            )
            self.card_body.controls.extend(
                [
                    ft.Row(
                        spacing=12,
                        controls=[
                            ft.Container(
                                width=48,
                                height=48,
                                border_radius=14,
                                bgcolor=Colors.EMERALD_SOFT,
                                alignment=ft.Alignment.CENTER,
                                content=ft.Icon(ft.Icons.STOREFRONT, color=Colors.EMERALD_DARK, size=26),
                            ),
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Iniciar Turno de Trabajo", size=22, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                                    ft.Text("Ingresa el cajero y el fondo inicial para comenzar a vender.", size=13, color=Colors.TEXT_MUTED),
                                ],
                            ),
                        ],
                    ),
                    ft.Divider(height=1, color=Colors.BORDER),
                    self.cashier_field,
                    self.opening_field,
                    quick_amounts,
                    ft.Row(
                        controls=[
                            ft.Container(
                                expand=True,
                                content=ft.Button(
                                    content="Abrir Caja y Comenzar",
                                    icon=ft.Icons.LOCK_OPEN,
                                    bgcolor=Colors.EMERALD,
                                    color=Colors.ON_PRIMARY,
                                    height=54,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14)),
                                    on_click=lambda _: self._open_cash(),
                                ),
                            )
                        ]
                    ),
                ]
            )
        safe_update(self)

    def _set_opening(self, value: str) -> None:
        self.opening_field.value = value
        safe_update(self)

    def _open_cash(self) -> None:
        try:
            amount = Decimal(self.opening_field.value or "0.00")
            self.api.open_cash_session(self.cashier_field.value or "Cajero", amount)
            self.on_notify("Caja abierta correctamente.", Colors.EMERALD_DARK)
            self.on_session_changed()
            self.refresh()
        except Exception as exc:
            self.on_notify(str(exc), Colors.CRIMSON)

    def _close_cash(self) -> None:
        try:
            amount = Decimal(self.closing_field.value or "0.00")
            res = self.api.close_cash_session(amount)
            self.on_notify(f"Caja cerrada. Diferencia: ${res['difference']}", Colors.EMERALD_DARK)
            self.on_session_changed()
            self.refresh()
        except Exception as exc:
            self.on_notify(str(exc), Colors.CRIMSON)
