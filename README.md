# ShopCloud MS4 Historial

MS4 Historial is a FastAPI service that consolidates user history across the ShopCloud microservices. It exposes a health check plus endpoints to retrieve a full purchase history or a purchase summary for a given user.

## Features

- Health check endpoint at `/`
- Consolidated historial endpoint at `/historial/{usuario_id}`
- Summary endpoint at `/historial/resumen/{usuario_id}`
- Integration with upstream services for users, orders, and products

## Requirements

- Python 3.11 or newer
- `pip`

## Configuration

The service reads its settings from environment variables. You can also place them in a `.env` file.

| Variable | Default | Description |
| --- | --- | --- |
| `ENVIRONMENT` | `development` | Current runtime environment |
| `DEBUG` | `false` | Enables verbose logs when supported by the runtime |
| `MS1_URL` | `http://ms1-productos:8001` | Base URL for the products service |
| `MS2_URL` | `http://ms2-pedidos:8002` | Base URL for the orders service |
| `MS3_URL` | `http://ms3-usuarios:8003` | Base URL for the users service |
| `REQUEST_TIMEOUT_SECONDS` | `10.0` | Timeout for upstream HTTP requests |

## Running Locally

Install dependencies and start the API with Uvicorn:

```bash
pip install -r requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port 8004 --reload
```

The service will be available at `http://localhost:8004`.

## Docker

Build and run the container:

```bash
docker build -t shopcloud-ms4-historial .
docker run --rm -p 8004:8004 \
  -e MS1_URL=http://ms1-productos:8001 \
  -e MS2_URL=http://ms2-pedidos:8002 \
  -e MS3_URL=http://ms3-usuarios:8003 \
  shopcloud-ms4-historial
```

## API

### Health check

`GET /`

Response:

```json
{
  "status": "ok",
  "service": "ms4-historial"
}
```

### Get consolidated historial

`GET /historial/{usuario_id}`

Returns the user data, their orders, and product details for each order item. The service resolves data from the upstream MS1, MS2, and MS3 services.

Example:

```bash
curl http://localhost:8004/historial/u-1
```

### Get historial summary

`GET /historial/resumen/{usuario_id}`

Returns the number of orders and the total amount spent by the user.

Example:

```bash
curl http://localhost:8004/historial/resumen/u-1
```

## Error Handling

- `404` when the user does not exist in MS3
- `502` when an upstream service returns an unexpected response or cannot be reached

## Testing

Run the test suite with:

```bash
pytest
```

## API Specification

The OpenAPI document is available in [openapi.yml](openapi.yml).