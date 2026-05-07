from fastapi import APIRouter, Header, HTTPException

from src.crud.historial import get_historial, get_resumen
from src.schemas.historial import HistorialResponse, ResumenHistorialResponse


router = APIRouter(prefix="/historial", tags=["Historial"])


@router.get("/{usuario_id}", response_model=HistorialResponse)
async def obtener_historial(
    usuario_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> HistorialResponse:
    if not authorization:
        raise HTTPException(status_code=401, detail="Falta el token de autorización")

    return await get_historial(usuario_id, authorization)


@router.get("/resumen/{usuario_id}", response_model=ResumenHistorialResponse)
async def obtener_resumen(
    usuario_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ResumenHistorialResponse:
    if not authorization:
        raise HTTPException(status_code=401, detail="Falta el token de autorización")

    return await get_resumen(usuario_id, authorization)
