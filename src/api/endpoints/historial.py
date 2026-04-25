from fastapi import APIRouter

from src.crud.historial import get_historial, get_resumen
from src.schemas.historial import HistorialResponse, ResumenHistorialResponse


router = APIRouter(prefix="/historial", tags=["Historial"])


@router.get("/{usuario_id}", response_model=HistorialResponse)
async def obtener_historial(usuario_id: str) -> HistorialResponse:
    return await get_historial(usuario_id)


@router.get("/resumen/{usuario_id}", response_model=ResumenHistorialResponse)
async def obtener_resumen(usuario_id: str) -> ResumenHistorialResponse:
    return await get_resumen(usuario_id)
