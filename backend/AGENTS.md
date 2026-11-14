# Reglas del Área Backend (`backend/`)

Aplica a todo agente o subagente (`backend-dev`) que modifique archivos dentro de `backend/`:

1. **Arquitectura por capas:** Mantener separación estricta entre `app/routers/`, `app/services/`, `app/models/` y `app/schemas/`. No colocar lógica de negocio ni consultas SQL complejas directamente en los routers.
2. **Precisión financiera y concurrencia:**
   - Todos los montos monetarios deben usar `Decimal` y `Numeric(12, 2)`.
   - Al registrar ventas (`sale_service.py`), validar sesión de caja abierta y bloquear filas de productos con `.with_for_update()` antes de descontar stock.
3. **Compatibilidad con Frontend:** Antes de cambiar rutas, parámetros o campos de respuesta en `app/schemas/`, revisar su uso en `frontend/app/services/api_client.py`.
4. **PostgreSQL / Supabase:** Seguir las reglas de `.agents/skills/supabase-postgres-best-practices/SKILL.md` al modificar modelos o índices.
5. **Verificación:** Ejecutar `cd backend && .venv/bin/pytest -v` después de cada cambio.

