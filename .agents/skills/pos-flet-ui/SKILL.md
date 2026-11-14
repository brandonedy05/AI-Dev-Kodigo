---
name: pos-flet-ui
description: >-
  Guía operativa para diseñar, crear o modificar vistas y componentes de interfaz en
  Flet 1.1.2 dentro de frontend/ del POS "Mi Tiendita Fácil". Activar siempre que se
  editen pantallas en frontend/app/views/, se creen modales o formularios, se apliquen
  tokens visuales de Stitch o se depuren errores de renderizado en Flet.
---

# Guía de Interfaz Flet 1.1.2 y Diseño Stitch (`pos-flet-ui`)

Procedimiento estándar para mantener consistencia visual, compatibilidad con Flet `1.1.2`
y estabilidad de renderizado en `frontend/app/`.

## Cuándo usar esta skill

- Al crear o modificar vistas en `frontend/app/views/` (`pos_terminal_view.py`, `secondary_views.py`, etc.).
- Al agregar diálogos (`AlertDialog`), tablas (`DataTable`), tarjetas de producto o formularios.
- Al corregir errores de atributos deprecados o incompatibles con Flet `1.1.2`.

## 1. Tokens visuales obligatorios (`frontend/app/theme.py`)

Importar siempre `Colors`, `CARD_SHADOW` y `FONT_FAMILY` desde `app.theme` en lugar de usar colores hexadecimales sueltos:

- **Superficies y bordes:** `Colors.CANVAS` (`#F8FAFC`), `Colors.SURFACE` (`#FFFFFF`), `Colors.SURFACE_ALT` (`#F1F5F9`), `Colors.BORDER` (`#E2E8F0`), `Colors.BORDER_STRONG` (`#CBD5E1`).
- **Texto:** `Colors.TEXT_PRIMARY` (`#0F172A`), `Colors.TEXT_SECONDARY` (`#475569`), `Colors.TEXT_MUTED` (`#64748B`).
- **Marca y estados:** `Colors.NAVY` (`#0F172A`), `Colors.EMERALD` (`#10B981`), `Colors.EMERALD_DARK` (`#059669`), `Colors.EMERALD_SOFT` (`#ECFDF5`), `Colors.AMBER_BG` / `Colors.AMBER_TEXT`, `Colors.CRIMSON` / `Colors.CRIMSON_BG`.
- **Tarjetas:** `bgcolor=Colors.SURFACE`, `border=ft.Border.all(1, Colors.BORDER)`, `border_radius=14` o `16`, `shadow=CARD_SHADOW`.

## 2. Reglas de compatibilidad con Flet `1.1.2`

1. **Botones:** Usar `ft.Button(content=ft.Text("..."), on_click=...)` en lugar de `ElevatedButton` o argumentos antiguos.
2. **Bordes y relleno:** Usar `ft.Border.all(1, Colors.BORDER)` y `ft.Padding.symmetric(horizontal=..., vertical=...)` (mayúscula inicial en `Border` y `Padding`).
3. **Diálogos modales:** Abrir con `self.page.show_dialog(dlg)` y cerrar con `self.page.pop_dialog()`, validando antes `if not self.page: return`.
4. **Actualización segura:** Usar `safe_update(control)` importado de `app.views` en lugar de `self.update()` directo, para evitar excepciones cuando el control aún no está montado en `page`.
5. **Tablas responsivas:** Envolver `ft.DataTable` dentro de un `ft.Row(scroll=ft.ScrollMode.AUTO, controls=[table])` y este a su vez en un `ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, ...)` para evitar desbordamientos horizontales o verticales.

## 3. Verificación obligatoria

Después de cualquier cambio en `frontend/`:

1. Ejecutar el smoke check de importación e instanciación de vistas con `frontend/.venv/bin/python`.
2. Ejecutar el Quality Gate completo desde la raíz del proyecto:
   ```bash
   ./scripts/verify_all.sh
   ```
   Confirmar salida `FRONTEND SMOKE CHECK OK` y código de retorno `0`.

