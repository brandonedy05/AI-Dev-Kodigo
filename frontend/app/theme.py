"""Tokens visuales de Mi Tiendita Fácil basados en docs/DESIGN_SYSTEM.md y Stitch."""

import flet as ft


class Colors:
    # Superficies y neutros
    CANVAS = "#F8FAFC"
    SURFACE = "#FFFFFF"
    SURFACE_ALT = "#F1F5F9"
    BORDER = "#E2E8F0"
    BORDER_STRONG = "#CBD5E1"

    # Texto
    TEXT_PRIMARY = "#0F172A"
    TEXT_SECONDARY = "#475569"
    TEXT_MUTED = "#64748B"

    # Marca y acciones
    NAVY = "#0F172A"
    EMERALD = "#10B981"
    EMERALD_DARK = "#059669"
    EMERALD_SOFT = "#ECFDF5"
    ON_PRIMARY = "#FFFFFF"

    # Alertas y estados
    AMBER = "#F59E0B"
    AMBER_BG = "#FEF3C7"
    AMBER_TEXT = "#D97706"

    CRIMSON = "#EF4444"
    CRIMSON_BG = "#FEE2E2"
    CRIMSON_TEXT = "#DC2626"


FONT_FAMILY = "Plus Jakarta Sans"

CARD_SHADOW = ft.BoxShadow(
    spread_radius=0,
    blur_radius=10,
    color="#0F172A12",
    offset=ft.Offset(0, 3),
)
