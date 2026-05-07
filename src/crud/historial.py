from __future__ import annotations

from typing import Any, TypeVar

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError

from src.config import get_settings
from src.schemas.historial import HistorialResponse, PedidoResponse, ResumenHistorialResponse
from src.schemas.producto import ProductoResponse
from src.schemas.usuario import UsuarioResponse


settings = get_settings()

ModelType = TypeVar("ModelType", bound=BaseModel)

_PEDIDO_KEY_MAP = {
    "usuarioId": "usuario_id",
    "creadoEn": "creado_en",
}

_DETALLE_KEY_MAP = {
    "productoId": "producto_id",
    "precioUnitario": "precio_unitario",
}


def _ensure_snake_case(payload: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    normalized = dict(payload)
    for source_key, target_key in mapping.items():
        if source_key in normalized and target_key not in normalized:
            normalized[target_key] = normalized[source_key]
    return normalized


def _normalize_detalle_items(detalle: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in detalle:
        if isinstance(item, dict):
            normalized.append(_ensure_snake_case(item, _DETALLE_KEY_MAP))
    return normalized


def _normalize_pedido(pedido: dict[str, Any]) -> dict[str, Any]:
    normalized = _ensure_snake_case(pedido, _PEDIDO_KEY_MAP)

    detalle = normalized.get("detalle")
    if isinstance(detalle, list):
        normalized["detalle"] = _normalize_detalle_items(detalle)

    detalle_alt = normalized.get("detalle_pedidos")
    if isinstance(detalle_alt, list):
        normalized["detalle_pedidos"] = _normalize_detalle_items(detalle_alt)

    return normalized


def _validate_model(model_cls: type[ModelType], payload: Any, error_detail: str) -> ModelType:
    try:
        return model_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=502, detail=error_detail) from exc


def _unwrap_data(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def _extract_usuario(payload: Any) -> dict[str, Any]:
    data = _unwrap_data(payload)

    if isinstance(data, dict) and "usuario" in data:
        data = data["usuario"]

    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="MS3 devolvió un formato inesperado de usuario")

    usuario = dict(data)

    direccion = usuario.get("direccion")
    if isinstance(direccion, dict) and "pais" not in usuario:
        usuario["pais"] = direccion.get("pais")

    if "_id" in usuario and "id" not in usuario:
        usuario["id"] = str(usuario["_id"])

    return usuario


def _extract_pedidos(payload: Any) -> list[dict[str, Any]]:
    data = _unwrap_data(payload)

    if isinstance(data, dict) and "pedidos" in data:
        data = data["pedidos"]

    if data is None:
        return []

    if not isinstance(data, list):
        raise HTTPException(status_code=502, detail="MS2 devolvió un formato inesperado de pedidos")

    return [_normalize_pedido(dict(item)) for item in data if isinstance(item, dict)]


def _extract_pedido(payload: Any) -> dict[str, Any]:
    data = _unwrap_data(payload)

    if isinstance(data, dict) and "pedido" in data:
        data = data["pedido"]

    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="MS2 devolvió un formato inesperado de pedido")

    return _normalize_pedido(dict(data))


def _extract_producto(payload: Any) -> dict[str, Any]:
    data = _unwrap_data(payload)

    if isinstance(data, dict) and "producto" in data:
        data = data["producto"]

    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="MS1 devolvió un formato inesperado de producto")

    return dict(data)


def _extract_detalle(pedido_data: dict[str, Any]) -> list[dict[str, Any]]:
    detalle = pedido_data.get("detalle")
    if isinstance(detalle, list):
        return _normalize_detalle_items([dict(item) for item in detalle if isinstance(item, dict)])

    detalle_alt = pedido_data.get("detalle_pedidos")
    if isinstance(detalle_alt, list):
        return _normalize_detalle_items([dict(item) for item in detalle_alt if isinstance(item, dict)])

    return []


async def _safe_get_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, Any]:
    try:
        response = await client.get(url, params=params, headers=headers, timeout=settings.REQUEST_TIMEOUT_SECONDS)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo conectar con servicio upstream: {exc.request.url}",
        ) from exc

    if response.status_code == 204:
        return response.status_code, None

    try:
        payload = response.json() if response.text else None
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"Respuesta no JSON desde servicio upstream: {url}") from exc

    return response.status_code, payload


async def _get_usuario(
    client: httpx.AsyncClient,
    usuario_id: str,
    headers: dict[str, str] | None,
) -> UsuarioResponse:
    url = f"{settings.MS3_URL.rstrip('/')}/usuarios/{usuario_id}"
    status_code, payload = await _safe_get_json(client, url, headers=headers)

    if status_code == 404:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if status_code >= 400:
        raise HTTPException(status_code=502, detail=f"MS3 respondió {status_code} al consultar usuario")

    return _validate_model(UsuarioResponse, _extract_usuario(payload), "MS3 devolvió un usuario inválido")


async def _get_pedidos(
    client: httpx.AsyncClient,
    usuario_id: str,
    headers: dict[str, str] | None,
) -> list[dict[str, Any]]:
    url = f"{settings.MS2_URL.rstrip('/')}/pedidos/usuario/{usuario_id}"
    status_code, payload = await _safe_get_json(client, url, headers=headers)

    if status_code == 404:
        return []
    if status_code >= 400:
        raise HTTPException(status_code=502, detail=f"MS2 respondió {status_code} al consultar pedidos")

    return _extract_pedidos(payload)


async def _get_detalle_for_pedido(
    client: httpx.AsyncClient,
    pedido_data: dict[str, Any],
    headers: dict[str, str] | None,
) -> list[dict[str, Any]]:
    detalle = _extract_detalle(pedido_data)
    if detalle:
        return detalle

    pedido_id = pedido_data.get("id")
    if pedido_id is None:
        return []

    url = f"{settings.MS2_URL.rstrip('/')}/pedidos/{pedido_id}"
    status_code, payload = await _safe_get_json(client, url, headers=headers)

    if status_code == 404:
        return []
    if status_code >= 400:
        raise HTTPException(status_code=502, detail=f"MS2 respondió {status_code} al consultar pedido {pedido_id}")

    pedido_detalle = _extract_pedido(payload)
    return _extract_detalle(pedido_detalle)


async def _get_producto(
    client: httpx.AsyncClient,
    producto_id: int,
    cache: dict[int, ProductoResponse | None],
    headers: dict[str, str] | None,
) -> ProductoResponse | None:
    if producto_id in cache:
        return cache[producto_id]

    url = f"{settings.MS1_URL.rstrip('/')}/productos/{producto_id}"
    status_code, payload = await _safe_get_json(client, url, headers=headers)

    if status_code == 404:
        cache[producto_id] = None
        return None
    if status_code >= 400:
        raise HTTPException(status_code=502, detail=f"MS1 respondió {status_code} al consultar producto {producto_id}")

    producto = _validate_model(ProductoResponse, _extract_producto(payload), "MS1 devolvió un producto inválido")
    cache[producto_id] = producto
    return producto


async def get_historial(usuario_id: str, authorization: str) -> HistorialResponse:
    headers = {"Authorization": authorization}

    async with httpx.AsyncClient() as client:
        usuario = await _get_usuario(client, usuario_id, headers)
        pedidos_raw = await _get_pedidos(client, usuario_id, headers)

        producto_cache: dict[int, ProductoResponse | None] = {}
        pedidos_normalizados: list[PedidoResponse] = []

        for pedido_data in pedidos_raw:
            detalle = await _get_detalle_for_pedido(client, pedido_data, headers)
            detalle_enriquecido: list[dict[str, Any]] = []

            for item in detalle:
                item_enriquecido = dict(item)
                producto_id = item_enriquecido.get("producto_id")

                if type(producto_id) is int:
                    producto = await _get_producto(client, producto_id, producto_cache, headers)
                    item_enriquecido["producto"] = producto.model_dump(mode="json") if producto else None
                else:
                    item_enriquecido["producto"] = None

                detalle_enriquecido.append(item_enriquecido)

            pedido_normalizado = dict(pedido_data)
            pedido_normalizado["detalle"] = detalle_enriquecido
            pedido_normalizado.pop("detalle_pedidos", None)

            pedidos_normalizados.append(
                _validate_model(PedidoResponse, pedido_normalizado, "MS2 devolvió un pedido inválido")
            )

        return HistorialResponse(usuario=usuario, pedidos=pedidos_normalizados)


async def get_resumen(usuario_id: str, authorization: str) -> ResumenHistorialResponse:
    headers = {"Authorization": authorization}

    async with httpx.AsyncClient() as client:
        await _get_usuario(client, usuario_id, headers)
        pedidos = await _get_pedidos(client, usuario_id, headers)

    total_gastado = 0.0
    for pedido in pedidos:
        try:
            total_gastado += float(pedido.get("total", 0) or 0)
        except (TypeError, ValueError):
            continue

    return ResumenHistorialResponse(
        usuario_id=str(usuario_id),
        nro_pedidos=len(pedidos),
        total_gastado=round(total_gastado, 2),
    )
