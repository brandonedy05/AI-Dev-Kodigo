---
name: pos-backend-testing
description: >-
  Patrones y flujo para escribir y ejecutar pruebas de integración FastAPI con pytest,
  SQLite en memoria (StaticPool) y TestClient en backend/tests/. Activar cuando se
  agreguen endpoints, reglas de negocio o regresiones en backend/ y se requiera
  verificar cobertura con pytest.
---

# Pruebas de Integración FastAPI con `pytest` (`pos-backend-testing`)

Guía para estructurar pruebas reproducibles e independientes contra la API REST
del POS en `backend/tests/`.

## Cuándo usar esta skill

- Al agregar nuevos endpoints en `backend/app/routers/` o reglas en `backend/app/services/`.
- Al reproducir y cubrir bugs reportados en ventas, caja, productos, categorías o clientes.
- Al extender `backend/tests/test_pos_api.py` o crear nuevos módulos `test_*.py`.

## 1. Configuración de fixture aislada (`client`)

Seguir el patrón de `backend/tests/test_pos_api.py`:

1. Crear un engine SQLite en memoria con `StaticPool` y `check_same_thread=False`.
2. Hacer `monkeypatch.setattr(db_module, "engine", engine)` para aislar `init_db()` o cualquier acceso directo al engine.
3. Ejecutar `SQLModel.metadata.create_all(engine)`.
4. Sobrescribir la dependencia `get_session` en `app.dependency_overrides[get_session]` y limpiarla con `app.dependency_overrides.clear()` al finalizar el fixture.

## 2. Qué validar en cada prueba de flujo

- **Códigos HTTP exactos:** `201` en creación, `200` en consultas/actualizaciones, y errores esperados `400`/`404`/`409`/`422` en casos inválidos (ej. vender sin caja abierta, stock insuficiente, pago con tarjeta sin banco/tipo/autorización).
- **Precondiciones de negocio:** Abrir sesión de caja (`POST /api/v1/cash-register/open`) antes de probar `POST /api/v1/sales`.
- **Persistencia y efectos colaterales:** Verificar decremento de stock, cálculo de totales/cambio, soft-delete (`is_active=False` y exclusión del listado activo) y respuestas de reportes (`/api/v1/reports/...`).
- **Montos exactos:** Comparar valores decimales como strings formateados (`"1.25"`) o `Decimal` sin usar aritmética de punto flotante.

## 3. Ejecución y verificación

Correr únicamente la suite del backend durante el desarrollo rápido:
```bash
backend/.venv/bin/pytest -v backend/tests
```
Antes de dar por finalizada la tarea, ejecutar el Quality Gate completo:
```bash
./scripts/verify_all.sh
```

