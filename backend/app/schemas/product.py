from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    """Datos para crear una nueva categoría de productos."""

    name: str = Field(..., min_length=2, max_length=80, description="Nombre único de la categoría.", examples=["Bebidas"])
    description: Optional[str] = Field(default=None, max_length=255, description="Descripción opcional de la categoría.", examples=["Refrescos, jugos y agua embotellada"])


class CategoryRead(BaseModel):
    """Representación pública de una categoría."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime


class ProductCreate(BaseModel):
    """Datos requeridos para registrar un nuevo producto."""

    sku: str = Field(..., min_length=2, max_length=40, description="Código interno único del producto.", examples=["BEB-001"])
    barcode: Optional[str] = Field(default=None, max_length=64, description="Código de barras EAN/UPC opcional.", examples=["7411000123456"])
    name: str = Field(..., min_length=2, max_length=150, description="Nombre comercial del producto.", examples=["Coca-Cola 600ml"])
    description: Optional[str] = Field(default=None, max_length=500, description="Detalles adicionales del producto.")
    image_url: Optional[str] = Field(default=None, max_length=500, description="URL de imagen de referencia del producto.", examples=["https://ejemplo.com/coca.png"])
    price: Decimal = Field(..., ge=0, decimal_places=2, description="Precio unitario de venta en USD.", examples=["1.25"])
    stock: int = Field(default=0, ge=0, description="Cantidad inicial disponible en tienda.", examples=[42])
    min_stock: int = Field(default=5, ge=0, description="Umbral mínimo para alertas de stock bajo.", examples=[10])
    category_id: Optional[int] = Field(default=None, description="ID de la categoría asociada.", examples=[1])


class ProductUpdate(BaseModel):
    """Campos editables de un producto existente."""

    sku: Optional[str] = Field(default=None, min_length=2, max_length=40)
    barcode: Optional[str] = Field(default=None, max_length=64)
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, max_length=500)
    image_url: Optional[str] = Field(default=None, max_length=500)
    price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    stock: Optional[int] = Field(default=None, ge=0)
    min_stock: Optional[int] = Field(default=None, ge=0)
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


class ProductRead(BaseModel):
    """Representación pública de un producto en catálogo."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    barcode: Optional[str]
    name: str
    description: Optional[str]
    image_url: Optional[str]
    price: Decimal
    stock: int
    min_stock: int
    is_active: bool
    category_id: Optional[int]
    created_at: datetime
    updated_at: datetime


class ProductImageUploadRequest(BaseModel):
    """Carga de imagen de referencia en base64 para un producto."""

    filename: str = Field(..., min_length=3, max_length=255, examples=["coca.png"])
    content_base64: str = Field(..., min_length=4, description="Contenido binario de la imagen codificado en base64.")


class ProductImageUploadResponse(BaseModel):
    """URL pública relativa de la imagen almacenada en el servidor."""

    image_url: str

