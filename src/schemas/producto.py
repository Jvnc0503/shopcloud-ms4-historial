from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# Esquema Base con atributos comunes
class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=150, description="Nombre del producto")
    precio: float = Field(..., gt=0, description="Precio mayor a 0")
    stock: int = Field(default=0, ge=0, description="El stock no puede ser negativo")
    categoria_id: int

# Esquema para CREAR (hereda de Base)
class ProductoCreate(ProductoBase):
    pass

# Esquema para LEER y DEVOLVER al cliente web
class ProductoResponse(ProductoBase):
    id: int
    creado_en: datetime

    # Permite a Pydantic leer los objetos de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

class ProductoUpdate(BaseModel):
    stock: int = Field(..., ge=0, description="Nuevo stock del producto")