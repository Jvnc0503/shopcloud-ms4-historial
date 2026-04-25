from pydantic import BaseModel, Field, ConfigDict

class UsuarioResponse(BaseModel):
    nombre: str
    apellido: str
    pais: str | None