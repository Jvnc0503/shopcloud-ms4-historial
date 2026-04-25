from pydantic import BaseModel, Field, ConfigDict

class CategoriaBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre de la categoría")

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaResponse(CategoriaBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class CategoriaUpdate(CategoriaBase):
    pass