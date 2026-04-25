from pydantic import BaseModel, ConfigDict


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str | None = None
    nombre: str
    apellido: str
    pais: str | None = None