from enum import Enum


class DocumentType(str, Enum):
    """Tipos de documento de identificación para clientes."""

    CF = "CF"  # Consumidor Final
    DUI = "DUI"
    NIT = "NIT"
    PASAPORTE = "PASAPORTE"


class CashSessionStatus(str, Enum):
    """Estados posibles de una sesión de caja."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"


class CashMovementType(str, Enum):
    """Tipos de movimiento registrados en caja."""

    INCOME = "INCOME"    # Ingreso manual de efectivo
    EXPENSE = "EXPENSE"  # Retiro / gasto de efectivo
    SALE = "SALE"        # Venta en efectivo asociada al turno


class PaymentMethod(str, Enum):
    """Métodos de pago soportados en el POS."""

    CASH = "CASH"
    CARD = "CARD"
    TRANSFER = "TRANSFER"


class SaleStatus(str, Enum):
    """Estados de una venta."""

    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class UserRole(str, Enum):
    """Roles de acceso del sistema POS."""

    CAJERO = "CAJERO"
    ENCARGADO = "ENCARGADO"

