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

---

## Modo de Ejecución: Directo vs. Subagentes

El usuario tiene control total sobre cuándo se usan subagentes:

- **Modo Directo (sin subagentes):**
  - **Obligatorio** cuando el usuario indique *"sin agentes"*, *"modo directo"*, *"hazlo directo"* o similar, y recomendado para cambios puntuales o de un solo módulo.
  - El agente principal realiza los cambios directamente sin invocar `invoke_subagent` ni `swarm`.
- **Modo Multi-Agente (subagentes por área):**
  - Usar cuando el usuario lo solicite (*"usa agentes"*, *"con subagentes"*, `/teamwork`) o en iteraciones grandes que abarquen simultáneamente `backend/` y `frontend/`.
  - Roles especializados:
    - `backend-dev`: trabaja exclusivamente en `backend/` siguiendo `backend/AGENTS.md`.
    - `frontend-dev`: trabaja exclusivamente en `frontend/` siguiendo `frontend/AGENTS.md`.
    - `qa-tester`: ejecuta la skill [pos-qa-gate](.agents/skills/pos-qa-gate/SKILL.md) y `./scripts/verify_all.sh` tras los cambios.

## Quality Gate Obligatorio

Antes de dar por terminada cualquier iteración con cambios de código (en modo directo o multi-agente), ejecutar:

```bash
./scripts/verify_all.sh
```
