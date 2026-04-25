from fastapi import FastAPI

from src.api.endpoints.historial import router as historial_router


app = FastAPI(
    title="ShopCloud - MS4 Historial",
    description="API de historial consolidado de usuario, pedidos y productos",
    version="1.0.0",
)

app.include_router(historial_router)


@app.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "ms4-historial"}
