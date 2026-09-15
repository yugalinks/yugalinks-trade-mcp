import json

import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

import app.main as main_module
from app.main import PROVENANCE, RateLimitMiddleware, app


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


def test_server_card_is_public(client: TestClient) -> None:
    response = client.get("/.well-known/mcp/server-card.json")
    assert response.status_code == 200
    assert response.json()["authentication"]["required"] is False
    assert {tool["name"] for tool in response.json()["tools"]} >= {
        "lookup_countries",
        "list_trade_datasets",
        "search_trade_datasets",
        "get_global_trade",
        "get_lane_risk",
    }


def test_provenance_identifies_the_public_dataset() -> None:
    assert PROVENANCE["dataset"] == "Balanced International Merchandise Trade Statistics (BIMTS)"
    assert PROVENANCE["edition"] == "HS 2017"
    assert PROVENANCE["dataflow_url"].startswith("https://sdmx.oecd.org/")
    assert PROVENANCE["terms_url"] == "https://www.oecd.org/termsandconditions/"


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
    assert initialize.json()["result"]["serverInfo"]["name"] == "Yugalinks Commerce Intelligence"
    assert tools.status_code == 200
    names = {tool["name"] for tool in tools.json()["result"]["tools"]}
    assert {
        "lookup_countries",
        "lookup_products",
        "list_trade_datasets",
        "search_trade_datasets",
        "get_global_trade",
        "get_country_trade",
        "get_product_trade",
        "get_corridor_trade",
        "get_lane_risk",
        "get_export_opportunities",
        "get_lane_page",
    } <= names


def test_tools_are_read_only_and_resources_are_available(client: TestClient) -> None:
    tools = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 20, "method": "tools/list", "params": {}},
    ).json()["result"]["tools"]
    assert len(tools) == 11
    for tool in tools:
        assert tool["annotations"]["readOnlyHint"] is True
        assert tool["annotations"]["destructiveHint"] is False
        assert tool["annotations"]["idempotentHint"] is True

    resources = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 21, "method": "resources/list", "params": {}},
    ).json()["result"]["resources"]
    assert {resource["uri"] for resource in resources} == {
        "yugalinks://data-sources",
        "yugalinks://methodology",
    }
    source = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 22,
            "method": "resources/read",
            "params": {"uri": "yugalinks://data-sources"},
        },
    ).json()
    assert "OECD" in json.dumps(source)


def test_mcp_response_has_no_internal_cache_headers(client: TestClient) -> None:
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}},
    )

    assert response.status_code == 200
    assert response.headers["x-ratelimit-limit"] == "60"
    assert response.headers["cache-control"] == "no-store"


def test_mcp_body_size_limit_is_enforced(client: TestClient) -> None:
    response = client.post(
        "/mcp",
        content=b"x" * 140_000,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413
    assert response.text == "Request body too large"


def test_mcp_cors_preflight_is_available(client: TestClient) -> None:
    response = client.options(
        "/mcp",
        headers={
            "Origin": "https://claude.ai",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://claude.ai"
    assert "POST" in response.headers["access-control-allow-methods"]

    blocked = client.options(
        "/mcp",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert blocked.status_code == 400
    assert "access-control-allow-origin" not in blocked.headers


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


def test_public_bounds_and_unknown_tools_are_rejected(client: TestClient) -> None:
    too_many_datasets = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 25,
            "method": "tools/call",
            "params": {
                "name": "search_trade_datasets",
                "arguments": {"dataset_keys": [f"dataset_{index}" for index in range(9)]},
            },
        },
    ).json()
    assert too_many_datasets["result"]["isError"] is True
    assert "invalid" in too_many_datasets["result"]["content"][0]["text"].lower()

    unknown_tool = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 26,
            "method": "tools/call",
            "params": {"name": "run_sql", "arguments": {"query": "SELECT 1"}},
        },
    ).json()
    assert unknown_tool["result"]["isError"] is True
    assert "select 1" not in json.dumps(unknown_tool).lower()
    assert "database" not in json.dumps(unknown_tool).lower()


def test_upstream_failure_is_customer_safe(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    async def failed_get_json(*args, **kwargs):
        raise RuntimeError("private database details must not escape")

    monkeypatch.setattr(main_module, "_get_json", failed_get_json)
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 23,
            "method": "tools/call",
            "params": {"name": "get_global_trade", "arguments": {"year": 2024, "limit": 1}},
        },
    )

    body = response.json()
    assert body["result"]["isError"] is True
    assert body["result"]["content"][0]["text"] == "Commerce data is temporarily unavailable."
    assert "private database" not in json.dumps(body).lower()


def test_rate_limit_returns_retry_headers() -> None:
    async def endpoint(_request):
        return JSONResponse({"ok": True})

    limited_app = Starlette(routes=[Route("/mcp", endpoint, methods=["POST"])])
    limited_app.add_middleware(
        RateLimitMiddleware,
        limit=2,
        window_seconds=60,
        redis_url="",
    )
    with TestClient(limited_app) as limited_client:
        first = limited_client.post("/mcp", json={})
        second = limited_client.post("/mcp", json={})
        third = limited_client.post("/mcp", json={})

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    assert third.headers["retry-after"] == "60"
    assert third.headers["cache-control"] == "no-store"


def test_dns_rebinding_host_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/mcp",
        headers={"host": "hostile.example"},
        json={"jsonrpc": "2.0", "id": 24, "method": "ping", "params": {}},
    )
    assert response.status_code == 421


def _call_tool(client: TestClient, name: str, arguments: dict | None = None) -> dict:
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["isError"] is False
    return json.loads(body["result"]["content"][0]["text"])


def test_trade_dataset_catalog_is_projected(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    async def fake_get_json(url: str, *, params=None, internal=False):
        assert internal is True
        assert url.endswith("/api/oecd/tables")
        return {
            "database": "private-db",
            "tables": [
                {
                    "key": "core_yearly_totals",
                    "table": "private_physical_table",
                    "columns": ["year", "global_trade_usd", "source_row_count"],
                    "available": True,
                }
            ],
        }

    monkeypatch.setattr(main_module, "_get_json", fake_get_json)
    payload = _call_tool(client, "list_trade_datasets")

    assert payload["dataset_count"] == 1
    assert payload["datasets"] == [
        {
            "key": "core_yearly_totals",
            "columns": ["year", "global_trade_usd"],
            "available": True,
        }
    ]
    assert "database" not in json.dumps(payload)
    assert "private_physical_table" not in json.dumps(payload)
    assert "source_row_count" not in json.dumps(payload)


def test_trade_dataset_search_is_bounded_and_projected(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    async def fake_get_json(url: str, *, params=None, internal=False):
        assert internal is True
        if url.endswith("/api/oecd/tables"):
            return {
                "tables": [
                    {
                        "key": "core_yearly_totals",
                        "table": "private_totals",
                        "columns": ["year", "global_trade_usd"],
                        "available": True,
                    },
                    {
                        "key": "risk_monitor_lane_all",
                        "table": "private_risk",
                        "columns": ["exporter_iso3", "importer_iso3"],
                        "available": True,
                    },
                ]
            }
        assert url.endswith("/api/oecd/search")
        assert params["tables"] == "core_yearly_totals,risk_monitor_lane_all"
        assert params["limit_per_table"] == 10
        return {
            "selected_tables": ["core_yearly_totals", "risk_monitor_lane_all"],
            "unavailable_tables": [],
            "results": {
                "core_yearly_totals": {
                    "table": "private_totals",
                    "rows": [{"year": 2024, "global_trade_usd": 1.0, "table": "leak"}],
                },
                "risk_monitor_lane_all": {
                    "table": "private_risk",
                    "rows": [{"exporter_iso3": "IND", "importer_iso3": "DEU"}],
                },
            },
        }

    monkeypatch.setattr(main_module, "_get_json", fake_get_json)
    payload = _call_tool(
        client,
        "search_trade_datasets",
        {
            "dataset_keys": ["core_yearly_totals", "risk_monitor_lane_all"],
            "year": 2024,
            "exporter_iso3": "IND",
        },
    )

    assert payload["selected_datasets"] == ["core_yearly_totals", "risk_monitor_lane_all"]
    assert payload["results"]["core_yearly_totals"]["rows"] == [
        {"year": 2024, "global_trade_usd": 1.0}
    ]
    assert "private_totals" not in json.dumps(payload)
    assert "private_risk" not in json.dumps(payload)


def test_hs_prefix_filters_cover_aggregate_contracts(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    async def fake_get_json(url: str, *, params=None, internal=False):
        assert internal is True
        if url.endswith("/api/oecd/tables"):
            return {
                "tables": [
                    {"key": "product_overview_hs2", "columns": ["hs2", "latest_trade_usd"], "available": True},
                    {"key": "product_overview_hs4", "columns": ["hs4", "latest_trade_usd"], "available": True},
                ]
            }
        assert url.endswith("/api/oecd/search")
        assert params["hs_code"] == "870899"
        return {
            "results": {
                "product_overview_hs2": {"rows": [{"hs2": "87"}]},
                "product_overview_hs4": {"rows": [{"hs4": "8708"}]},
            },
            "unavailable_tables": [],
        }

    monkeypatch.setattr(main_module, "_get_json", fake_get_json)
    payload = _call_tool(
        client,
        "search_trade_datasets",
        {
            "dataset_keys": ["product_overview_hs2", "product_overview_hs4"],
            "hs_code": "870899",
        },
    )

    assert payload["results"]["product_overview_hs2"]["rows"] == [
        {"hs2": "87", "latest_trade_usd": None}
    ]
    assert payload["results"]["product_overview_hs4"]["rows"] == [
        {"hs4": "8708", "latest_trade_usd": None}
    ]


def test_unfiltered_trade_dataset_search_is_rejected(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    async def fake_get_json(url: str, *, params=None, internal=False):
        assert url.endswith("/api/oecd/tables")
        if url.endswith("/api/oecd/search"):
            raise AssertionError("unfiltered search must not reach the upstream service")
        return {
            "tables": [
                {
                    "key": "risk_monitor_lane_all",
                    "columns": ["exporter_iso3", "importer_iso3", "hs_code"],
                    "available": True,
                }
            ]
        }

    monkeypatch.setattr(main_module, "_get_json", fake_get_json)
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 13,
            "method": "tools/call",
            "params": {
                "name": "search_trade_datasets",
                "arguments": {"dataset_keys": ["risk_monitor_lane_all"]},
            },
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["result"]["isError"] is True
    assert body["result"]["content"][0]["text"] == (
        "The dataset search could not be completed. Add an applicable filter and try again."
    )
