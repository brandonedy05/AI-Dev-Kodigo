---
name: pos-api-operator
description: >-
  Reglas operativas y flujos obligatorios para interactuar con la API REST del
  POS "Mi Tiendita Fácil" (ventas, clientes, caja y reportes). Activar siempre
  que el agente vaya a consultar, registrar o depurar operaciones contra el
  backend FastAPI del POS.
metadata:
  version: "1.0.0"
  author: "Mi Tiendita Fácil"
---

# POS API Operator (`Mi Tiendita Fácil`)

Esta skill condiciona el comportamiento del agente al operar contra la API REST
del POS (`/api/v1`), garantizando integridad operativa de caja e inventario.

## Cobertura de Endpoints

| Módulo | Endpoints principales |
| :--- | :--- |
| **Caja** | `GET /api/v1/cash-register/current`, `POST /api/v1/cash-register/open`, `POST /api/v1/cash-register/movements`, `POST /api/v1/cash-register/close` |
| **Catálogo** | `GET /api/v1/categories`, `GET /api/v1/products`, `POST /api/v1/products`, `PATCH /api/v1/products/{id}` |
| **Clientes** | `GET /api/v1/customers`, `POST /api/v1/customers`, `PATCH /api/v1/customers/{id}` |
| **Ventas** | `POST /api/v1/sales`, `GET /api/v1/sales`, `GET /api/v1/sales/{id}` |
| **Reportes** | `GET /api/v1/reports/sales-summary`, `GET /api/v1/reports/top-products`, `GET /api/v1/reports/low-stock` |

## Reglas Obligatorias de Comportamiento

1. **Verificar caja abierta antes de vender:**
   - Antes de ejecutar `POST /api/v1/sales`, el agente DEBE consultar `GET /api/v1/cash-register/current`.
   - Si responde `409 Conflict`, el agente NO debe reintentar la venta: debe informar al usuario que la caja está cerrada y solicitar nombre de cajero + fondo inicial para abrirla con `POST /api/v1/cash-register/open`.

2. **Validar existencia y stock antes de armar un ticket:**
   - Antes de enviar `POST /api/v1/sales`, consultar `GET /api/v1/products?search=...` para obtener el `product_id`, `price` actual y `stock` disponible.
   - Si `stock < quantity`, detener el flujo e informar exactamente cuántas unidades hay disponibles.

3. **Confirmación explícita en cierre de caja:**
   - Antes de llamar a `POST /api/v1/cash-register/close`, mostrar el resumen de `GET /api/v1/cash-register/current` (`expected_cash_in_drawer`) y pedir confirmación del efectivo físico contado (`closing_amount`).

4. **Formato de respuesta al usuario:**
   - Todos los montos monetarios deben mostrarse en USD con dos decimales (ej. `$12.50`).
   - Al completar una venta (`201 Created`), reportar siempre: `ticket_number`, `total`, `amount_paid` y `change_amount`.
   - Ante errores `400`, `404` o `409`, extraer el campo `detail` de la respuesta JSON y explicar la causa operativa exacta sin inventar datos.

