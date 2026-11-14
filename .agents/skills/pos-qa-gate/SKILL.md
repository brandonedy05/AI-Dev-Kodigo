---
name: pos-qa-gate
description: >-
  Procedimiento de verificación integral (Quality Gate) para el POS "Mi Tiendita
  Fácil". Activar al finalizar cambios en backend/, frontend/ o ambos para
  ejecutar pruebas automatizadas, smoke checks de Flet 1.1.2 y validación de
  contratos antes de entregar una iteración.
metadata:
  version: "1.0.0"
  author: "Mi Tiendita Fácil"
---

# POS QA Gate (`qa-tester`)

Este flujo valida que ninguna iteración rompa el backend FastAPI ni el frontend Flet.

## Pasos de Verificación

1. **Ejecutar la suite unificada desde la raíz del repositorio:**
   ```bash
   ./scripts/verify_all.sh
   ```
2. **Revisar qué valida cada etapa:**
   - **Sintaxis:** `python3 -m compileall -q backend frontend`
   - **Backend:** `backend/.venv/bin/pytest -v` (flujo completo de categorías, productos, clientes, caja, ventas, stock y reportes).
   - **Frontend:** Instanciación de `POSTerminalView`, `CashRegisterView`, `ProductsView`, `CustomersView` y `ReportsView` con `frontend/.venv/bin/python` para detectar incompatibilidades de Flet `1.1.2` o errores de serialización (ej. `set` en `SegmentedButton`).
3. **Criterio de rechazo:**
   - Si cualquier paso devuelve código distinto de `0`, **no aprobar la iteración**: reportar el archivo, línea y error exacto al agente correspondiente (`backend-dev` o `frontend-dev`) o corregirlo directamente en modo directo.

