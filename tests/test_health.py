from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "database" in data


async def test_health_response_schema(client: AsyncClient) -> None:
    response = await client.get("/health")
    data = response.json()
    assert set(data.keys()) == {"status", "database", "version"}


async def test_health_database_status_is_valid(client: AsyncClient) -> None:
    response = await client.get("/health")
    data = response.json()
    assert data["database"] in ("ok", "error", "not_configured")
