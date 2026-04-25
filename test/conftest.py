from __future__ import annotations

import asyncio

import httpx
import pytest

from src.main import app


class SyncASGIClient:
    def __init__(self, asgi_app):
        self._app = asgi_app

    def request(self, method: str, url: str, **kwargs):
        async def _request():
            transport = httpx.ASGITransport(app=self._app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                return await client.request(method, url, **kwargs)

        return asyncio.run(_request())

    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)


@pytest.fixture()
def client() -> SyncASGIClient:
    return SyncASGIClient(app)