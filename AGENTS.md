# Reglas del Proyecto - Mi Tiendita Fácil (POS)

## Integración de la Skill `pos-api-operator`

Siempre que el agente interactúe con la API REST del POS (`/api/v1`) para consultar,
registrar o depurar operaciones de ventas, clientes, caja o reportes:

1. **Carga obligatoria de la skill:** Lee y aplica las reglas de
   [pos-api-operator](.agents/skills/pos-api-operator/SKILL.md).
2. **Precondiciones antes de vender:**
   - Verifica `GET /api/v1/cash-register/current` antes de `POST /api/v1/sales`.
   - Verifica existencia y stock suficiente con `GET /api/v1/products` antes de enviar la venta.
3. **Consistencia:** Usa siempre montos formateados en USD (`$0.00`) y reporta el campo `detail` ante errores HTTP `400`/`404`/`409`.

