# Reglas del Área Frontend (`frontend/`)

Aplica a todo agente o subagente (`frontend-dev`) que modifique archivos dentro de `frontend/`:

1. **Compatibilidad estricta con Flet `1.1.2`:**
   - Usar `ft.Button(content=...)` (no `ft.ElevatedButton`).
   - Usar `ft.Chip(...)` (no `ft.ChoiceChip`).
   - Usar `ft.Border.all(...)` / `ft.Border.only(...)` (no `ft.border.*`).
   - Usar `ft.Padding.symmetric(...)` (no `ft.padding.*`).
   - En `ft.SegmentedButton`, pasar `selected` como `list[str]` (ej. `["CASH"]`), **nunca** como `set` (`{"CASH"}`), porque `msgpack` no serializa `set`.
   - Para notificaciones usar `page.show_dialog(ft.SnackBar(...))` y arrancar con `ft.run(main)`.
2. **Sistema de diseño:** Respetar los colores y tipografía definidos en `frontend/app/theme.py` (basado en `docs/DESIGN_SYSTEM.md` y `designs/`).
3. **Consumo de API:** Todas las llamadas HTTP deben pasar por `frontend/app/services/api_client.py` (`POSApiClient`) manejando `POSApiError`.
4. **Verificación:** Validar siempre que todas las vistas se instancian sin errores usando `frontend/.venv/bin/python`.

