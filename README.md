# Mi Tiendita Fácil - Sistema de Punto de Venta (POS)

Sistema de Punto de Venta (POS) de escritorio y pantalla táctil construido con **FastAPI + SQLModel** en el backend y **Flet 1.1.2** en el frontend, siguiendo el sistema de diseño definido con **Google Stitch**.

---

## 📁 Estructura del Proyecto

```text
POS/
├── backend/                  # API REST FastAPI + SQLModel (SQLite local / PostgreSQL Supabase)
│   ├── app/
│   │   ├── core/             # Configuración, base de datos (init_db) y seguridad
│   │   ├── models/           # Modelos SQLModel (User, Product, Category, Customer, Sale, CashRegister)
│   │   ├── routers/          # Endpoints REST (/api/v1/auth, /users, /products, /customers, /sales, /cash-register, /reports)
│   │   ├── schemas/          # Esquemas Pydantic de entrada/salida
│   │   └── services/         # Lógica de negocio y reglas transaccionales
│   └── tests/                # Pruebas de integración con pytest + TestClient
├── frontend/                 # Aplicación de escritorio Flet 1.1.2
│   └── app/
│       ├── services/         # Cliente HTTP (POSApiClient) con manejo de sesión Bearer
│       ├── theme.py          # Paleta, tipografía y sombras Stitch
│       └── views/            # Vistas: Login, Terminal POS, Caja, Productos, Clientes, Reportes, Usuarios
├── docs/
│   └── DESIGN_SYSTEM.md      # Tokens, colores, tipografía y componentes visuales
├── scripts/
│   └── verify_all.sh         # Quality Gate integral (sintaxis, pytest y smoke check Flet)
└── README.md
```

---

## 🚀 Instalación y Ejecución

> **Prerrequisitos:** Python 3.12+ y `pip`. Cada módulo (`backend/` y `frontend/`) maneja su propio entorno virtual (`.venv`) para aislar sus dependencias.

### 1. Backend (FastAPI)

Desde la raíz del proyecto, entra a la carpeta `backend/`, crea el entorno virtual, instala `backend/requirements.txt` y levanta la API:

```bash
cd backend
python3 -m venv .venv

# Activar entorno virtual:
# En Linux / macOS:
source .venv/bin/activate
# En Windows (PowerShell):
# .venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt

# Iniciar servidor API
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Documentación interactiva OpenAPI: `http://127.0.0.1:8000/docs`
- Verificación de salud: `http://127.0.0.1:8000/health`

### 2. Frontend (Flet 1.1.2)

En una **segunda terminal** (manteniendo el backend corriendo), entra a `frontend/`, crea su entorno virtual, instala `frontend/requirements.txt` y ejecuta la app:

```bash
cd frontend
python3 -m venv .venv

# Activar entorno virtual:
# En Linux / macOS:
source .venv/bin/activate
# En Windows (PowerShell):
# .venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt

# Iniciar aplicación de escritorio POS
python -m app.main
```

---

## 🔐 Autenticación, Seguridad y Roles

### Métodos de Autenticación y Protección de Contraseñas

- **Hashing y Salting (`backend/app/core/security.py`):**
  - Las contraseñas nunca se almacenan ni se exponen en texto plano (`UserRead` omite `password_hash`).
  - Se utiliza `PBKDF2-HMAC-SHA256` (`210,000` iteraciones) con una sal criptográfica aleatoria de `16` bytes generada por usuario mediante `secrets.token_bytes(16)`.
  - Formato almacenado: `pbkdf2_sha256$210000$<salt_hex>$<hash_hex>`.
  - La verificación se realiza en tiempo constante mediante `hmac.compare_digest`.
- **Tokens de Sesión:**
  - Al iniciar sesión (`POST /api/v1/auth/login`), el backend emite un token `Bearer` firmado con `HMAC-SHA256` y expiración configurable (`AUTH_SECRET_KEY` y `AUTH_TOKEN_TTL_MINUTES` en `backend/app/core/config.py`).
  - El frontend envía el token en cada petición autenticada (`Authorization: Bearer <token>`) y muestra en el encabezado el nombre y rol del usuario conectado junto con la opción de cerrar sesión.

### Usuarios Iniciales (Seed Automático)

Al inicializar la base de datos (`init_db()` en `backend/app/core/database.py`), si la tabla `users` está vacía se crean automáticamente dos perfiles iniciales:

| Usuario | Contraseña Inicial | Rol | Acceso |
| :--- | :--- | :--- | :--- |
| `Encargado` | `admin123` | `ENCARGADO` | Acceso total a todos los módulos y mantenimiento CRUD de usuarios |
| `Cajero` | `cajero123` | `CAJERO` | Terminal de ventas, arqueo de caja y creación/consulta de clientes |

> **Recomendación:** Cambiar las contraseñas iniciales desde el módulo **Usuarios** al desplegar en producción y definir una clave segura en la variable de entorno `AUTH_SECRET_KEY`.

### Matriz de Permisos por Rol

- **`ENCARGADO`:**
  - `Vender` (Terminal POS), `Caja` (apertura, movimientos y cierre), `Productos` (CRUD + categorías + ficha técnica + soft-delete), `Clientes`, `Reportes` (KPIs, listado de ventas del día y stock bajo) y `Usuarios` (CRUD y activación/desactivación de cuentas).
- **`CAJERO`:**
  - `Vender` (lectura de catálogo/precios detalle-mayoreo y registro de ventas en efectivo/tarjeta), `Caja` (apertura con pre-llenado de usuario, movimientos y cierre) y `Clientes` (registro y consulta).
  - En backend, las rutas administrativas (`/api/v1/users`, `/api/v1/reports/*` y escritura en `/api/v1/products` y `/api/v1/categories`) responden `403 Forbidden` ante tokens con rol `CAJERO`.

---

## 🧩 Módulos Principales

- **Terminal de Ventas (`Vender`):** Catálogo visual con tarjetas de producto, búsqueda, modo Detalle/Mayoreo, carrito interactivo, cobro en Efectivo (con cálculo de cambio) o Tarjeta (banco, tipo Crédito/Débito y número de autorización).
- **Arqueo de Caja (`Caja`):** Apertura de turno, registro de ingresos/retiros de efectivo y cierre con cálculo de diferencia esperada.
- **Productos y Categorías (`Productos`):** CRUD completo con carga de imagen, ficha técnica (costo, mayoreo, unidad, IVA, ubicación, proveedor) y borrado lógico (`is_active=False`).
- **Clientes (`Clientes`):** Registro diferenciado para Consumidor Final / Personal y Contribuyente (con datos fiscales y ubicación obligatoria para El Salvador).
- **Reportes (`Reportes`):** KPIs del día, listado de ventas de hoy (ticket, fecha y hora, artículos, método de pago, total y modal de detalle) y alertas de stock bajo.
- **Usuarios (`Usuarios`):** Mantenimiento CRUD exclusivo para el Encargado con protección contra auto-desactivación o eliminación del último Encargado activo.

---

## 🌐 Documentación de la API REST (`/api/v1`)

- **Base URL local:** `http://127.0.0.1:8000/api/v1`
- **Documentación OpenAPI / Swagger:** `http://127.0.0.1:8000/docs`
- **Autenticación:** Cabecera `Authorization: Bearer <access_token>` obtenida desde `POST /api/v1/auth/login`.
- **Formato de errores:** JSON `{"detail": "Descripción del error"}` con códigos HTTP estándar (`400` validación de negocio, `401` no autenticado, `403` sin permisos de rol, `404` no encontrado, `409` conflicto de estado/duplicado, `422` esquema inválido).

### Sistema

| Método | Ruta | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Metadatos de la API y rutas principales | Público |
| `GET` | `/health` | Verificación de estado (`{"status": "ok"}`) | Público |

### Autenticación (`/api/v1/auth`)

| Método | Ruta | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/auth/options` | Lista usuarios activos (`id`, `name`, `role`) para la pantalla de login | Público |
| `POST` | `/api/v1/auth/login` | Autentica por `user_id` o `name` + `password`; retorna `access_token` y `user` | Público |
| `GET` | `/api/v1/auth/me` | Devuelve el perfil del usuario conectado según el token Bearer | Autenticado |

### Usuarios (`/api/v1/users`)

| Método | Ruta | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/users` | Lista usuarios (`?include_inactive=true\|false`) | `ENCARGADO` |
| `POST` | `/api/v1/users` | Crea usuario (`name`, `password`, `role`) con hash salteado | `ENCARGADO` |
| `GET` | `/api/v1/users/{user_id}` | Obtiene detalle de un usuario por ID | `ENCARGADO` |
| `PATCH` | `/api/v1/users/{user_id}` | Actualiza nombre, rol, estado o contraseña | `ENCARGADO` |
| `DELETE` | `/api/v1/users/{user_id}` | Desactiva usuario (soft-delete, `is_active=false`) | `ENCARGADO` |

### Categorías y Productos (`/api/v1/categories`, `/api/v1/products`)

| Método | Ruta | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/categories` | Lista categorías activas | Lectura |
| `POST` | `/api/v1/categories` | Crea categoría (`name`, `description`) | `ENCARGADO` |
| `PATCH` | `/api/v1/categories/{category_id}` | Actualiza categoría existente | `ENCARGADO` |
| `DELETE` | `/api/v1/categories/{category_id}` | Desactiva categoría (soft-delete) | `ENCARGADO` |
| `GET` | `/api/v1/products` | Lista productos (`?search=`, `?category_id=`, `?low_stock_only=`) | Lectura |
| `GET` | `/api/v1/products/{product_id}` | Obtiene ficha completa del producto | Lectura |
| `POST` | `/api/v1/products` | Registra producto (SKU único, precio detalle/mayoreo, stock, proveedor) | `ENCARGADO` |
| `PATCH` | `/api/v1/products/{product_id}` | Actualiza parcialmente un producto | `ENCARGADO` |
| `DELETE` | `/api/v1/products/{product_id}` | Desactiva producto (soft-delete) | `ENCARGADO` |
| `POST` | `/api/v1/products/upload-image` | Sube imagen en Base64 (PNG/JPG/WEBP/GIF, máx. 5 MB) y devuelve `image_url` | `ENCARGADO` |

### Clientes (`/api/v1/customers`)

| Método | Ruta | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/customers` | Lista clientes (`?search=`, `?include_inactive=`) | `CAJERO` / `ENCARGADO` |
| `GET` | `/api/v1/customers/{customer_id}` | Consulta cliente por ID | `CAJERO` / `ENCARGADO` |
| `POST` | `/api/v1/customers` | Registra cliente (`PERSONAL` o `TAXPAYER` con datos fiscales y ubicación) | `CAJERO` / `ENCARGADO` |
| `PATCH` | `/api/v1/customers/{customer_id}` | Actualiza parcialmente datos de cliente | `CAJERO` / `ENCARGADO` |
| `DELETE` | `/api/v1/customers/{customer_id}` | Desactiva cliente (soft-delete) | `CAJERO` / `ENCARGADO` |

### Caja / Arqueo (`/api/v1/cash-register`)

| Método | Ruta | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/cash-register/open` | Abre turno de caja (`cashier_name`, `opening_amount`) | `CAJERO` / `ENCARGADO` |
| `GET` | `/api/v1/cash-register/current` | Devuelve la sesión abierta, movimientos y efectivo esperado | `CAJERO` / `ENCARGADO` |
| `POST` | `/api/v1/cash-register/movements` | Registra ingreso (`INCOME`) o retiro (`EXPENSE`) manual | `CAJERO` / `ENCARGADO` |
| `POST` | `/api/v1/cash-register/close` | Cierra la sesión abierta calculando diferencia contra efectivo esperado | `CAJERO` / `ENCARGADO` |
| `GET` | `/api/v1/cash-register/sessions` | Historial reciente de sesiones de caja | `CAJERO` / `ENCARGADO` |

### Ventas (`/api/v1/sales`)

| Método | Ruta | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/sales` | Registra venta (`CASH`/`CARD`/`TRANSFER`, `price_mode`: `RETAIL`/`WHOLESALE`, datos de tarjeta si aplica), descuenta stock y suma a caja | `CAJERO` / `ENCARGADO` |
| `GET` | `/api/v1/sales` | Lista ventas recientes con sus líneas (`?limit=50`) | `CAJERO` / `ENCARGADO` |
| `GET` | `/api/v1/sales/{sale_id}` | Obtiene detalle completo de una venta | `CAJERO` / `ENCARGADO` |

### Reportes (`/api/v1/reports`)

| Método | Ruta | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/reports/sales-summary` | Ingresos, transacciones, ticket promedio y desglose por método (`?start_date=`, `?end_date=`) | `ENCARGADO` |
| `GET` | `/api/v1/reports/top-products` | Productos más vendidos en el rango de fechas (`?limit=10`) | `ENCARGADO` |
| `GET` | `/api/v1/reports/low-stock` | Productos activos con `stock <= min_stock` | `ENCARGADO` |

### Ejemplo de Uso (`curl`)

```bash
# 1. Iniciar sesión y obtener token
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"name": "Encargado", "password": "admin123"}'

# 2. Consultar usuarios usando el token Bearer
curl -s http://127.0.0.1:8000/api/v1/users \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## ✅ Verificación (Quality Gate)

Antes de cerrar cualquier cambio, ejecutar desde la raíz del proyecto:

```bash
./scripts/verify_all.sh
```

Este script valida:
1. Compilación de sintaxis Python en `backend/app`, `backend/tests` y `frontend/app`.
2. Suite de pruebas de integración con `pytest` (`backend/.venv/bin/pytest -v`).
3. Smoke check de instanciación de todas las vistas Flet `1.1.2`.
