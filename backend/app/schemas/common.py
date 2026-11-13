from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Esquema estándar de respuesta para errores HTTP."""

    detail: str = Field(..., description="Descripción legible del error ocurrido.", examples=["No hay una sesión de caja abierta."])

