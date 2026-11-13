from decimal import Decimal
from typing import Callable

import flet as ft

from app.services.api_client import POSApiClient, POSApiError
from app.theme import Colors


class CashRegisterView(ft.Container):
    """Vista de apertura, resumen en tiempo real y cierre de caja."""

    def __init__(
        self,
        api: POSApiClient,
        on_notify: Callable[[str, str], None],
        on_session_changed: Callable[[], None],
    ):
        super().__init__(expand=True, padding=24)
        self.api = api
        self.on_notify = on_notify
        self.on_session_changed = on_session_changed

        self.cashier_field = ft.TextField(label="Nombre del cajero", value="Cajero Principal", width=320)
        self.opening_field = ft.TextField(label="Fondo inicial ($)", value="100.00", width=320)
        self.closing_field = ft.TextField(label="Efectivo contado al cierre ($)", value="0.00", width=320)
        self.status_container = ft.Column(spacing=12)
        self.content = self.status_container

    def refresh(self) -> None:
        self.status_container.controls.clear()
        try:
            summary = self.api.get_current_cash_session()
            sess = summary["session"]
            self.status_container.controls.extend(
                [
                    ft.Text("Caja Abierta", size=24, weight=ft.FontWeight.BOLD, color=Colors.PRIMARY),
                    ft.Text(f"Cajero: {sess['cashier_name']} | Fondo inicial: ${sess['opening_amount']}"),
                    ft.Text(f"Ventas en efectivo: ${summary['cash_sales_total']}"),
                    ft.Text(
                        f"Efectivo esperado en gaveta: ${summary['expected_cash_in_drawer']}",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                    self.closing_field,
                    ft.Button(
                        content="Cerrar Caja",
                        icon=ft.Icons.LOCK,
                        bgcolor=Colors.ERROR,
                        color=Colors.ON_PRIMARY,
                        on_click=lambda _: self._close_cash(),
                    ),
                ]
            )
        except POSApiError:
            self.status_container.controls.extend(
                [
                    ft.Text("Apertura de Caja", size=24, weight=ft.FontWeight.BOLD, color=Colors.ON_SURFACE),
                    ft.Text("Abre un turno para habilitar el registro de ventas.", color=Colors.ON_SURFACE_VARIANT),
                    self.cashier_field,
                    self.opening_field,
                    ft.Button(
                        content="Abrir Caja",
                        icon=ft.Icons.LOCK_OPEN,
                        bgcolor=Colors.PRIMARY_CONTAINER,
                        color=Colors.ON_PRIMARY,
                        on_click=lambda _: self._open_cash(),
                    ),
                ]
            )
        self.update()

    def _open_cash(self) -> None:
        try:
            amount = Decimal(self.opening_field.value or "0.00")
            self.api.open_cash_session(self.cashier_field.value or "Cajero", amount)
            self.on_notify("Caja abierta correctamente.", Colors.PRIMARY)
            self.on_session_changed()
            self.refresh()
        except Exception as exc:
            self.on_notify(str(exc), Colors.ERROR)

    def _close_cash(self) -> None:
        try:
            amount = Decimal(self.closing_field.value or "0.00")
            res = self.api.close_cash_session(amount)
            self.on_notify(f"Caja cerrada. Diferencia: ${res['difference']}", Colors.PRIMARY)
            self.on_session_changed()
            self.refresh()
        except Exception as exc:
            self.on_notify(str(exc), Colors.ERROR)

