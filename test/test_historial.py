from __future__ import annotations

from src.crud import historial as historial_service


def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ms4-historial"}


def test_historial_endpoint_consolidates_upstream_data(client, monkeypatch):
    async def fake_safe_get_json(_client, url: str, *, params=None):
        if url.endswith("/usuarios/u-1"):
            return 200, {
                "status": "success",
                "data": {
                    "usuario": {
                        "_id": "u-1",
                        "nombre": "Ana",
                        "apellido": "Lopez",
                        "direccion": {"pais": "Perú"},
                    }
                },
            }

        if url.endswith("/pedidos"):
            assert params == {"usuario_id": "u-1"}
            return 200, {
                "data": {
                    "pedidos": [
                        {
                            "id": 10,
                            "usuario_id": "u-1",
                            "total": 259.98,
                            "estado": "entregado",
                        }
                    ]
                },
            }

        if url.endswith("/pedidos/10"):
            return 200, {
                "data": {
                    "pedido": {
                        "detalle_pedidos": [
                            {"producto_id": 123, "cantidad": 2, "precio_unitario": 129.99},
                            {"producto_id": 123, "cantidad": 1, "precio_unitario": 129.99},
                            {"producto_id": 456, "cantidad": 1, "precio_unitario": 39.99},
                        ]
                    }
                },
            }

        if url.endswith("/productos/123"):
            return 200, {
                "data": {
                    "id": 123,
                    "nombre": "Teclado mecanico",
                    "precio": 129.99,
                    "stock": 8,
                    "categoria_id": 1,
                    "creado_en": "2026-04-24T12:34:56.789000",
                }
            }

        if url.endswith("/productos/456"):
            return 200, {
                "producto": {
                    "id": 456,
                    "nombre": "Mouse ergonomico",
                    "precio": 39.99,
                    "stock": 16,
                    "categoria_id": 1,
                    "creado_en": "2026-04-24T12:34:56.789000",
                }
            }

        raise AssertionError(f"URL no esperada: {url}")

    monkeypatch.setattr(historial_service, "_safe_get_json", fake_safe_get_json)

    response = client.get("/historial/u-1")
    assert response.status_code == 200

    payload = response.json()
    assert payload["usuario"] == {"id": "u-1", "nombre": "Ana", "apellido": "Lopez", "pais": "Perú"}
    assert payload["pedidos"][0]["id"] == 10
    assert payload["pedidos"][0]["detalle"][0]["producto"]["id"] == 123
    assert payload["pedidos"][0]["detalle"][1]["producto"]["id"] == 123
    assert payload["pedidos"][0]["detalle"][2]["producto"]["id"] == 456


def test_historial_endpoint_returns_502_for_malformed_usuario_payload(client, monkeypatch):
    async def fake_safe_get_json(_client, url: str, *, params=None):
        if url.endswith("/usuarios/bad"):
            return 200, {"data": ["invalid", "payload"]}

        raise AssertionError(f"URL no esperada: {url}")

    monkeypatch.setattr(historial_service, "_safe_get_json", fake_safe_get_json)

    response = client.get("/historial/bad")
    assert response.status_code == 502
    assert response.json()["detail"] == "MS3 devolvió un formato inesperado de usuario"


def test_historial_summary_calculates_totals(client, monkeypatch):
    async def fake_safe_get_json(_client, url: str, *, params=None):
        if url.endswith("/usuarios/u-2"):
            return 200, {"data": {"nombre": "Juan", "apellido": "Perez", "pais": "Perú"}}

        if url.endswith("/pedidos"):
            assert params == {"usuario_id": "u-2"}
            return 200, {"data": [{"id": 1, "total": 100.5}, {"id": 2, "total": "49.5"}, {"id": 3, "total": "invalid"}]}

        raise AssertionError(f"URL no esperada: {url}")

    monkeypatch.setattr(historial_service, "_safe_get_json", fake_safe_get_json)

    response = client.get("/historial/resumen/u-2")
    assert response.status_code == 200
    assert response.json() == {
        "usuario_id": "u-2",
        "nro_pedidos": 3,
        "total_gastado": 150.0,
    }


def test_extract_helpers_support_wrapped_payloads():
    usuario = historial_service._extract_usuario(
        {"data": {"usuario": {"_id": "u-9", "nombre": "Marta", "apellido": "Diaz", "direccion": {"pais": "Chile"}}}}
    )
    pedidos = historial_service._extract_pedidos({"data": {"pedidos": [{"id": 1}, {"id": 2}]}})
    detalle = historial_service._extract_detalle({"detalle_pedidos": [{"producto_id": 7, "cantidad": 1, "precio_unitario": 5.0}]})

    assert usuario == {
        "_id": "u-9",
        "nombre": "Marta",
        "apellido": "Diaz",
        "direccion": {"pais": "Chile"},
        "pais": "Chile",
        "id": "u-9",
    }
    assert pedidos == [{"id": 1}, {"id": 2}]
    assert detalle == [{"producto_id": 7, "cantidad": 1, "precio_unitario": 5.0}]


def test_historial_returns_404_when_user_is_missing(client, monkeypatch):
    async def fake_safe_get_json(_client, url: str, *, params=None):
        if url.endswith("/usuarios/missing"):
            return 404, {"detail": "not found"}
        raise AssertionError(f"URL no esperada: {url}")

    monkeypatch.setattr(historial_service, "_safe_get_json", fake_safe_get_json)

    response = client.get("/historial/missing")
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuario no encontrado"