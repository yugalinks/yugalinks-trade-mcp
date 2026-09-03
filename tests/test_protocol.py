import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_health_is_public(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "trade-mcp"


def test_discovery_metadata_is_public(client: TestClient) -> None:
    response = client.get("/.well-known/mcp.json")
    assert response.status_code == 200
    assert response.json()["url"].endswith("/mcp")


def test_initialize_and_tools_list(client: TestClient) -> None:
    initialize = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "0.1.0"},
            },
        },
    )
    tools = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    )

    assert initialize.status_code == 200
    assert initialize.json()["result"]["serverInfo"]["name"] == "Yugalinks Trade"
    assert tools.status_code == 200
    names = {tool["name"] for tool in tools.json()["result"]["tools"]}
    assert {
        "lookup_countries",
        "lookup_products",
        "get_global_trade",
        "get_country_trade",
        "get_product_trade",
        "get_corridor_trade",
        "get_lane_risk",
        "get_export_opportunities",
        "get_lane_page",
    } <= names


def test_mcp_response_has_no_internal_cache_headers(client: TestClient) -> None:
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}},
    )

    assert response.status_code == 200
    assert response.headers["x-ratelimit-limit"] == "60"
    assert response.headers["cache-control"] == "no-store"


def test_invalid_tool_input_is_customer_safe(client: TestClient) -> None:
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "get_country_trade",
                "arguments": {"country_iso3": "INDIA"},
            },
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["result"]["isError"] is True
    assert body["result"]["content"][0]["text"] == (
        "One or more tool inputs are invalid. Check the tool schema and try again."
    )
