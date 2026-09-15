#!/usr/bin/env python3
"""Run the public MCP release checks against a local or deployed endpoint."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

EXPECTED_TOOLS = {
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
}
INTERNAL_KEYS = {"database", "table", "table_key"}
FORBIDDEN_MARKERS = ("trade_gold", "trade_intelligence", "private_physical")


class PreflightFailure(RuntimeError):
    pass


def request_json(url: str, payload: dict[str, Any] | None = None) -> Any:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json, text/event-stream"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method="POST" if body else "GET")
    try:
        with urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise PreflightFailure(f"{url} returned HTTP {response.status}")
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise PreflightFailure(f"{url} returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise PreflightFailure(f"Could not reach {url}: {exc.reason}") from exc


def rpc(base_url: str, method: str, params: dict[str, Any] | None = None, request_id: int = 1) -> dict[str, Any]:
    response = request_json(
        f"{base_url}/mcp",
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        },
    )
    if "error" in response:
        raise PreflightFailure(f"MCP {method} failed: {response['error']}")
    return response


def tool_call(base_url: str, name: str, arguments: dict[str, Any], request_id: int) -> Any:
    response = rpc(
        base_url,
        "tools/call",
        {"name": name, "arguments": arguments},
        request_id,
    )
    result = response.get("result") or {}
    if result.get("isError"):
        text = " ".join(
            item.get("text", "") for item in result.get("content", []) if isinstance(item, dict)
        )
        raise PreflightFailure(f"Tool {name} returned an error: {text}")
    content = result.get("content") or []
    text = next((item.get("text") for item in content if item.get("type") == "text"), None)
    if not isinstance(text, str):
        raise PreflightFailure(f"Tool {name} returned no text content")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise PreflightFailure(f"Tool {name} returned non-JSON text") from exc


def walk(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


def assert_public_payload(payload: Any, label: str) -> None:
    serialized = json.dumps(payload, ensure_ascii=True)
    for key, _ in walk(payload):
        if key in INTERNAL_KEYS:
            raise PreflightFailure(f"{label} exposes internal response key: {key}")
    for marker in FORBIDDEN_MARKERS:
        if marker in serialized:
            raise PreflightFailure(f"{label} exposes forbidden marker: {marker}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PreflightFailure(message)


def probe_dataset_contracts(base_url: str, datasets: list[dict[str, Any]]) -> None:
    """Exercise every catalog contract with one bounded, route-safe filter batch."""
    probe_arguments = {
        "year": 2024,
        "exporter_iso3": "IND",
        "importer_iso3": "DEU",
        "country_iso3": "IND",
        "hs_code": "870899",
        "limit": 1,
    }
    keys = [str(dataset.get("key")) for dataset in datasets]
    for batch_start in range(0, len(keys), 8):
        batch = keys[batch_start : batch_start + 8]
        payload = tool_call(
            base_url,
            "search_trade_datasets",
            {"dataset_keys": batch, **probe_arguments},
            40 + batch_start // 8,
        )
        assert_public_payload(payload, "dataset contract probe")
        results = payload.get("results", {})
        require(isinstance(results, dict), "Dataset contract probe returned no result map")
        unavailable = payload.get("unavailable_datasets", [])
        require(not unavailable, f"Dataset contract probe found unavailable datasets: {unavailable}")
        for dataset in datasets[batch_start : batch_start + 8]:
            key = dataset["key"]
            result = results.get(key)
            require(isinstance(result, dict), f"Dataset contract probe omitted {key}")
            require(result.get("columns") == dataset.get("columns"), f"Dataset columns changed for {key}")
            rows = result.get("rows", [])
            require(isinstance(rows, list) and len(rows) <= 1, f"Dataset probe exceeded limit for {key}")
            declared_columns = set(dataset.get("columns", []))
            for row in rows:
                require(isinstance(row, dict), f"Dataset probe returned a non-object row for {key}")
                require(set(row) == declared_columns, f"Dataset row columns changed for {key}")
    print(f"[ok] dataset contracts: {len(keys)} datasets probed")


def run(base_url: str, expected_dataset_count: int) -> None:
    base_url = base_url.rstrip("/")
    health = request_json(f"{base_url}/health")
    require(health.get("status") == "ok", "Health check did not return status=ok")
    print(f"[ok] health: {health.get('version')}")

    discovery = request_json(f"{base_url}/.well-known/mcp.json")
    require(discovery.get("url", "").endswith("/mcp"), "Discovery metadata has no MCP endpoint")
    print("[ok] discovery metadata")

    card = request_json(f"{base_url}/.well-known/mcp/server-card.json")
    card_tools = {tool.get("name") for tool in card.get("tools", [])}
    require(card.get("authentication", {}).get("required") is False, "Server card requires authentication")
    require(card_tools == EXPECTED_TOOLS, "Server card tool set differs from the release contract")
    print(f"[ok] server card: {len(card_tools)} tools")

    initialize = rpc(
        base_url,
        "initialize",
        {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "yugalinks-preflight", "version": "1.0.0"},
        },
        2,
    )
    require(
        initialize.get("result", {}).get("serverInfo", {}).get("name") == "Yugalinks Commerce Intelligence",
        "Initialize returned the wrong server",
    )
    print(f"[ok] initialize: {initialize['result'].get('protocolVersion')}")

    tools = rpc(base_url, "tools/list", {}, 3).get("result", {}).get("tools", [])
    tool_names = {tool.get("name") for tool in tools}
    require(tool_names == EXPECTED_TOOLS, "tools/list differs from the server card")
    for tool in tools:
        annotations = tool.get("annotations", {})
        require(annotations.get("readOnlyHint") is True, f"{tool['name']} is not read-only")
        require(annotations.get("destructiveHint") is False, f"{tool['name']} is marked destructive")
    print("[ok] tools/list schemas and read-only annotations")

    resources = rpc(base_url, "resources/list", {}, 4).get("result", {}).get("resources", [])
    resource_uris = {resource.get("uri") for resource in resources}
    require({"yugalinks://data-sources", "yugalinks://methodology"} <= resource_uris, "Required resources are missing")
    print("[ok] resources/list")

    sources = rpc(base_url, "resources/read", {"uri": "yugalinks://data-sources"}, 5)
    source_text = json.dumps(sources)
    require("OECD" in source_text and "1995-2024" in source_text, "Data-source resource is incomplete")
    print("[ok] resources/read")

    catalog = tool_call(base_url, "list_trade_datasets", {}, 6)
    assert_public_payload(catalog, "dataset catalog")
    dataset_count = int(catalog.get("dataset_count", 0))
    available_count = int(catalog.get("available_count", 0))
    require(dataset_count >= expected_dataset_count, f"Expected at least {expected_dataset_count} datasets, got {dataset_count}")
    require(available_count == dataset_count, "One or more approved datasets are unavailable")
    print(f"[ok] dataset catalog: {dataset_count} datasets, all available")
    probe_dataset_contracts(base_url, catalog.get("datasets", []))

    cases = [
        ("lookup_countries", {"q": "India", "limit": 2}),
        ("lookup_products", {"hs_code": "870899", "limit": 2}),
        ("get_global_trade", {"year": 2024, "limit": 2}),
        ("get_country_trade", {"country_iso3": "IND", "year": 2024, "limit": 2}),
        ("get_product_trade", {"hs_code": "870899", "year": 2024, "limit": 2}),
        ("get_corridor_trade", {"exporter_iso3": "IND", "importer_iso3": "DEU", "year": 2024, "limit": 2}),
        ("get_lane_risk", {"exporter_iso3": "IND", "importer_iso3": "DEU", "hs_code": "870899", "limit": 2}),
        ("get_export_opportunities", {"exporter_iso3": "IND", "importer_iso3": "DEU", "hs_code": "870899", "year": 2024, "limit": 2}),
        ("get_lane_page", {"exporter_iso3": "IND", "importer_iso3": "DEU", "hs_code": "870899"}),
        ("search_trade_datasets", {"dataset_keys": ["core_product_year"], "hs_code": "870899", "year": 2024, "limit": 2}),
        ("search_trade_datasets", {"dataset_keys": ["risk_monitor_lane_all"], "exporter_iso3": "IND", "hs_code": "870899", "limit": 2}),
        ("search_trade_datasets", {"dataset_keys": ["serve_opportunity_real"], "exporter_iso3": "IND", "importer_iso3": "DEU", "hs_code": "870899", "limit": 2}),
    ]
    for index, (name, arguments) in enumerate(cases, start=10):
        payload = tool_call(base_url, name, arguments, index)
        assert_public_payload(payload, name)
        require("provenance" in payload, f"{name} did not return provenance")
        print(f"[ok] tool: {name}")

    lane_payload = tool_call(base_url, "get_lane_page", {"exporter_iso3": "IND", "importer_iso3": "DEU", "hs_code": "870899"}, 30)
    seo_title = str(lane_payload.get("seo", {}).get("title", ""))
    canonical = str(lane_payload.get("seo", {}).get("canonical", ""))
    require("India" in seo_title and "Germany" in seo_title and "United Kingdom" not in seo_title, "Lane page SEO title is not normalized to the requested route")
    require("ind-deu-870899" in canonical, "Lane page canonical does not match the requested route")
    print("[ok] lane-page route semantics")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8002", help="MCP service origin")
    parser.add_argument("--expected-dataset-count", type=int, default=43)
    args = parser.parse_args()
    try:
        run(args.base_url, args.expected_dataset_count)
    except PreflightFailure as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 1
    print("Preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
