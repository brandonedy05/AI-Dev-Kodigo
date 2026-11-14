---
name: pos-db-schema
description: >-
  Procedimiento para modificar modelos SQLModel, agregar columnas o tablas, implementar
  soft-delete y mantener compatibilidad dual entre PostgreSQL (Supabase) y SQLite en
  backend/. Activar antes de editar backend/app/models/, backend/app/schemas/ o
  backend/app/core/database.py.
---

# Gestión de Modelos y Esquema SQLModel (`pos-db-schema`)

Reglas para evolucionar el esquema de base de datos en `backend/` sin romper bases
de datos existentes en PostgreSQL (Supabase) ni pruebas locales en SQLite.

## Cuándo usar esta skill

- Al agregar o modificar campos en modelos de `backend/app/models/`.
- Al actualizar `init_db()` en `backend/app/core/database.py`.
- Al implementar borrado lógico (soft-delete) o restricciones de integridad referencial.

## 1. Diseño de modelos y tipos

1. **Precisión monetaria:** Usar `Decimal` con `NUMERIC(12, 2)` para precios, costos, descuentos, límites de crédito y totales. Nunca usar `float` para dinero.
2. **Soft-delete:** Entidades maestras como productos y clientes utilizan bandera `is_active: bool = True` en lugar de `DELETE` físico, preservando el historial de ventas (`SaleItem`, `Sale`).
3. **Valores por defecto seguros:** Toda columna nueva agregada a una tabla existente debe ser nullable o definir un `DEFAULT` explícito para no fallar sobre filas previas.

## 2. Migración incremental en `backend/app/core/database.py`

1. Importar `app.models` antes de ejecutar `SQLModel.metadata.create_all(engine)`.
2. Para columnas nuevas en tablas existentes (`products`, `customers`, etc.), inspeccionar columnas actuales con `inspect(engine).get_columns("<table>")` y aplicar `ALTER TABLE <table> ADD COLUMN <col> <def>` solo si la columna no existe.
3. Usar definiciones SQL compatibles con **ambos** motores (PostgreSQL y SQLite):
   - Texto: `VARCHAR(N)`
   - Moneda: `NUMERIC(12, 2)`
   - Enteros: `INTEGER`
   - Booleanos: `BOOLEAN NOT NULL DEFAULT TRUE` / `FALSE`
4. Ejecutar cada `ALTER TABLE` dentro de `with engine.begin() as conn:` usando `sqlalchemy.text(...)`.

## 3. Sincronización de esquemas Pydantic

Actualizar los esquemas `*Create`, `*Update` y `*Read` en `backend/app/schemas/` junto con los servicios en `backend/app/services/` para exponer y validar los nuevos campos desde la API REST.

## 4. Verificación obligatoria

Ejecutar las pruebas de integración y el Quality Gate completo:
```bash
./scripts/verify_all.sh
```
Verificar que `SQLModel.metadata.create_all(engine)` e `init_db()` ejecutan sin errores en SQLite y que todos los tests de `pytest` pasan.

