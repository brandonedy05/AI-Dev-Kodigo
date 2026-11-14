from decimal import Decimal
from pathlib import Path
from typing import Callable, Optional

import flet as ft

from app.services.api_client import POSApiClient, POSApiError
from app.theme import CARD_SHADOW, Colors
from app.views import safe_update


def _kpi_card(title: str, value: str, subtitle: str, icon: ft.IconData, accent: str) -> ft.Control:
    return ft.Container(
        expand=True,
        padding=16,
        bgcolor=Colors.SURFACE,
        border=ft.Border.all(1, Colors.BORDER),
        border_radius=14,
        shadow=CARD_SHADOW,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text(title, size=12, weight=ft.FontWeight.W_600, color=Colors.TEXT_MUTED),
                        ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                        ft.Text(subtitle, size=11, color=Colors.TEXT_SECONDARY),
                    ],
                ),
                ft.Container(
                    width=42,
                    height=42,
                    border_radius=12,
                    bgcolor=Colors.SURFACE_ALT,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(icon, color=accent, size=22),
                ),
            ],
        ),
    )


class ProductsView(ft.Container):
    """Catálogo y gestión de productos basada en diseños 02 y 03."""

    def __init__(self, api: POSApiClient, on_notify: Optional[Callable[[str, str], None]] = None):
        super().__init__(expand=True, padding=20)
        self.api = api
        self.on_notify = on_notify or (lambda m, c: None)

        self.search_field = ft.TextField(
            hint_text="Buscar producto por nombre o SKU...",
            prefix_icon=ft.Icons.SEARCH,
            bgcolor=Colors.SURFACE,
            border_color=Colors.BORDER,
            border_radius=10,
            expand=True,
            on_submit=lambda _: self.refresh(),
        )
        self.table = ft.DataTable(
            heading_row_color=Colors.SURFACE_ALT,
            columns=[
                ft.DataColumn(ft.Text("Imagen", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("SKU", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Producto", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Precio", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Stock", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Estado", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
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
                                ft.Text("Catálogo de Productos", size=24, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                                ft.Text("Administra precios, códigos SKU y existencias en tienda.", size=13, color=Colors.TEXT_MUTED),
                            ],
                        ),
                        ft.Button(
                            content="Nuevo Producto",
                            icon=ft.Icons.ADD,
                            bgcolor=Colors.EMERALD,
                            color=Colors.ON_PRIMARY,
                            height=44,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                            on_click=lambda _: self._open_create_dialog(),
                        ),
                    ],
                ),
                ft.Row(
                    spacing=10,
                    controls=[
                        self.search_field,
                        ft.Button(
                            content="Buscar",
                            bgcolor=Colors.NAVY,
                            color=Colors.ON_PRIMARY,
                            height=46,
                            on_click=lambda _: self.refresh(),
                        ),
                    ],
                ),
                ft.Container(
                    expand=True,
                    padding=12,
                    bgcolor=Colors.SURFACE,
                    border=ft.Border.all(1, Colors.BORDER),
                    border_radius=16,
                    shadow=CARD_SHADOW,
                    content=ft.Column([self.table], scroll=ft.ScrollMode.AUTO, expand=True),
                ),
            ],
        )

    def _open_create_dialog(self) -> None:
        sku_f = ft.TextField(label="SKU *", hint_text="BEB-001")
        name_f = ft.TextField(label="Nombre del producto *")
        price_f = ft.TextField(label="Precio USD *", value="1.00", keyboard_type=ft.KeyboardType.NUMBER)
        stock_f = ft.TextField(label="Stock inicial *", value="10", keyboard_type=ft.KeyboardType.NUMBER)
        uploaded_url: dict[str, Optional[str]] = {"value": None}
        img_status = ft.Text("Sin imagen seleccionada", size=12, color=Colors.TEXT_MUTED)
        img_preview = ft.Container(visible=False)

        file_picker = ft.FilePicker()
        if file_picker not in self.page.services:
            self.page.services.append(file_picker)

        async def pick_image(_: ft.ControlEvent) -> None:
            files = await file_picker.pick_files(
                dialog_title="Seleccionar imagen del producto",
                file_type=ft.FilePickerFileType.IMAGE,
                allow_multiple=False,
                with_data=True,
            )
            if not files:
                return
            picked = files[0]
            raw = picked.bytes
            if raw is None and picked.path:
                raw = Path(picked.path).read_bytes()
            if not raw:
                self.on_notify("No se pudo leer el archivo seleccionado.", Colors.CRIMSON)
                return
            try:
                rel_url = self.api.upload_product_image(picked.name, raw)
                uploaded_url["value"] = rel_url
                img_status.value = f"Imagen lista: {picked.name}"
                img_status.color = Colors.EMERALD_DARK
                img_preview.content = ft.Image(
                    src=self.api.resolve_media_url(rel_url) or rel_url,
                    width=72,
                    height=72,
                    fit=ft.BoxFit.COVER,
                    border_radius=10,
                )
                img_preview.visible = True
                safe_update(dlg)
            except Exception as exc:
                self.on_notify(str(exc), Colors.CRIMSON)

        def save(_: ft.ControlEvent) -> None:
            try:
                self.api.create_product(
                    sku=sku_f.value.strip(),
                    name=name_f.value.strip(),
                    price=Decimal(price_f.value or "0"),
                    stock=int(stock_f.value or "0"),
                    image_url=uploaded_url["value"],
                )
                dlg.open = False
                safe_update(self.page)
                self.on_notify("Producto creado correctamente.", Colors.EMERALD_DARK)
                self.refresh()
            except Exception as exc:
                self.on_notify(str(exc), Colors.CRIMSON)

        dlg = ft.AlertDialog(
            title=ft.Text("Registrar Nuevo Producto", weight=ft.FontWeight.BOLD),
            content=ft.Column(
                tight=True,
                width=420,
                spacing=10,
                controls=[
                    sku_f,
                    name_f,
                    price_f,
                    stock_f,
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Button(
                                content="Subir imagen",
                                icon=ft.Icons.UPLOAD_FILE,
                                bgcolor=Colors.NAVY,
                                color=Colors.ON_PRIMARY,
                                on_click=pick_image,
                            ),
                            img_status,
                        ],
                    ),
                    img_preview,
                ],
            ),
            actions=[
                ft.TextButton(content="Cancelar", on_click=lambda _: self._close_dialog(dlg)),
                ft.Button(content="Guardar", bgcolor=Colors.EMERALD, color=Colors.ON_PRIMARY, on_click=save),
            ],
        )
        self.page.show_dialog(dlg)

    def _close_dialog(self, dlg: ft.AlertDialog) -> None:
        dlg.open = False
        safe_update(self.page)

    def refresh(self) -> None:
        self.table.rows.clear()
        try:
            for p in self.api.get_products(search=self.search_field.value or None):
                stock = int(p["stock"])
                low = stock <= int(p["min_stock"])
                if stock == 0:
                    bg, fg, lbl = Colors.CRIMSON_BG, Colors.CRIMSON_TEXT, "Agotado"
                elif low:
                    bg, fg, lbl = Colors.AMBER_BG, Colors.AMBER_TEXT, "Stock Bajo"
                else:
                    bg, fg, lbl = Colors.EMERALD_SOFT, Colors.EMERALD_DARK, "Disponible"

                img_url = self.api.resolve_media_url(p.get("image_url"))
                fallback_thumb = ft.Container(
                    width=36,
                    height=36,
                    border_radius=8,
                    bgcolor=Colors.SURFACE_ALT,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED, size=18, color=Colors.TEXT_MUTED),
                )
                thumb = (
                    ft.Image(
                        src=img_url,
                        width=36,
                        height=36,
                        fit=ft.BoxFit.COVER,
                        border_radius=8,
                        error_content=fallback_thumb,
                    )
                    if img_url
                    else fallback_thumb
                )

                self.table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(thumb),
                            ft.DataCell(ft.Text(p["sku"], color=Colors.TEXT_MUTED)),
                            ft.DataCell(ft.Text(p["name"], weight=ft.FontWeight.W_600)),
                            ft.DataCell(ft.Text(f"${Decimal(str(p['price'])):.2f}", weight=ft.FontWeight.BOLD, color=Colors.EMERALD_DARK)),
                            ft.DataCell(ft.Text(str(stock))),
                            ft.DataCell(
                                ft.Container(
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                    bgcolor=bg,
                                    border_radius=99,
                                    content=ft.Text(lbl, size=11, weight=ft.FontWeight.BOLD, color=fg),
                                )
                            ),
                        ]
                    )
                )
        except POSApiError:
            pass
        safe_update(self)


_SV_DEPARTMENTS = [
    "San Salvador",
    "La Libertad",
    "Santa Ana",
    "San Miguel",
    "Sonsonate",
    "Usulután",
    "Ahuachapán",
    "La Paz",
    "Cuscatlán",
    "Chalatenango",
    "San Vicente",
    "Cabañas",
    "Morazán",
    "La Unión",
]


class CustomersView(ft.Container):
    """Directorio y registro CRUD de clientes (El Salvador) basado en diseño 04."""

    def __init__(self, api: POSApiClient, on_notify: Optional[Callable[[str, str], None]] = None):
        super().__init__(expand=True, padding=20)
        self.api = api
        self.on_notify = on_notify or (lambda m, c: None)
        self.filter_category: Optional[str] = None

        self.search_field = ft.TextField(
            hint_text="Buscar por Nombre, DUI, NIT o NRC...",
            prefix_icon=ft.Icons.SEARCH,
            bgcolor=Colors.SURFACE,
            border_color=Colors.BORDER,
            border_radius=10,
            expand=True,
            on_submit=lambda _: self.refresh(),
        )
        self.filter_row = ft.Row(spacing=8)
        self.kpi_row = ft.Row(spacing=12)
        self.table = ft.DataTable(
            heading_row_color=Colors.SURFACE_ALT,
            columns=[
                ft.DataColumn(ft.Text("Cliente / Razón Social", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("DUI / NIT / NRC", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Ubicación (El Salvador)", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Clasificación Fiscal", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Contacto", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Límite Crédito", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
            ],
            rows=[],
        )

        self.content = ft.Column(
            expand=True,
            spacing=14,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("Directorio de Clientes", size=24, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                                ft.Text("Registro de clientes y contribuyentes (El Salvador).", size=13, color=Colors.TEXT_MUTED),
                            ],
                        ),
                        ft.Button(
                            content="Nuevo Cliente",
                            icon=ft.Icons.PERSON_ADD,
                            bgcolor=Colors.EMERALD,
                            color=Colors.ON_PRIMARY,
                            height=44,
                            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                            on_click=lambda _: self._open_customer_dialog(),
                        ),
                    ],
                ),
                self.kpi_row,
                ft.Row(
                    spacing=10,
                    controls=[
                        self.search_field,
                        ft.Button(
                            content="Buscar",
                            bgcolor=Colors.NAVY,
                            color=Colors.ON_PRIMARY,
                            height=46,
                            on_click=lambda _: self.refresh(),
                        ),
                    ],
                ),
                self.filter_row,
                ft.Container(
                    expand=True,
                    padding=12,
                    bgcolor=Colors.SURFACE,
                    border=ft.Border.all(1, Colors.BORDER),
                    border_radius=16,
                    shadow=CARD_SHADOW,
                    content=ft.Column([self.table], scroll=ft.ScrollMode.AUTO, expand=True),
                ),
            ],
        )

    def _filter_pill(self, label: str, cat_value: Optional[str]) -> ft.Control:
        selected = self.filter_category == cat_value
        return ft.Container(
            padding=ft.Padding.symmetric(horizontal=14, vertical=7),
            bgcolor=Colors.NAVY if selected else Colors.SURFACE,
            border=ft.Border.all(1, Colors.NAVY if selected else Colors.BORDER),
            border_radius=99,
            on_click=lambda _, v=cat_value: self._set_filter(v),
            content=ft.Text(
                label,
                size=12,
                weight=ft.FontWeight.W_600,
                color=Colors.ON_PRIMARY if selected else Colors.TEXT_SECONDARY,
            ),
        )

    def _set_filter(self, cat_value: Optional[str]) -> None:
        self.filter_category = cat_value
        self.refresh()

    def _open_customer_dialog(self, customer: Optional[dict] = None) -> None:
        is_edit = customer is not None
        data = customer or {}
        selected_cat = {"value": data.get("customer_category", "PERSONAL")}

        country_f = ft.TextField(
            label="País de Emisión *",
            value=data.get("country", "El Salvador"),
            visible=selected_cat["value"] == "FOREIGN",
        )
        doc_type_f = ft.Dropdown(
            label="Tipo de Documento *",
            value=data.get("document_type", "DUI"),
            options=[
                ft.dropdown.Option("DUI", "DUI"),
                ft.dropdown.Option("NIT", "NIT Homologado"),
                ft.dropdown.Option("PASAPORTE", "Pasaporte / Residente"),
                ft.dropdown.Option("CF", "Consumidor Final"),
            ],
        )
        doc_num_f = ft.TextField(
            label="DUI / NIT / Pasaporte",
            hint_text="00000000-0",
            value=data.get("document_number") or "",
        )
        name_f = ft.TextField(
            label="Nombre Completo según Documento *",
            hint_text="Ej: Carlos Roberto Hernández Gómez",
            value=data.get("full_name") or "",
        )

        # Datos Fiscales (Tarjeta de IVA) — visible solo si es Contribuyente (TAXPAYER)
        nrc_f = ft.TextField(label="NRC (Número de Registro) *", hint_text="Ej: 284910-3", value=data.get("nrc") or "")
        business_f = ft.TextField(
            label="Nombre o Razón Social (Tarjeta de IVA) *",
            hint_text="Ej: Distribuidora Cuscatlán S.A. de C.V.",
            value=data.get("business_name") or "",
        )
        activity_f = ft.TextField(
            label="Actividad Económica (Giro según MH)",
            hint_text="47110 - Venta al por menor...",
            value=data.get("economic_activity") or "",
        )
        perception_cb = ft.Checkbox(label="Aplica Percepción 1% (Agente de Percepción)", value=bool(data.get("is_perception_agent", False)))
        retention_cb = ft.Checkbox(label="Aplica Retención 1% (Gran Contribuyente)", value=bool(data.get("is_retention_agent", False)))

        fiscal_section = ft.Container(
            visible=selected_cat["value"] == "TAXPAYER",
            padding=12,
            bgcolor=Colors.CANVAS,
            border=ft.Border.all(1, Colors.BORDER),
            border_radius=12,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text("Datos Fiscales - Tarjeta de IVA (Crédito Fiscal)", size=13, weight=ft.FontWeight.BOLD, color=Colors.EMERALD_DARK),
                    ft.Row(spacing=10, controls=[ft.Container(expand=True, content=nrc_f), ft.Container(expand=True, content=business_f)]),
                    activity_f,
                    perception_cb,
                    retention_cb,
                ],
            ),
        )

        # Ubicación (El Salvador) y Contacto — obligatoria solo para Contribuyente (TAXPAYER)
        is_taxpayer_init = selected_cat["value"] == "TAXPAYER"
        location_title = ft.Text(
            "Ubicación (El Salvador - Obligatoria) & Contacto" if is_taxpayer_init else "Ubicación (Opcional) & Contacto",
            size=13,
            weight=ft.FontWeight.BOLD,
            color=Colors.NAVY,
        )
        dept_f = ft.Dropdown(
            label="Departamento *" if is_taxpayer_init else "Departamento (opcional)",
            value=data.get("department") or ("San Salvador" if is_taxpayer_init else ""),
            options=[ft.dropdown.Option("", "Sin especificar")] + [ft.dropdown.Option(d) for d in _SV_DEPARTMENTS],
        )
        muni_f = ft.TextField(
            label="Municipio *" if is_taxpayer_init else "Municipio (opcional)",
            hint_text="Ej: San Salvador Centro",
            value=data.get("municipality") or "",
        )
        dist_f = ft.TextField(
            label="Distrito *" if is_taxpayer_init else "Distrito (opcional)",
            hint_text="Ej: San Salvador",
            value=data.get("district") or "",
        )
        addr_f = ft.TextField(
            label="Dirección Detallada *" if is_taxpayer_init else "Dirección Detallada (opcional)",
            hint_text="Col., Calle, Pasaje, # Casa o Local",
            value=data.get("address") or "",
        )
        email_f = ft.TextField(
            label="Correo Electrónico",
            hint_text="cliente@correo.com",
            value=data.get("email") or "",
        )
        phone_f = ft.TextField(
            label="Teléfono / WhatsApp",
            hint_text="+503 7000-0000",
            value=data.get("phone") or "",
        )

        # Crédito / Fiado
        credit_limit_f = ft.TextField(
            label="Límite de Crédito / Fiado (USD $)",
            value=str(data.get("credit_limit") or "0.00"),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        credit_days_f = ft.TextField(
            label="Días Plazo para Pago",
            value=str(data.get("credit_days") if data.get("credit_days") is not None else "0"),
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        cat_pills_row = ft.Row(spacing=8)

        def render_cat_pills() -> None:
            cat_pills_row.controls.clear()
            for code, lbl in (
                ("PERSONAL", "Personal / DUI"),
                ("TAXPAYER", "Contribuyente (IVA)"),
                ("FOREIGN", "Extranjero"),
            ):
                active = selected_cat["value"] == code
                cat_pills_row.controls.append(
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.symmetric(vertical=9, horizontal=10),
                        bgcolor=Colors.NAVY if active else Colors.SURFACE_ALT,
                        border=ft.Border.all(1, Colors.NAVY if active else Colors.BORDER),
                        border_radius=10,
                        alignment=ft.Alignment.CENTER,
                        on_click=lambda _, c=code: switch_category(c),
                        content=ft.Text(
                            lbl,
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=Colors.ON_PRIMARY if active else Colors.TEXT_SECONDARY,
                        ),
                    )
                )

        def switch_category(cat_code: str) -> None:
            selected_cat["value"] = cat_code
            is_taxpayer = cat_code == "TAXPAYER"
            fiscal_section.visible = is_taxpayer
            country_f.visible = cat_code == "FOREIGN"
            location_title.value = (
                "Ubicación (El Salvador - Obligatoria) & Contacto"
                if is_taxpayer
                else "Ubicación (Opcional) & Contacto"
            )
            dept_f.label = "Departamento *" if is_taxpayer else "Departamento (opcional)"
            muni_f.label = "Municipio *" if is_taxpayer else "Municipio (opcional)"
            dist_f.label = "Distrito *" if is_taxpayer else "Distrito (opcional)"
            addr_f.label = "Dirección Detallada *" if is_taxpayer else "Dirección Detallada (opcional)"
            if is_taxpayer and not dept_f.value:
                dept_f.value = "San Salvador"
            elif not is_taxpayer and not data.get("department"):
                dept_f.value = ""

            if cat_code == "FOREIGN":
                doc_type_f.value = "PASAPORTE"
                if country_f.value == "El Salvador":
                    country_f.value = ""
            else:
                country_f.value = "El Salvador"
                if doc_type_f.value == "PASAPORTE":
                    doc_type_f.value = "DUI"
            render_cat_pills()
            safe_update(dlg)

        render_cat_pills()

        def save(_: ft.ControlEvent) -> None:
            try:
                is_taxpayer = selected_cat["value"] == "TAXPAYER"
                dept_val = (dept_f.value or "").strip() or None
                muni_val = (muni_f.value or "").strip() or None
                dist_val = (dist_f.value or "").strip() or None
                addr_val = (addr_f.value or "").strip() or None

                if is_taxpayer and not all((dept_val, muni_val, dist_val, addr_val)):
                    self.on_notify(
                        "Para Contribuyentes, Departamento, Municipio, Distrito y Dirección son obligatorios.",
                        Colors.CRIMSON,
                    )
                    return

                payload = {
                    "full_name": (name_f.value or "").strip(),
                    "customer_category": selected_cat["value"],
                    "country": (country_f.value or "El Salvador").strip(),
                    "document_type": doc_type_f.value or "DUI",
                    "document_number": (doc_num_f.value or "").strip() or None,
                    "nrc": (nrc_f.value or "").strip() or None if is_taxpayer else None,
                    "business_name": (business_f.value or "").strip() or None if is_taxpayer else None,
                    "economic_activity": (activity_f.value or "").strip() or None if is_taxpayer else None,
                    "is_perception_agent": bool(perception_cb.value) if is_taxpayer else False,
                    "is_retention_agent": bool(retention_cb.value) if is_taxpayer else False,
                    "department": dept_val,
                    "municipality": muni_val,
                    "district": dist_val,
                    "address": addr_val,
                    "email": (email_f.value or "").strip() or None,
                    "phone": (phone_f.value or "").strip() or None,
                    "credit_limit": str(Decimal(credit_limit_f.value or "0.00")),
                    "credit_days": int(credit_days_f.value or "0"),
                }
                if is_edit:
                    self.api.update_customer(data["id"], payload)
                    msg = "Cliente actualizado correctamente."
                else:
                    self.api.create_customer(payload)
                    msg = "Cliente registrado correctamente."
                dlg.open = False
                safe_update(self.page)
                self.on_notify(msg, Colors.EMERALD_DARK)
                self.refresh()
            except Exception as exc:
                self.on_notify(str(exc), Colors.CRIMSON)

        form_scroll = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            height=460,
            width=540,
            spacing=10,
            controls=[
                ft.Text("Tipo de Cliente", size=12, weight=ft.FontWeight.BOLD, color=Colors.TEXT_MUTED),
                cat_pills_row,
                ft.Divider(height=1, color=Colors.BORDER),
                ft.Text("Información General", size=13, weight=ft.FontWeight.BOLD, color=Colors.NAVY),
                country_f,
                ft.Row(spacing=10, controls=[ft.Container(expand=True, content=doc_type_f), ft.Container(expand=True, content=doc_num_f)]),
                name_f,
                fiscal_section,
                ft.Divider(height=1, color=Colors.BORDER),
                location_title,
                ft.Row(spacing=10, controls=[ft.Container(expand=True, content=dept_f), ft.Container(expand=True, content=muni_f)]),
                ft.Row(spacing=10, controls=[ft.Container(expand=True, content=dist_f), ft.Container(expand=True, content=phone_f)]),
                addr_f,
                email_f,
                ft.Divider(height=1, color=Colors.BORDER),
                ft.Text("Crédito / Fiado", size=13, weight=ft.FontWeight.BOLD, color=Colors.NAVY),
                ft.Row(spacing=10, controls=[ft.Container(expand=True, content=credit_limit_f), ft.Container(expand=True, content=credit_days_f)]),
            ],
        )

        dlg = ft.AlertDialog(
            title=ft.Text("Editar Cliente" if is_edit else "Registrar Nuevo Cliente", weight=ft.FontWeight.BOLD),
            content=form_scroll,
            actions=[
                ft.TextButton(content="Cancelar", on_click=lambda _: self._close_dialog(dlg)),
                ft.Button(content="Guardar Cliente", bgcolor=Colors.EMERALD, color=Colors.ON_PRIMARY, on_click=save),
            ],
        )
        self.page.show_dialog(dlg)

    def _deactivate_customer(self, customer_id: int) -> None:
        try:
            self.api.delete_customer(customer_id)
            self.on_notify("Cliente desactivado.", Colors.AMBER_TEXT)
            self.refresh()
        except POSApiError as exc:
            self.on_notify(exc.detail, Colors.CRIMSON)

    def _close_dialog(self, dlg: ft.AlertDialog) -> None:
        dlg.open = False
        safe_update(self.page)

    def refresh(self) -> None:
        self.table.rows.clear()
        self.kpi_row.controls.clear()
        self.filter_row.controls = [
            self._filter_pill("Todos", None),
            self._filter_pill("Personal / DUI", "PERSONAL"),
            self._filter_pill("Contribuyentes (NRC)", "TAXPAYER"),
            self._filter_pill("Extranjeros", "FOREIGN"),
        ]
        try:
            customers = self.api.get_customers(search=self.search_field.value or None)
            personal_count = sum(1 for c in customers if c.get("customer_category", "PERSONAL") == "PERSONAL")
            taxpayer_count = sum(1 for c in customers if c.get("customer_category") == "TAXPAYER" or c.get("nrc"))
            self.kpi_row.controls.extend(
                [
                    _kpi_card("Total Clientes", str(len(customers)), "Directorio activo", ft.Icons.GROUPS, Colors.NAVY),
                    _kpi_card("Consumidor Final / DUI", str(personal_count), "Con DUI o Pasaporte", ft.Icons.BADGE, Colors.EMERALD_DARK),
                    _kpi_card("Contribuyentes (NRC)", str(taxpayer_count), "Con Tarjeta de IVA", ft.Icons.ACCOUNT_BALANCE, Colors.AMBER_TEXT),
                ]
            )

            filtered = [
                c for c in customers
                if self.filter_category is None or c.get("customer_category", "PERSONAL") == self.filter_category
            ]
            for c in filtered:
                cat = c.get("customer_category", "PERSONAL")
                if cat == "TAXPAYER":
                    cat_bg, cat_fg, cat_lbl = Colors.EMERALD_SOFT, Colors.EMERALD_DARK, "Contribuyente"
                elif cat == "FOREIGN":
                    cat_bg, cat_fg, cat_lbl = Colors.AMBER_BG, Colors.AMBER_TEXT, "Extranjero"
                else:
                    cat_bg, cat_fg, cat_lbl = Colors.SURFACE_ALT, Colors.TEXT_SECONDARY, "Consumidor Final"

                doc_line = f"{c['document_type']}: {c.get('document_number') or 'N/A'}"
                if c.get("nrc"):
                    doc_line += f" | NRC: {c['nrc']}"

                loc_parts = [p for p in (c.get("district"), c.get("municipality"), c.get("department")) if p]
                location_str = ", ".join(loc_parts) if loc_parts else "Sin ubicación"

                contact_parts = [p for p in (c.get("phone"), c.get("email")) if p]
                contact_str = " · ".join(contact_parts) if contact_parts else "Sin contacto"

                limit_dec = Decimal(str(c.get("credit_limit") or "0.00"))

                self.table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(
                                ft.Column(
                                    spacing=1,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        ft.Text(c["full_name"], weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                                        ft.Text(c.get("business_name") or "", size=11, color=Colors.TEXT_MUTED),
                                    ],
                                )
                            ),
                            ft.DataCell(ft.Text(doc_line, size=12)),
                            ft.DataCell(ft.Text(location_str, size=12, color=Colors.TEXT_SECONDARY)),
                            ft.DataCell(
                                ft.Container(
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                    bgcolor=cat_bg,
                                    border_radius=99,
                                    content=ft.Text(cat_lbl, size=11, weight=ft.FontWeight.BOLD, color=cat_fg),
                                )
                            ),
                            ft.DataCell(ft.Text(contact_str, size=12)),
                            ft.DataCell(ft.Text(f"${limit_dec:.2f} ({c.get('credit_days', 0)}d)", size=12, weight=ft.FontWeight.W_600)),
                            ft.DataCell(
                                ft.Row(
                                    spacing=2,
                                    controls=[
                                        ft.IconButton(
                                            ft.Icons.EDIT_OUTLINED,
                                            icon_size=18,
                                            tooltip="Editar cliente",
                                            on_click=lambda _, cust=c: self._open_customer_dialog(cust),
                                        ),
                                        ft.IconButton(
                                            ft.Icons.DELETE_OUTLINE,
                                            icon_size=18,
                                            icon_color=Colors.CRIMSON,
                                            tooltip="Desactivar cliente",
                                            on_click=lambda _, cid=c["id"]: self._deactivate_customer(cid),
                                        ),
                                    ],
                                )
                            ),
                        ]
                    )
                )
        except POSApiError:
            pass
        safe_update(self)


class ReportsView(ft.Container):
    """Vista de reportes de ventas del día y alertas de stock bajo."""

    def __init__(self, api: POSApiClient):
        super().__init__(expand=True, padding=20)
        self.api = api
        self.kpi_row = ft.Row(spacing=12)
        self.low_stock_list = ft.ListView(expand=True, spacing=8)
        self.content = ft.Column(
            expand=True,
            spacing=16,
            controls=[
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text("Reportes del Día", size=24, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                        ft.Text("Resumen operativo de ventas y alertas de reposición.", size=13, color=Colors.TEXT_MUTED),
                    ],
                ),
                self.kpi_row,
                ft.Container(
                    expand=True,
                    padding=16,
                    bgcolor=Colors.SURFACE,
                    border=ft.Border.all(1, Colors.BORDER),
                    border_radius=16,
                    shadow=CARD_SHADOW,
                    content=ft.Column(
                        expand=True,
                        spacing=10,
                        controls=[
                            ft.Text("Alertas de Stock Bajo", size=16, weight=ft.FontWeight.BOLD, color=Colors.AMBER_TEXT),
                            ft.Divider(height=1, color=Colors.BORDER),
                            self.low_stock_list,
                        ],
                    ),
                ),
            ],
        )

    def refresh(self) -> None:
        self.kpi_row.controls.clear()
        self.low_stock_list.controls.clear()
        try:
            summary = self.api.get_sales_summary()
            self.kpi_row.controls.extend(
                [
                    _kpi_card("Ventas Hoy", str(summary["total_transactions"]), "Transacciones completadas", ft.Icons.RECEIPT_LONG, Colors.NAVY),
                    _kpi_card("Ingresos", f"${summary['total_revenue']}", "Total facturado", ft.Icons.TRENDING_UP, Colors.EMERALD_DARK),
                    _kpi_card("Ticket Promedio", f"${summary['average_ticket']}", "Promedio por venta", ft.Icons.ANALYTICS, Colors.AMBER_TEXT),
                ]
            )
            low_items = self.api.get_low_stock()
            if not low_items:
                self.low_stock_list.controls.append(
                    ft.Text("Todo el inventario se encuentra por encima del stock mínimo.", color=Colors.TEXT_MUTED)
                )
            for item in low_items:
                self.low_stock_list.controls.append(
                    ft.Container(
                        padding=10,
                        bgcolor=Colors.AMBER_BG,
                        border_radius=10,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(f"{item['name']} ({item['sku']})", weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                                ft.Text(f"Stock: {item['stock']} / Mín: {item['min_stock']}", weight=ft.FontWeight.BOLD, color=Colors.AMBER_TEXT),
                            ],
                        ),
                    )
                )
        except POSApiError:
            self.kpi_row.controls.append(
                _kpi_card("Sin conexión", "--", "No se pudo consultar /api/v1/reports", ft.Icons.CLOUD_OFF, Colors.CRIMSON)
            )
        safe_update(self)
