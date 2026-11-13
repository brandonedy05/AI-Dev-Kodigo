# Mi Tiendita Fácil - Sistema de Punto de Venta (POS)

Sistema moderno, ergonómico y de alta eficiencia diseñado para terminales de Punto de Venta (POS) en escritorio y pantallas táctiles (relaciones 16:9 y 4:3).

## 📁 Estructura del Proyecto

```text
├── designs/                        # Prototipos y pantallas exportadas desde Google Stitch
│   ├── 01-login-apertura-caja.html         # Login, selección de cajero y arqueo inicial
│   ├── 02-catalogo-gestion-productos.html  # Catálogo, filtrado y vista de productos
│   ├── 03-registro-edicion-producto.html   # Formulario CRUD para inventario y productos
│   ├── 04-directorio-crud-clientes.html    # Directorio y gestión de clientes (El Salvador)
│   ├── 05-modal-cobro-vuelto.html          # Modal de checkout, cálculo de vuelto y pago
│   ├── 06-terminal-ventas-pos.html         # Terminal principal de ventas con teclado numérico
│   └── 07-punto-de-venta-pos.html          # Vista simplificada / responsiva de venta
├── docs/
│   └── DESIGN_SYSTEM.md            # Especificación completa de tokens, colores, tipografía y componentes
└── README.md
```

## 🎨 Sistema de Diseño

El sistema de diseño está documentado en detalle en [`docs/DESIGN_SYSTEM.md`](docs/DESIGN_SYSTEM.md).

- **Tipografía:** [Plus Jakarta Sans](https://fonts.google.com/specimen/Plus+Jakarta+Sans) con números tabulares (`tabular-nums`) para legibilidad monetaria en tiempo real.
- **Paleta de Colores:**
  - **Primario (`#10B981` — Fresh Emerald):** Acciones afirmativas de cobro, tickets completados y confirmaciones.
  - **Secundario (`#0F172A` — Deep Navy):** Barras estructurales, encabezados y dock del ticket.
  - **Terciario (`#F59E0B` — Amber Alert):** Avisos de stock bajo, descuentos y tickets en espera.
  - **Error (`#EF4444` / `#BA1A1A` — Crimson):** Anulación de ventas, eliminación de líneas y alertas de inventario agotado.
- **Layout:**
  - División fija 65% catálogo / 35% dock de ticket activo con botón de cobro persistente.
