from __future__ import annotations

from src.crud import historial as historial_service


def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ms4-historial"}


def test_historial_endpoint_consolidates_upstream_data(client, monkeypatch):
    async def fake_safe_get_json(_client, url: str, *, params=None):
        if url.endswith("/usuarios/u-1"):
            return 200, {"status": "success", "data": {"nombre": "Ana", "apellido": "Lopez", "pais": "Perú"}}

        if url.endswith("/pedidos"):
            assert params == {"usuario_id": "u-1"}
            return 200, {
                "data": [
                    {
                        "id": 10,
                        "usuario_id": "u-1",
                        "total": 259.98,
                        "estado": "entregado",
                        "detalle": [
                            {"producto_id": 123, "cantidad": 2, "precio_unitario": 129.99},
                        ],
                    }
                ]
            }

        if url.endswith("/productos/123"):
            return 200, {
                "id": 123,
                "nombre": "Teclado mecanico",
                "precio": 129.99,
                "stock": 8,
                "categoria_id": 1,
                "creado_en": "2026-04-24T12:34:56.789000",
            }

        raise AssertionError(f"URL no esperada: {url}")

    monkeypatch.setattr(historial_service, "_safe_get_json", fake_safe_get_json)

    response = client.get("/historial/u-1")
    assert response.status_code == 200

    payload = response.json()
    assert payload["usuario"]["nombre"] == "Ana"
    assert payload["pedidos"][0]["id"] == 10
    assert payload["pedidos"][0]["detalle"][0]["producto"]["id"] == 123


def test_historial_summary_calculates_totals(client, monkeypatch):
    async def fake_safe_get_json(_client, url: str, *, params=None):
        if url.endswith("/usuarios/u-2"):
            return 200, {"data": {"nombre": "Juan", "apellido": "Perez", "pais": "Perú"}}

        if url.endswith("/pedidos"):
            assert params == {"usuario_id": "u-2"}
            return 200, {"data": [{"id": 1, "total": 100.5}, {"id": 2, "total": "49.5"}]}

        raise AssertionError(f"URL no esperada: {url}")

    monkeypatch.setattr(historial_service, "_safe_get_json", fake_safe_get_json)

    response = client.get("/historial/resumen/u-2")
    assert response.status_code == 200
    assert response.json() == {
        "usuario_id": "u-2",
        "nro_pedidos": 2,
        "total_gastado": 150.0,
    }


def test_historial_returns_404_when_user_is_missing(client, monkeypatch):
    async def fake_safe_get_json(_client, url: str, *, params=None):
        if url.endswith("/usuarios/missing"):
            return 404, {"detail": "not found"}
        raise AssertionError(f"URL no esperada: {url}")

    monkeypatch.setattr(historial_service, "_safe_get_json", fake_safe_get_json)

    response = client.get("/historial/missing")
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuario no encontrado"