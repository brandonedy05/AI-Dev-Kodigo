from datetime import datetime
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
    """Catálogo, Ficha Técnica y CRUD de productos basada en diseños 02 y 03."""

    def __init__(self, api: POSApiClient, on_notify: Optional[Callable[[str, str], None]] = None):
        super().__init__(expand=True, padding=20)
        self.api = api
        self.on_notify = on_notify or (lambda m, c: None)
        self.categories_map: dict[int, str] = {}

        self.search_field = ft.TextField(
            hint_text="Buscar por nombre, SKU o código de barras...",
            prefix_icon=ft.Icons.SEARCH,
            bgcolor=Colors.SURFACE,
            border_color=Colors.BORDER,
            border_radius=10,
            expand=True,
            on_submit=lambda _: self.refresh(),
        )
        self.kpi_row = ft.Row(spacing=12)
        self.table = ft.DataTable(
            heading_row_color=Colors.SURFACE_ALT,
            columns=[
                ft.DataColumn(ft.Text("Imagen", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Producto y Presentación", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("SKU / Código", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Categoría", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Costo", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("P. Venta", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Margen", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Stock", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Ubicación", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
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
                                ft.Text("Catálogo de Productos", size=24, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                                ft.Text("Gestión de inventario, precios, ficha técnica y proveedores.", size=13, color=Colors.TEXT_MUTED),
                            ],
                        ),
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Button(
                                    content="Categorías",
                                    icon=ft.Icons.CATEGORY_OUTLINED,
                                    bgcolor=Colors.NAVY,
                                    color=Colors.ON_PRIMARY,
                                    height=44,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                                    on_click=lambda _: self._open_categories_dialog(),
                                ),
                                ft.Button(
                                    content="Nuevo Producto",
                                    icon=ft.Icons.ADD,
                                    bgcolor=Colors.EMERALD,
                                    color=Colors.ON_PRIMARY,
                                    height=44,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                                    on_click=lambda _: self._open_product_dialog(),
                                ),
                            ],
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

    @staticmethod
    def _calc_margin_pct(cost: Decimal, price: Decimal) -> str:
        if cost <= Decimal("0.00") or price <= Decimal("0.00"):
            return "--"
        margin = ((price - cost) / price) * Decimal("100")
        return f"{margin:.1f}%"

    def _open_categories_dialog(self) -> None:
        editing_id: dict[str, Optional[int]] = {"value": None}
        cat_name_f = ft.TextField(label="Nombre de categoría *", hint_text="Ej: Bebidas", expand=True)
        cat_desc_f = ft.TextField(label="Descripción (opcional)", hint_text="Refrescos, jugos...", expand=True)
        save_btn = ft.Button(
            content="Agregar",
            icon=ft.Icons.ADD,
            bgcolor=Colors.EMERALD,
            color=Colors.ON_PRIMARY,
            height=46,
        )
        cat_list = ft.ListView(height=240, spacing=8)

        def reset_form() -> None:
            editing_id["value"] = None
            cat_name_f.value = ""
            cat_desc_f.value = ""
            save_btn.content = "Agregar"
            save_btn.icon = ft.Icons.ADD

        def load_list() -> None:
            cat_list.controls.clear()
            try:
                cats = self.api.get_categories()
                self.categories_map = {c["id"]: c["name"] for c in cats}
                if not cats:
                    cat_list.controls.append(ft.Text("No hay categorías registradas.", color=Colors.TEXT_MUTED))
                for c in cats:
                    cat_list.controls.append(
                        ft.Container(
                            padding=10,
                            bgcolor=Colors.CANVAS,
                            border=ft.Border.all(1, Colors.BORDER),
                            border_radius=10,
                            content=ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Column(
                                        spacing=2,
                                        expand=True,
                                        controls=[
                                            ft.Text(c["name"], weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                                            ft.Text(c.get("description") or "Sin descripción", size=12, color=Colors.TEXT_MUTED),
                                        ],
                                    ),
                                    ft.Row(
                                        spacing=0,
                                        controls=[
                                            ft.IconButton(
                                                ft.Icons.EDIT_OUTLINED,
                                                icon_size=18,
                                                tooltip="Editar categoría",
                                                on_click=lambda _, cat=c: start_edit(cat),
                                            ),
                                            ft.IconButton(
                                                ft.Icons.DELETE_OUTLINE,
                                                icon_size=18,
                                                icon_color=Colors.CRIMSON,
                                                tooltip="Desactivar categoría",
                                                on_click=lambda _, cid=c["id"]: remove_cat(cid),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        )
                    )
            except POSApiError as exc:
                self.on_notify(exc.detail, Colors.CRIMSON)
            safe_update(dlg)

        def start_edit(cat: dict) -> None:
            editing_id["value"] = cat["id"]
            cat_name_f.value = cat["name"]
            cat_desc_f.value = cat.get("description") or ""
            save_btn.content = "Guardar"
            save_btn.icon = ft.Icons.CHECK
            safe_update(dlg)

        def save_cat(_: ft.ControlEvent) -> None:
            name = (cat_name_f.value or "").strip()
            desc = (cat_desc_f.value or "").strip() or None
            if len(name) < 2:
                self.on_notify("Ingresa un nombre de al menos 2 caracteres.", Colors.CRIMSON)
                return
            try:
                if editing_id["value"] is not None:
                    self.api.update_category(editing_id["value"], {"name": name, "description": desc})
                    self.on_notify("Categoría actualizada.", Colors.EMERALD_DARK)
                else:
                    self.api.create_category(name=name, description=desc)
                    self.on_notify("Categoría creada.", Colors.EMERALD_DARK)
                reset_form()
                load_list()
                self.refresh()
            except POSApiError as exc:
                self.on_notify(exc.detail, Colors.CRIMSON)

        def remove_cat(cid: int) -> None:
            try:
                self.api.delete_category(cid)
                if editing_id["value"] == cid:
                    reset_form()
                self.on_notify("Categoría desactivada.", Colors.AMBER_TEXT)
                load_list()
                self.refresh()
            except POSApiError as exc:
                self.on_notify(exc.detail, Colors.CRIMSON)

        save_btn.on_click = save_cat

        dlg = ft.AlertDialog(
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.CATEGORY, color=Colors.EMERALD_DARK),
                    ft.Text("Gestión de Categorías", weight=ft.FontWeight.BOLD),
                ],
            ),
            content=ft.Column(
                tight=True,
                width=480,
                spacing=12,
                controls=[
                    ft.Row(spacing=8, controls=[cat_name_f, cat_desc_f]),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        controls=[
                            ft.TextButton(content="Limpiar", on_click=lambda _: (reset_form(), safe_update(dlg))),
                            save_btn,
                        ],
                    ),
                    ft.Divider(height=1, color=Colors.BORDER),
                    cat_list,
                ],
            ),
            actions=[
                ft.Button(content="Cerrar", bgcolor=Colors.NAVY, color=Colors.ON_PRIMARY, on_click=lambda _: self._close_dialog(dlg)),
            ],
        )
        self.page.show_dialog(dlg)
        load_list()

    def _open_tech_sheet_dialog(self, p: dict) -> None:
        img_url = self.api.resolve_media_url(p.get("image_url"))
        fallback_img = ft.Container(
            width=140,
            height=140,
            bgcolor=Colors.CANVAS,
            border=ft.Border.all(1, Colors.BORDER),
            border_radius=14,
            alignment=ft.Alignment.CENTER,
            content=ft.Icon(ft.Icons.INVENTORY_2_OUTLINED, size=44, color=Colors.EMERALD),
        )
        visual = (
            ft.Container(
                width=140,
                height=140,
                bgcolor=Colors.SURFACE,
                border=ft.Border.all(1, Colors.BORDER),
                border_radius=14,
                padding=6,
                content=ft.Image(src=img_url, fit=ft.BoxFit.CONTAIN, error_content=fallback_img),
            )
            if img_url
            else fallback_img
        )

        price_dec = Decimal(str(p.get("price") or "0.00"))
        cost_dec = Decimal(str(p.get("cost_price") or "0.00"))
        wholesale = p.get("wholesale_price")
        margin_txt = self._calc_margin_pct(cost_dec, price_dec)
        cat_name = self.categories_map.get(p.get("category_id"), "Sin categoría")

        def close_and_edit(_: ft.ControlEvent) -> None:
            self._close_dialog(dlg)
            self._open_product_dialog(p)

        def close_and_delete(_: ft.ControlEvent) -> None:
            self._close_dialog(dlg)
            self._confirm_soft_delete(p)

        def spec_row(lbl: str, val: str) -> ft.Control:
            return ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(lbl, size=12, color=Colors.TEXT_MUTED),
                    ft.Text(val, size=12, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                ],
            )

        body = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            height=430,
            width=520,
            spacing=12,
            controls=[
                ft.Row(
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        visual,
                        ft.Column(
                            expand=True,
                            spacing=4,
                            controls=[
                                ft.Text(p["name"], size=18, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                                ft.Text(f"SKU: {p['sku']}  ·  Barras: {p.get('barcode') or 'N/A'}", size=12, color=Colors.TEXT_MUTED),
                                ft.Text(f"Categoría: {cat_name}  ·  Unidad: {p.get('unit_of_measure', 'Unidad')}", size=12, color=Colors.EMERALD_DARK, weight=ft.FontWeight.W_600),
                                ft.Text(p.get("description") or "Sin descripción adicional.", size=12, color=Colors.TEXT_SECONDARY),
                            ],
                        ),
                    ],
                ),
                ft.Divider(height=1, color=Colors.BORDER),
                ft.Text("Estructura de Precios & IVA", size=13, weight=ft.FontWeight.BOLD, color=Colors.NAVY),
                ft.Container(
                    padding=12,
                    bgcolor=Colors.CANVAS,
                    border=ft.Border.all(1, Colors.BORDER),
                    border_radius=10,
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            spec_row("Precio de Venta", f"${price_dec:.2f}"),
                            spec_row("Costo Neto Compra", f"${cost_dec:.2f}"),
                            spec_row("Margen Estimado", margin_txt),
                            spec_row("Precio Mayoreo", f"${Decimal(str(wholesale)):.2f}" if wholesale else "No definido"),
                            spec_row("Aplica IVA 13%", "Sí" if p.get("applies_iva", True) else "Exento"),
                        ],
                    ),
                ),
                ft.Text("Inventario, Ubicación & Proveedor", size=13, weight=ft.FontWeight.BOLD, color=Colors.NAVY),
                ft.Container(
                    padding=12,
                    bgcolor=Colors.CANVAS,
                    border=ft.Border.all(1, Colors.BORDER),
                    border_radius=10,
                    content=ft.Column(
                        spacing=6,
                        controls=[
                            spec_row("Stock Actual", f"{p['stock']} uds"),
                            spec_row("Stock Mínimo (Alerta)", f"{p['min_stock']} uds"),
                            spec_row("Ubicación / Pasillo", p.get("location") or "No asignada"),
                            spec_row("Proveedor Principal", p.get("supplier_name") or "No especificado"),
                            spec_row("Código Ref. Proveedor", p.get("supplier_code") or "N/A"),
                        ],
                    ),
                ),
            ],
        )

        dlg = ft.AlertDialog(
            title=ft.Row(
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, color=Colors.EMERALD_DARK),
                    ft.Text("Ficha Técnica del Producto", weight=ft.FontWeight.BOLD),
                ],
            ),
            content=body,
            actions=[
                ft.TextButton(content="Cerrar", on_click=lambda _: self._close_dialog(dlg)),
                ft.Button(content="Desactivar", icon=ft.Icons.DELETE_OUTLINE, bgcolor=Colors.CRIMSON_BG, color=Colors.CRIMSON_TEXT, on_click=close_and_delete),
                ft.Button(content="Editar", icon=ft.Icons.EDIT, bgcolor=Colors.NAVY, color=Colors.ON_PRIMARY, on_click=close_and_edit),
            ],
        )
        self.page.show_dialog(dlg)

    def _open_product_dialog(self, product: Optional[dict] = None) -> None:
        is_edit = product is not None
        data = product or {}

        sku_f = ft.TextField(label="SKU *", hint_text="BEB-001", value=data.get("sku") or "")
        barcode_f = ft.TextField(label="Código de Barras (EAN-13 / UPC)", value=data.get("barcode") or "")
        name_f = ft.TextField(label="Nombre Comercial & Presentación *", value=data.get("name") or "")
        desc_f = ft.TextField(label="Descripción", value=data.get("description") or "")

        cat_options = [ft.dropdown.Option("", "Sin categoría")] + [
            ft.dropdown.Option(str(cid), cname) for cid, cname in self.categories_map.items()
        ]
        cat_f = ft.Dropdown(
            label="Categoría",
            value=str(data["category_id"]) if data.get("category_id") else "",
            options=cat_options,
        )
        unit_f = ft.Dropdown(
            label="Unidad de Medida *",
            value=data.get("unit_of_measure") or "Unidad",
            options=[
                ft.dropdown.Option("Unidad"),
                ft.dropdown.Option("Litro"),
                ft.dropdown.Option("Kilogramo"),
                ft.dropdown.Option("Libra"),
                ft.dropdown.Option("Paquete"),
                ft.dropdown.Option("Caja"),
            ],
        )

        price_f = ft.TextField(label="Precio Venta (USD) *", value=str(data.get("price") or "1.00"), keyboard_type=ft.KeyboardType.NUMBER)
        cost_f = ft.TextField(label="Costo Compra Neto (USD)", value=str(data.get("cost_price") or "0.00"), keyboard_type=ft.KeyboardType.NUMBER)
        wholesale_f = ft.TextField(
            label="Precio Mayoreo (Opcional)",
            value=str(data["wholesale_price"]) if data.get("wholesale_price") is not None else "",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        iva_cb = ft.Checkbox(label="Aplica IVA 13% (El Salvador)", value=bool(data.get("applies_iva", True)))

        stock_f = ft.TextField(label="Stock Actual *", value=str(data.get("stock") if data.get("stock") is not None else "10"), keyboard_type=ft.KeyboardType.NUMBER)
        min_stock_f = ft.TextField(label="Stock Mínimo (Alerta) *", value=str(data.get("min_stock") if data.get("min_stock") is not None else "5"), keyboard_type=ft.KeyboardType.NUMBER)
        location_f = ft.TextField(label="Ubicación / Pasillo", hint_text="Ej: Pasillo 2 - Abarrotes", value=data.get("location") or "")
        supplier_f = ft.TextField(label="Proveedor Principal", value=data.get("supplier_name") or "")
        supplier_code_f = ft.TextField(label="Código Ref. Proveedor", value=data.get("supplier_code") or "")

        uploaded_url: dict[str, Optional[str]] = {"value": data.get("image_url")}
        existing_resolved = self.api.resolve_media_url(data.get("image_url"))
        img_status = ft.Text(
            "Imagen actual cargada" if existing_resolved else "Sin imagen seleccionada",
            size=12,
            color=Colors.EMERALD_DARK if existing_resolved else Colors.TEXT_MUTED,
        )
        img_preview = ft.Container(
            visible=bool(existing_resolved),
            content=(
                ft.Image(src=existing_resolved, width=72, height=72, fit=ft.BoxFit.COVER, border_radius=10)
                if existing_resolved
                else None
            ),
        )

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
                cat_val = (cat_f.value or "").strip()
                wholesale_val = (wholesale_f.value or "").strip()
                payload = {
                    "sku": (sku_f.value or "").strip(),
                    "barcode": (barcode_f.value or "").strip() or None,
                    "name": (name_f.value or "").strip(),
                    "description": (desc_f.value or "").strip() or None,
                    "image_url": uploaded_url["value"],
                    "unit_of_measure": unit_f.value or "Unidad",
                    "price": str(Decimal(price_f.value or "0.00")),
                    "cost_price": str(Decimal(cost_f.value or "0.00")),
                    "wholesale_price": str(Decimal(wholesale_val)) if wholesale_val else None,
                    "applies_iva": bool(iva_cb.value),
                    "stock": int(stock_f.value or "0"),
                    "min_stock": int(min_stock_f.value or "0"),
                    "location": (location_f.value or "").strip() or None,
                    "supplier_name": (supplier_f.value or "").strip() or None,
                    "supplier_code": (supplier_code_f.value or "").strip() or None,
                    "category_id": int(cat_val) if cat_val else None,
                }
                if is_edit:
                    self.api.update_product(data["id"], payload)
                    msg = "Producto actualizado correctamente."
                else:
                    self.api.create_product(payload)
                    msg = "Producto creado correctamente."
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
                ft.Text("1. Datos Generales del Artículo", size=13, weight=ft.FontWeight.BOLD, color=Colors.NAVY),
                name_f,
                ft.Row(spacing=10, controls=[ft.Container(expand=True, content=sku_f), ft.Container(expand=True, content=barcode_f)]),
                ft.Row(spacing=10, controls=[ft.Container(expand=True, content=cat_f), ft.Container(expand=True, content=unit_f)]),
                desc_f,
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
                ft.Divider(height=1, color=Colors.BORDER),
                ft.Text("2. Estructura de Precios & IVA (13% El Salvador)", size=13, weight=ft.FontWeight.BOLD, color=Colors.NAVY),
                ft.Row(spacing=10, controls=[ft.Container(expand=True, content=cost_f), ft.Container(expand=True, content=price_f)]),
                wholesale_f,
                iva_cb,
                ft.Divider(height=1, color=Colors.BORDER),
                ft.Text("3. Inventario & Ubicación", size=13, weight=ft.FontWeight.BOLD, color=Colors.NAVY),
                ft.Row(spacing=10, controls=[ft.Container(expand=True, content=stock_f), ft.Container(expand=True, content=min_stock_f)]),
                location_f,
                ft.Divider(height=1, color=Colors.BORDER),
                ft.Text("4. Datos de Proveedor", size=13, weight=ft.FontWeight.BOLD, color=Colors.NAVY),
                ft.Row(spacing=10, controls=[ft.Container(expand=True, content=supplier_f), ft.Container(expand=True, content=supplier_code_f)]),
            ],
        )

        dlg = ft.AlertDialog(
            title=ft.Text("Editar Producto" if is_edit else "Registrar Nuevo Producto", weight=ft.FontWeight.BOLD),
            content=form_scroll,
            actions=[
                ft.TextButton(content="Cancelar", on_click=lambda _: self._close_dialog(dlg)),
                ft.Button(content="Guardar Producto", bgcolor=Colors.EMERALD, color=Colors.ON_PRIMARY, on_click=save),
            ],
        )
        self.page.show_dialog(dlg)

    def _confirm_soft_delete(self, product: dict) -> None:
        def confirm(_: ft.ControlEvent) -> None:
            try:
                self.api.delete_product(product["id"])
                dlg.open = False
                safe_update(self.page)
                self.on_notify(f"Producto '{product['name']}' desactivado (soft delete).", Colors.AMBER_TEXT)
                self.refresh()
            except POSApiError as exc:
                self.on_notify(exc.detail, Colors.CRIMSON)

        dlg = ft.AlertDialog(
            title=ft.Text("Desactivar Producto", weight=ft.FontWeight.BOLD),
            content=ft.Text(
                f"¿Seguro que deseas desactivar '{product['name']}'?\n"
                "Se ocultará del catálogo y del terminal POS, pero se conservará su historial de ventas."
            ),
            actions=[
                ft.TextButton(content="Cancelar", on_click=lambda _: self._close_dialog(dlg)),
                ft.Button(content="Sí, desactivar", bgcolor=Colors.CRIMSON, color=Colors.ON_PRIMARY, on_click=confirm),
            ],
        )
        self.page.show_dialog(dlg)

    def _close_dialog(self, dlg: ft.AlertDialog) -> None:
        dlg.open = False
        safe_update(self.page)

    def refresh(self) -> None:
        self.table.rows.clear()
        self.kpi_row.controls.clear()
        try:
            self.categories_map = {c["id"]: c["name"] for c in self.api.get_categories()}
            products = self.api.get_products(search=self.search_field.value or None)

            low_count = sum(1 for p in products if int(p["stock"]) <= int(p["min_stock"]))
            inv_cost = sum(
                (Decimal(str(p.get("cost_price") or "0.00")) * int(p["stock"]) for p in products),
                Decimal("0.00"),
            )
            self.kpi_row.controls.extend(
                [
                    _kpi_card("Productos Activos", str(len(products)), "En catálogo vigente", ft.Icons.INVENTORY_2, Colors.NAVY),
                    _kpi_card("Stock Bajo / Crítico", str(low_count), "Requieren reposición", ft.Icons.WARNING_AMBER, Colors.AMBER_TEXT),
                    _kpi_card("Valor en Inventario", f"${inv_cost:.2f}", "Calculado a costo neto", ft.Icons.ATTACH_MONEY, Colors.EMERALD_DARK),
                ]
            )

            for p in products:
                stock = int(p["stock"])
                low = stock <= int(p["min_stock"])
                if stock == 0:
                    bg, fg, lbl = Colors.CRIMSON_BG, Colors.CRIMSON_TEXT, f"{stock} · Agotado"
                elif low:
                    bg, fg, lbl = Colors.AMBER_BG, Colors.AMBER_TEXT, f"{stock} · Bajo"
                else:
                    bg, fg, lbl = Colors.EMERALD_SOFT, Colors.EMERALD_DARK, f"{stock} uds"

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

                price_dec = Decimal(str(p.get("price") or "0.00"))
                cost_dec = Decimal(str(p.get("cost_price") or "0.00"))
                margin_txt = self._calc_margin_pct(cost_dec, price_dec)
                cat_name = self.categories_map.get(p.get("category_id"), "Sin categoría")

                self.table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(thumb),
                            ft.DataCell(
                                ft.Column(
                                    spacing=1,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    controls=[
                                        ft.Text(p["name"], weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                                        ft.Text(p.get("unit_of_measure", "Unidad"), size=11, color=Colors.TEXT_MUTED),
                                    ],
                                )
                            ),
                            ft.DataCell(ft.Text(p["sku"], color=Colors.TEXT_MUTED, size=12)),
                            ft.DataCell(ft.Text(cat_name, size=12)),
                            ft.DataCell(ft.Text(f"${cost_dec:.2f}", size=12, color=Colors.TEXT_SECONDARY)),
                            ft.DataCell(ft.Text(f"${price_dec:.2f}", weight=ft.FontWeight.BOLD, color=Colors.EMERALD_DARK)),
                            ft.DataCell(ft.Text(margin_txt, size=12, color=Colors.TEXT_SECONDARY)),
                            ft.DataCell(
                                ft.Container(
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                                    bgcolor=bg,
                                    border_radius=99,
                                    content=ft.Text(lbl, size=11, weight=ft.FontWeight.BOLD, color=fg),
                                )
                            ),
                            ft.DataCell(ft.Text(p.get("location") or "—", size=12, color=Colors.TEXT_MUTED)),
                            ft.DataCell(
                                ft.Row(
                                    spacing=0,
                                    controls=[
                                        ft.IconButton(
                                            ft.Icons.VISIBILITY_OUTLINED,
                                            icon_size=18,
                                            tooltip="Ver ficha técnica",
                                            on_click=lambda _, prod=p: self._open_tech_sheet_dialog(prod),
                                        ),
                                        ft.IconButton(
                                            ft.Icons.EDIT_OUTLINED,
                                            icon_size=18,
                                            tooltip="Editar producto",
                                            on_click=lambda _, prod=p: self._open_product_dialog(prod),
                                        ),
                                        ft.IconButton(
                                            ft.Icons.DELETE_OUTLINE,
                                            icon_size=18,
                                            icon_color=Colors.CRIMSON,
                                            tooltip="Desactivar (soft delete)",
                                            on_click=lambda _, prod=p: self._confirm_soft_delete(prod),
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
        self.sales_count_badge = ft.Text("0 ventas hoy", size=12, color=Colors.TEXT_MUTED)
        self.sales_empty_msg = ft.Text(
            "No hay ventas registradas hoy.",
            color=Colors.TEXT_MUTED,
            visible=False,
        )
        self.sales_table = ft.DataTable(
            heading_row_color=Colors.SURFACE_ALT,
            column_spacing=18,
            columns=[
                ft.DataColumn(ft.Text("Ticket", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Fecha y Hora", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Artículos", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Método de Pago", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Total", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
                ft.DataColumn(ft.Text("Detalle", weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY)),
            ],
            rows=[],
        )
        self.low_stock_list = ft.ListView(expand=True, spacing=8)
        self.content = ft.Column(
            expand=True,
            spacing=16,
            controls=[
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text("Reportes del Día", size=24, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                        ft.Text("Resumen operativo de ventas de hoy y alertas de reposición.", size=13, color=Colors.TEXT_MUTED),
                    ],
                ),
                self.kpi_row,
                ft.Row(
                    expand=True,
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        ft.Container(
                            expand=65,
                            padding=16,
                            bgcolor=Colors.SURFACE,
                            border=ft.Border.all(1, Colors.BORDER),
                            border_radius=16,
                            shadow=CARD_SHADOW,
                            content=ft.Column(
                                expand=True,
                                spacing=10,
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.Text(
                                                "Listado de Ventas de Hoy",
                                                size=16,
                                                weight=ft.FontWeight.BOLD,
                                                color=Colors.TEXT_PRIMARY,
                                            ),
                                            self.sales_count_badge,
                                        ],
                                    ),
                                    ft.Divider(height=1, color=Colors.BORDER),
                                    self.sales_empty_msg,
                                    ft.Column(
                                        expand=True,
                                        scroll=ft.ScrollMode.AUTO,
                                        controls=[
                                            ft.Row(
                                                scroll=ft.ScrollMode.AUTO,
                                                controls=[self.sales_table],
                                            )
                                        ],
                                    ),
                                ],
                            ),
                        ),
                        ft.Container(
                            expand=35,
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
                ),
            ],
        )

    @staticmethod
    def _parse_sale_datetime(created_raw: object) -> Optional[datetime]:
        if not created_raw:
            return None
        raw_str = str(created_raw).strip()
        if not raw_str:
            return None
        try:
            dt = datetime.fromisoformat(raw_str.replace("Z", "+00:00"))
            if dt.tzinfo is not None:
                dt = dt.astimezone()
            return dt
        except ValueError:
            return None

    @classmethod
    def _format_sale_datetime(cls, created_raw: object) -> str:
        dt = cls._parse_sale_datetime(created_raw)
        if dt is not None:
            return dt.strftime("%d/%m/%Y %H:%M")
        raw_str = str(created_raw or "").strip()
        if len(raw_str) >= 16:
            return f"{raw_str[:10]} {raw_str[11:16]}"
        return "--/--/---- --:--"

    def _open_sale_detail(self, sale: dict) -> None:
        if not self.page:
            return
        method = sale.get("payment_method", "CASH")
        method_lbl = "Efectivo" if method == "CASH" else ("Tarjeta" if method == "CARD" else str(method))
        card_info: list[ft.Control] = []
        if method == "CARD":
            bank = sale.get("card_bank") or "-"
            ctype = sale.get("card_type") or "-"
            auth = sale.get("card_auth_number") or "-"
            card_info.append(
                ft.Text(
                    f"Tarjeta: {ctype} | Banco: {bank} | Autorización: {auth}",
                    size=12,
                    color=Colors.TEXT_MUTED,
                )
            )

        items = sale.get("items", [])
        units_count = sum(int(it.get("quantity", 0)) for it in items)
        item_rows: list[ft.Control] = []
        for it in items:
            item_rows.append(
                ft.Container(
                    padding=ft.Padding.symmetric(vertical=6, horizontal=8),
                    bgcolor=Colors.SURFACE_ALT,
                    border_radius=8,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=1,
                                expand=True,
                                controls=[
                                    ft.Text(
                                        str(it.get("product_name", "Producto")),
                                        size=13,
                                        weight=ft.FontWeight.W_600,
                                        color=Colors.TEXT_PRIMARY,
                                    ),
                                    ft.Text(
                                        f"{it.get('quantity', 0)} x ${it.get('unit_price', '0.00')}",
                                        size=11,
                                        color=Colors.TEXT_MUTED,
                                    ),
                                ],
                            ),
                            ft.Text(
                                f"${it.get('line_total', '0.00')}",
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color=Colors.TEXT_PRIMARY,
                            ),
                        ],
                    ),
                )
            )

        discount_val = Decimal(str(sale.get("discount", "0.00")))
        summary_controls: list[ft.Control] = [
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("Subtotal", size=12, color=Colors.TEXT_MUTED),
                    ft.Text(f"${sale.get('subtotal', '0.00')}", size=12, color=Colors.TEXT_PRIMARY),
                ],
            ),
        ]
        if discount_val > Decimal("0"):
            summary_controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Descuento", size=12, color=Colors.TEXT_MUTED),
                        ft.Text(f"-${sale.get('discount', '0.00')}", size=12, color=Colors.CRIMSON),
                    ],
                )
            )
        summary_controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("Total", size=14, weight=ft.FontWeight.BOLD, color=Colors.TEXT_PRIMARY),
                    ft.Text(f"${sale.get('total', '0.00')}", size=15, weight=ft.FontWeight.BOLD, color=Colors.EMERALD_DARK),
                ],
            )
        )
        if method == "CASH":
            summary_controls.append(
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Recibido / Cambio", size=12, color=Colors.TEXT_MUTED),
                        ft.Text(
                            f"${sale.get('amount_paid', '0.00')} / ${sale.get('change_amount', '0.00')}",
                            size=12,
                            color=Colors.TEXT_PRIMARY,
                        ),
                    ],
                )
            )

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Detalle de Venta - {sale.get('ticket_number', '')}", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                width=440,
                content=ft.Column(
                    tight=True,
                    spacing=8,
                    controls=[
                        ft.Text(
                            f"Fecha y hora: {self._format_sale_datetime(sale.get('created_at'))}",
                            size=12,
                            color=Colors.TEXT_MUTED,
                        ),
                        ft.Text(
                            f"Método de pago: {method_lbl} | Artículos: {units_count}",
                            size=12,
                            color=Colors.TEXT_MUTED,
                        ),
                        *card_info,
                        ft.Divider(height=1, color=Colors.BORDER),
                        ft.Text("Artículos vendidos", size=13, weight=ft.FontWeight.W_600, color=Colors.TEXT_PRIMARY),
                        ft.Container(
                            height=180 if len(item_rows) > 3 else None,
                            content=ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, controls=item_rows),
                        ),
                        ft.Divider(height=1, color=Colors.BORDER),
                        *summary_controls,
                    ],
                ),
            ),
            actions=[
                ft.Button(
                    content=ft.Text("Cerrar"),
                    on_click=lambda _: self.page.pop_dialog(),
                ),
            ],
        )
        self.page.show_dialog(dlg)

    def refresh(self) -> None:
        self.kpi_row.controls.clear()
        self.sales_table.rows.clear()
        self.low_stock_list.controls.clear()
        self.sales_empty_msg.visible = False
        try:
            summary = self.api.get_sales_summary()
            self.kpi_row.controls.extend(
                [
                    _kpi_card("Ventas Hoy", str(summary["total_transactions"]), "Transacciones completadas", ft.Icons.RECEIPT_LONG, Colors.NAVY),
                    _kpi_card("Ingresos", f"${summary['total_revenue']}", "Total facturado", ft.Icons.TRENDING_UP, Colors.EMERALD_DARK),
                    _kpi_card("Ticket Promedio", f"${summary['average_ticket']}", "Promedio por venta", ft.Icons.ANALYTICS, Colors.AMBER_TEXT),
                ]
            )

            all_sales = self.api.get_sales(limit=100)
            today_date = datetime.now().date()
            today_sales = []
            for s in all_sales:
                dt = self._parse_sale_datetime(s.get("created_at"))
                if dt is None or dt.date() == today_date:
                    today_sales.append(s)

            self.sales_count_badge.value = f"{len(today_sales)} venta(s) hoy"
            if not today_sales:
                self.sales_empty_msg.visible = True
            for s in today_sales:
                items = s.get("items", [])
                units_count = sum(int(it.get("quantity", 0)) for it in items)
                datetime_str = self._format_sale_datetime(s.get("created_at"))
                method = s.get("payment_method", "CASH")
                method_lbl = "Efectivo" if method == "CASH" else ("Tarjeta" if method == "CARD" else str(method))
                method_bg = Colors.EMERALD_SOFT if method == "CASH" else Colors.SURFACE_ALT
                method_fg = Colors.EMERALD_DARK if method == "CASH" else Colors.NAVY

                self.sales_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(s["ticket_number"], weight=ft.FontWeight.W_600, size=12)),
                            ft.DataCell(ft.Text(datetime_str, size=12, color=Colors.TEXT_MUTED)),
                            ft.DataCell(ft.Text(f"{units_count} art.", size=12, color=Colors.TEXT_PRIMARY)),
                            ft.DataCell(
                                ft.Container(
                                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                                    bgcolor=method_bg,
                                    border_radius=8,
                                    content=ft.Text(method_lbl, size=11, weight=ft.FontWeight.W_600, color=method_fg),
                                )
                            ),
                            ft.DataCell(ft.Text(f"${s['total']}", weight=ft.FontWeight.BOLD, size=12, color=Colors.TEXT_PRIMARY)),
                            ft.DataCell(
                                ft.IconButton(
                                    ft.Icons.VISIBILITY_OUTLINED,
                                    icon_size=18,
                                    icon_color=Colors.NAVY,
                                    tooltip="Ver detalle de venta",
                                    on_click=lambda _, sale=s: self._open_sale_detail(sale),
                                )
                            ),
                        ]
                    )
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
