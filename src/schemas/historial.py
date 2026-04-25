from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.producto import ProductoResponse
from src.schemas.usuario import UsuarioResponse


class DetallePedidoResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    producto_id: int
    cantidad: int = Field(..., ge=1)
    precio_unitario: float = Field(..., ge=0)
    producto: ProductoResponse | None = None


class PedidoResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    usuario_id: int | str
    total: float = Field(..., ge=0)
    estado: str | None = None
    creado_en: datetime | None = None
    detalle: list[DetallePedidoResponse] = Field(default_factory=list)


class HistorialResponse(BaseModel):
    usuario: UsuarioResponse
    pedidos: list[PedidoResponse]


class ResumenHistorialResponse(BaseModel):
    usuario_id: str
    nro_pedidos: int = Field(..., ge=0)
    total_gastado: float = Field(..., ge=0)