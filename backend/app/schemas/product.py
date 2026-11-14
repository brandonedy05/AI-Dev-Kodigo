from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    """Datos para crear una nueva categoría de productos."""

    name: str = Field(..., min_length=2, max_length=80, description="Nombre único de la categoría.", examples=["Bebidas"])
    description: Optional[str] = Field(default=None, max_length=255, description="Descripción opcional de la categoría.", examples=["Refrescos, jugos y agua embotellada"])


class CategoryUpdate(BaseModel):
    """Campos editables de una categoría existente."""

    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


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
    unit_of_measure: str = Field(default="Unidad", max_length=30, description="Unidad de medida (Unidad, Litro, Kg, Paquete).")
    price: Decimal = Field(..., ge=0, decimal_places=2, description="Precio unitario de venta en USD.", examples=["1.25"])
    cost_price: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2, description="Costo neto de compra en USD.")
    wholesale_price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2, description="Precio de mayoreo opcional en USD.")
    applies_iva: bool = Field(default=True, description="Indica si el producto grava IVA 13%.")
    stock: int = Field(default=0, ge=0, description="Cantidad inicial disponible en tienda.", examples=[42])
    min_stock: int = Field(default=5, ge=0, description="Umbral mínimo para alertas de stock bajo.", examples=[10])
    location: Optional[str] = Field(default=None, max_length=80, description="Ubicación o pasillo en tienda.")
    supplier_name: Optional[str] = Field(default=None, max_length=120, description="Proveedor principal.")
    supplier_code: Optional[str] = Field(default=None, max_length=60, description="Código de referencia del proveedor.")
    category_id: Optional[int] = Field(default=None, description="ID de la categoría asociada.", examples=[1])


class ProductUpdate(BaseModel):
    """Campos editables de un producto existente."""

    sku: Optional[str] = Field(default=None, min_length=2, max_length=40)
    barcode: Optional[str] = Field(default=None, max_length=64)
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, max_length=500)
    image_url: Optional[str] = Field(default=None, max_length=500)
    unit_of_measure: Optional[str] = Field(default=None, max_length=30)
    price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    cost_price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    wholesale_price: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    applies_iva: Optional[bool] = None
    stock: Optional[int] = Field(default=None, ge=0)
    min_stock: Optional[int] = Field(default=None, ge=0)
    location: Optional[str] = Field(default=None, max_length=80)
    supplier_name: Optional[str] = Field(default=None, max_length=120)
    supplier_code: Optional[str] = Field(default=None, max_length=60)
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
    unit_of_measure: str
    price: Decimal
    cost_price: Decimal
    wholesale_price: Optional[Decimal]
    applies_iva: bool
    stock: int
    min_stock: int
    location: Optional[str]
    supplier_name: Optional[str]
    supplier_code: Optional[str]
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

