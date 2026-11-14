import flet as ft


def safe_update(control: ft.Control) -> None:
    """Actualiza el control solo si ya está montado en una Page de Flet."""
    try:
        control.update()
    except RuntimeError:
        pass
