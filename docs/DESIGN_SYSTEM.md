---
name: Mi Tiendita Fácil
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#3c4a42'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#6c7a71'
  outline-variant: '#bbcabf'
  surface-tint: '#006c49'
  primary: '#006c49'
  on-primary: '#ffffff'
  primary-container: '#10b981'
  on-primary-container: '#00422b'
  inverse-primary: '#4edea3'
  secondary: '#565e74'
  on-secondary: '#ffffff'
  secondary-container: '#dae2fd'
  on-secondary-container: '#5c647a'
  tertiary: '#855300'
  on-tertiary: '#ffffff'
  tertiary-container: '#e29100'
  on-tertiary-container: '#523200'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#6ffbbe'
  primary-fixed-dim: '#4edea3'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#005236'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 15px
    fontWeight: '700'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.02em
  numeric-keypad:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  numeric-total:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '800'
    lineHeight: 48px
    letterSpacing: -0.03em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-compact: 0.5rem
  margin: 1.25rem
  margin-screen: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1.25rem
  space-xl: 2rem
---

## Brand & Style

The design system establishes a high-efficiency, reliable, and ergonomic visual language engineered specifically for high-frequency desktop Point of Sale (POS) environments. The brand personality blends retail precision with accessible modern commerce: trustworthy, quick-witted, and frictionless.

Target users span busy cashiers operating under rapid checkout queues and shop owners managing inventory, closing shifts, and reviewing daily tallies. The primary emotional outcome is operational calm and cognitive clarity: eliminating mis-taps, speeding up basket processing, and highlighting transaction statuses without visual fatigue during 8-to-12-hour shifts.

The aesthetic fuses **Modern Functionalism** with **Tactile Utility**:
- Crisp, distraction-free surfaces with ample spatial buffer.
- High-contrast visual anchors for fast peripheral recognition (e.g., total sums, payment triggers).
- Generously scaled hit targets designed for both touch monitors and physical barcode scanner / keyboard-driven workflows.

## Colors

The palette is optimized for operational speed, status clarity, and all-day visual endurance under artificial retail lighting.

- **Primary (`#10B981` — Fresh Emerald):** Reserved strictly for affirmative retail actions: "Cobrar", completed receipts, successful barcode matches, and net profits. Never dilute its urgency by using it for passive backgrounds.
- **Secondary (`#0F172A` — Slate Deep Navy):** Represents structural authority. Used for header bars, active cart containers, major metrics, and navigation rails to frame and balance the workspace.
- **Tertiary (`#F59E0B` — Amber Alert):** Applied intentionally to indicate stock warnings, discount badges, pending validations, and hold tickets.
- **Error & Annulment (`#EF4444` — Crisp Crimson):** Dedicated to void lines ("Anular venta"), item deletions, refunds, and zero-inventory warnings.
- **Neutrals & Surfaces (`#FFFFFF`, `#F8FAFC`, `#F1F5F9`, `#64748B`):** Clean, neutral foundational layers that reduce glare while maintaining contrast ratios above WCAG 2.1 AAA for numeric readouts.

## Typography

The type system is powered by **Plus Jakarta Sans**, offering geometric readability with friendly, open counters that remain sharp on lower-density POS touchscreen panels.

### Numeric Legibility
All monetary figures, SKU quantities, inventory stocks, and totals must render using tabular figures (`font-variant-numeric: tabular-nums;` or `font-feature-settings: "tnum"`). This prevents optical jumping when cart balances update during rapid item scanning.

### Hierarchy Guidelines
- **`numeric-total` & `display-xl`:** Exclusively for total due balances, customer change screens, and primary shift end cash summaries.
- **`headline-sm` & `body-lg`:** For product titles inside grid tiles and receipt line items to guarantee glanceable identification from arm’s-length distances.
- **`label-sm`:** For stock status indicators, shortcut keys (e.g., `[F4]`, `[ESC]`), and item category markers.

## Layout & Spacing

The layout is built as a structured, fixed-split desktop application optimized for standard POS ratios (16:9 and 4:3 touch monitors, 1280px to 1920px width).

### Layout Framework
- **Master Split:**
  - **Left Section (Product Catalog & Quick Actions):** 60–65% fluid workspace holding product grids, category filtering carousels, and search inputs.
  - **Right Section (Ticket & Summary Dock):** 35–40% fixed minimum column (min 420px, max 520px) retaining active ticket lines, subtotal breakdowns, and persistent checkout action modules.
- **Grid Structure:** The catalog section uses an adaptive CSS auto-fit grid (`minmax(140px, 1fr)`) with an internal gutter of `space-md` (`0.75rem`) to fit between 4 to 8 product touch-tiles per row depending on resolution.
- **Tap Tolerances:** Any interactive checkout button or product tile must sustain a minimum target height of 48px, with 60px+ preferred for high-frequency actions (`Cobrar`, `Buscar`, numeric keypad).

## Elevation & Depth

Visual hierarchy uses crisp **tonal layering combined with subtle ambient shadows**, providing physical tactility without heavy visual clutter.

- **Base Canvas (Level 0):** Pure muted tone `#F8FAFC`. Houses non-interactive background areas.
- **Surface Panels (Level 1):** Solid `#FFFFFF` with ultra-low contrast border (`1px solid #E2E8F0`). Used for product tiles, category pills, and checkout ticket rows.
- **Floating Cart & Active Modals (Level 2):** Layered with a dual soft ambient drop: `box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.05), 0 2px 4px -2px rgba(15, 23, 42, 0.05);`.
- **Payment Modals & Overlays (Level 3):** Modal overlays with backdrop scrim (`rgba(15, 23, 42, 0.45)`) and elevated card containers: `box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 8px 10px -6px rgba(15, 23, 42, 0.05);`.
- **Tactile Button Press:** Buttons transition downward on `:active` (`transform: scale(0.98)` or inset shadow), mimicking physical register keys.

## Shapes

The design system employs **Rounded (Level 2)** geometry to balance approachability with screen-space efficiency.

- **Base Radius (0.5rem / 8px):** Standard controls, inputs, dropdowns, badge pills, and inner data table borders.
- **Large Radius (`rounded-lg`, 1rem / 16px):** Product catalog tiles, key summary cards, ticket list envelopes, and slide-in panels.
- **Extra-Large Radius (`rounded-xl`, 1.5rem / 24px):** Used strategically on the primary "COBRAR" action cluster, customer payment method selector cards, and primary modal containers.
- **Pill (Fully rounded):** Reserved for category filter badges and quantity increment/decrement toggles.

## Components

### 1. Primary Action Button ("Cobrar")
- **Visuals:** Background `#10B981`, text `#FFFFFF`, bold `headline-md` type.
- **Dimensions:** Full ticket width, minimum height 64px, `rounded-xl`.
- **States:** Hover `#059669`, active press translation, disabled `#CBD5E1`. Displays the total sum inside the button for double confirmation.

### 2. Destructive & Annulling Actions
- **Visuals:** Outline or soft tint default (`#FEE2E2` background, `#DC2626` text). Turns solid `#EF4444` on destructive confirmation dialogs.
- **Usage:** "Anular Venta", "Eliminar Partida", "Devolución".

### 3. Product Catalog Tiles
- **Structure:** Surface card `#FFFFFF`, 1px border `#E2E8F0`, `rounded-lg` (16px).
- **Contents:** Upper visual/thumbnail or 2-letter fallback, title in `body-lg` (bold), clear emerald numeric price at bottom right, stock chip top right.
- **Touch Target:** Minimum 130px height x 120px width.

### 4. Ticket Item List
- **Row Styling:** Zebra striping alternate `#FFFFFF` and `#F8FAFC`. Height 52px.
- **Data Columns:** Quantity selector stepper ([-], count, [+]), item description, unit price, total price (tabular nums), and a discrete trash trigger on row end.

### 5. Category Chips & Badges
- **Inactive:** Surface `#FFFFFF`, border `#E2E8F0`, text `#64748B`.
- **Active:** Background `#0F172A`, text `#FFFFFF`, border `#0F172A`.
- **Stock Badges:**
  - In Stock: Tinted neutral `#F1F5F9`, text `#475569`.
  - Low Stock: Background `#FEF3C7`, text `#D97706`.
  - Out of Stock: Background `#FEE2E2`, text `#DC2626`.

### 6. Search Bar & Barcode Direct Input
- **Styling:** Height 52px, `rounded-lg`, background `#FFFFFF`, border 2px solid `#E2E8F0`. Focused: border `#10B981` with subtle glow.
- **Affordance:** Pre-fixed barcode scanner icon and a right-aligned shortcut badge indicator `[F2]`.

### 7. Numeric Keypad (Numpad)
- **Grid:** 3x4 layout. Keys styled as tactile tiles (`#FFFFFF` with `#F1F5F9` bottom border).
- **Feedback:** Audio chime support and immediate tactile scale-down effect on press for high-speed cash registration.