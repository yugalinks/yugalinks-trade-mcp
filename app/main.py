from __future__ import annotations

import hashlib
import logging
import os
import time
from typing import Annotated, Any

import httpx
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import Field
from redis.asyncio import Redis
from starlette.datastructures import MutableHeaders
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

VERSION = "0.1.0"
MAX_RESPONSE_BYTES = 512 * 1024

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("yugalinks.trade_mcp")


def _csv_env(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


TRADE_SERVICE_URL = os.getenv("TRADE_SERVICE_URL", "http://127.0.0.1:8000").rstrip("/")
TRADE_SERVICE_API_KEY = os.getenv("TRADE_SERVICE_API_KEY", "").strip()
PUBLIC_SITE_ORIGIN = os.getenv("PUBLIC_SITE_ORIGIN", "https://www.yugalinks.com").rstrip("/")
MCP_PUBLIC_URL = os.getenv("MCP_PUBLIC_URL", "https://mcp.yugalinks.com").rstrip("/")
RATE_LIMIT = max(1, _int_env("MCP_RATE_LIMIT", 60))
RATE_WINDOW_SECONDS = max(1, _int_env("MCP_RATE_WINDOW_SECONDS", 60))
MAX_BODY_BYTES = max(16 * 1024, _int_env("MCP_MAX_BODY_BYTES", 128 * 1024))
RATE_LIMIT_REDIS_URL = os.getenv("MCP_RATE_LIMIT_REDIS_URL", os.getenv("REDIS_URL", "")).strip()

ALLOWED_HOSTS = _csv_env(
    "MCP_ALLOWED_HOSTS",
    "localhost:*,127.0.0.1:*,[::1]:*,testserver,mcp.yugalinks.com,mcp.yugalinks.com:*",
)
ALLOWED_ORIGINS = _csv_env(
    "MCP_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8002,http://127.0.0.1:8002,"
    "https://www.yugalinks.com,https://claude.ai,https://chatgpt.com,https://www.chatgpt.com,"
    "https://copilot.microsoft.com,https://vscode.dev",
)

PROVENANCE = {
    "provider": "OECD",
    "dataset": "Balanced International Merchandise Trade Statistics (BIMTS)",
    "edition": "HS 2017",
    "coverage": "1995-2024 where available",
    "source_url": "https://data-explorer.oecd.org/",
    "dataflow_url": "https://sdmx.oecd.org/sti-public/rest/dataflow/OECD.SDD.TPS/DSD_BIMTS_6D@DF_BIMTS_HS2017_6D/1.0",
    "terms_url": "https://www.oecd.org/termsandconditions/",
    "notice": "Values may include OECD adjustments and balancing; see the BIMTS methodology.",
}

CountryIso3 = Annotated[
    str,
    Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Za-z]{3}$",
        description="Three-letter ISO country code, for example IND or DEU.",
    ),
]
HsCode = Annotated[
    str,
    Field(
        min_length=2,
        max_length=6,
        pattern=r"^\d{2,6}$",
        description="HS2, HS4, or HS6 product code.",
    ),
]
Hs6Code = Annotated[
    str,
    Field(min_length=6, max_length=6, pattern=r"^\d{6}$", description="Six-digit HS code."),
]
Year = Annotated[int | None, Field(ge=1995, le=2024, description="Reporting year from 1995 through 2024.")]
Limit = Annotated[int, Field(ge=1, le=100, description="Maximum number of rows to return.")]
Offset = Annotated[int, Field(ge=0, le=10000, description="Number of rows to skip.")]
SearchText = Annotated[str | None, Field(max_length=160, description="Optional text filter.")]


def _normalize_iso(value: str | None) -> str | None:
    return value.upper() if value else None


def _normalize_hs(value: str | None, exact_length: int | None = None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if exact_length is not None and len(cleaned) != exact_length:
        raise ValueError(f"HS code must contain exactly {exact_length} digits.")
    return cleaned


def _public_payload(payload: Any, *, indicator_note: str | None = None) -> dict[str, Any]:
    if isinstance(payload, dict):
        safe = {
            key: value
            for key, value in payload.items()
            if key not in {"database", "table", "table_key"}
        }
    else:
        safe = {"value": payload}
    provenance = {**PROVENANCE, "accessed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if indicator_note:
        provenance["indicator_note"] = indicator_note
    safe["provenance"] = provenance
    return safe


async def _get_json(url: str, *, params: dict[str, Any] | None = None, internal: bool = False) -> Any:
    headers = {"x-api-key": TRADE_SERVICE_API_KEY} if internal and TRADE_SERVICE_API_KEY else {}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(12.0, connect=3.0)) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            if len(response.content) > MAX_RESPONSE_BYTES:
                raise RuntimeError("The requested result is too large.")
            return response.json()
    except RuntimeError:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Upstream request failed: %s", url, exc_info=logger.isEnabledFor(logging.DEBUG))
        raise RuntimeError("Trade data is temporarily unavailable.") from exc


async def _trade_request(
    path: str,
    params: dict[str, Any],
    *,
    indicator_note: str | None = None,
) -> dict[str, Any]:
    payload = await _get_json(f"{TRADE_SERVICE_URL}{path}", params=params, internal=True)
    return _public_payload(payload, indicator_note=indicator_note)


def _params(**values: Any) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None and value != ""}


class PublicMCPServer(MCPServer):
    async def _handle_call_tool(self, ctx: Any, params: Any) -> CallToolResult:
        result = await super()._handle_call_tool(ctx, params)
        if getattr(result, "is_error", False):
            text = " ".join(
                item.text for item in result.content if isinstance(item, TextContent)
            )
            if "validation error" in text.lower() or "pydantic" in text.lower():
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="One or more tool inputs are invalid. Check the tool schema and try again.",
                        )
                    ],
                    isError=True,
                )
        return result


mcp = PublicMCPServer(
    "Yugalinks Trade",
    version=VERSION,
    title="Yugalinks Trade Intelligence",
    description="Read-only access to reported trade statistics and lane-risk research.",
    instructions=(
        "Use these tools for reported merchandise trade research. Responses include source and coverage "
        "context. Calculated indicators are research aids, not forecasts or guarantees."
    ),
    website_url=PUBLIC_SITE_ORIGIN,
    log_level=os.getenv("LOG_LEVEL", "INFO"),
)
READ_ONLY_TOOL = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


@mcp.tool(annotations=READ_ONLY_TOOL)
async def lookup_countries(
    q: SearchText = None,
    country_iso3: CountryIso3 | None = None,
    limit: Limit = 50,
) -> dict[str, Any]:
    """Find country names and ISO3 codes used in Yugalinks trade data."""
    return await _trade_request(
        "/api/oecd/lookup/countries",
        _params(q=q, country_iso3=_normalize_iso(country_iso3), limit=limit),
    )


@mcp.tool(annotations=READ_ONLY_TOOL)
async def lookup_products(
    q: SearchText = None,
    hs_code: HsCode | None = None,
    limit: Limit = 50,
    offset: Offset = 0,
) -> dict[str, Any]:
    """Find HS product codes and descriptions used in Yugalinks trade data."""
    return await _trade_request(
        "/api/oecd/lookup/products",
        _params(q=q, hs_code=_normalize_hs(hs_code), limit=limit, offset=offset),
    )


@mcp.tool(annotations=READ_ONLY_TOOL)
async def get_global_trade(
    year: Year = 2024,
    limit: Limit = 50,
    offset: Offset = 0,
) -> dict[str, Any]:
    """Return reported global merchandise trade totals for a year."""
    return await _trade_request(
        "/api/oecd/core/yearly-totals",
        _params(year=year, limit=limit, offset=offset),
    )


@mcp.tool(annotations=READ_ONLY_TOOL)
async def get_country_trade(
    country_iso3: CountryIso3,
    year: Year = None,
    limit: Limit = 50,
    offset: Offset = 0,
) -> dict[str, Any]:
    """Return reported yearly exports, imports, balance, and growth for a country."""
    return await _trade_request(
        "/api/oecd/core/country-year",
        _params(country_iso3=_normalize_iso(country_iso3), year=year, limit=limit, offset=offset),
    )


@mcp.tool(annotations=READ_ONLY_TOOL)
async def get_product_trade(
    hs_code: HsCode,
    year: Year = None,
    limit: Limit = 50,
    offset: Offset = 0,
) -> dict[str, Any]:
    """Return reported yearly global trade and growth for an HS2, HS4, or HS6 product."""
    return await _trade_request(
        "/api/oecd/core/product-year",
        _params(hs_code=_normalize_hs(hs_code), year=year, limit=limit, offset=offset),
    )


@mcp.tool(annotations=READ_ONLY_TOOL)
async def get_corridor_trade(
    exporter_iso3: CountryIso3 | None = None,
    importer_iso3: CountryIso3 | None = None,
    year: Year = None,
    limit: Limit = 50,
    offset: Offset = 0,
) -> dict[str, Any]:
    """Return reported yearly trade values between exporter and importer countries."""
    return await _trade_request(
        "/api/oecd/core/corridor-year",
        _params(
            exporter_iso3=_normalize_iso(exporter_iso3),
            importer_iso3=_normalize_iso(importer_iso3),
            year=year,
            limit=limit,
            offset=offset,
        ),
    )


@mcp.tool(annotations=READ_ONLY_TOOL)
async def get_lane_risk(
    exporter_iso3: CountryIso3 | None = None,
    importer_iso3: CountryIso3 | None = None,
    hs_code: Hs6Code | None = None,
    hs_chapter: Annotated[str | None, Field(pattern=r"^\d{2}$", description="Two-digit HS chapter.")] = None,
    attention_level: Annotated[str | None, Field(max_length=120)] = None,
    risk_driver: Annotated[str | None, Field(max_length=160)] = None,
    min_trade_usd: Annotated[float | None, Field(ge=0)] = None,
    current_only: bool = True,
    q: SearchText = None,
    limit: Limit = 50,
    offset: Offset = 0,
) -> dict[str, Any]:
    """Return reported lane-risk observations for country and product filters."""
    return await _trade_request(
        "/api/oecd/risk/monitor/lanes",
        _params(
            exporter_iso3=_normalize_iso(exporter_iso3),
            importer_iso3=_normalize_iso(importer_iso3),
            hs_code=_normalize_hs(hs_code, 6),
            hs_chapter=hs_chapter,
            attention_level=attention_level,
            risk_driver=risk_driver,
            min_trade_usd=min_trade_usd,
            current_only=current_only,
            q=q,
            limit=limit,
            offset=offset,
        ),
    )


@mcp.tool(annotations=READ_ONLY_TOOL)
async def get_export_opportunities(
    exporter_iso3: CountryIso3 | None = None,
    importer_iso3: CountryIso3 | None = None,
    hs_code: HsCode | None = None,
    year: Year = None,
    limit: Limit = 50,
    offset: Offset = 0,
) -> dict[str, Any]:
    """Return bounded export-opportunity indicators for country and product filters."""
    return await _trade_request(
        "/api/oecd/score/export-opportunity",
        _params(
            exporter_iso3=_normalize_iso(exporter_iso3),
            importer_iso3=_normalize_iso(importer_iso3),
            hs_code=_normalize_hs(hs_code),
            year=year,
            limit=limit,
            offset=offset,
        ),
        indicator_note="Calculated opportunity indicators based on reported trade observations.",
    )


@mcp.tool(annotations=READ_ONLY_TOOL)
async def get_lane_page(
    exporter_iso3: CountryIso3,
    importer_iso3: CountryIso3,
    hs_code: Hs6Code,
) -> dict[str, Any]:
    """Read the public machine-readable page for one exporter-importer HS6 lane-risk record."""
    exporter = _normalize_iso(exporter_iso3)
    importer = _normalize_iso(importer_iso3)
    code = _normalize_hs(hs_code, 6)
    route = f"/trade/lane-risk/{exporter.lower()}-{importer.lower()}-{code}"
    url = f"{PUBLIC_SITE_ORIGIN}{route}/index.json"
    payload = await _get_json(url)
    result = _public_payload(payload)
    result["url"] = f"{PUBLIC_SITE_ORIGIN}{route}"
    result["source_url"] = result["url"]
    return result


@mcp.resource("yugalinks://data-sources")
def data_sources() -> str:
    """Describe the providers and coverage represented by the public tools."""
    return (
        "Yugalinks public MCP tools primarily expose OECD bilateral merchandise trade statistics "
        "covering 1995-2024 where observations are available. See "
        f"{PUBLIC_SITE_ORIGIN}/data-sources for provider details."
    )


@mcp.resource("yugalinks://methodology")
def methodology() -> str:
    """Describe how users can review definitions and indicator limitations."""
    return (
        "Review definitions, formulas, coverage boundaries, and indicator limitations at "
        f"{PUBLIC_SITE_ORIGIN}/methodology and {PUBLIC_SITE_ORIGIN}/data-coverage."
    )


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> Response:
    return JSONResponse({"status": "ok", "service": "trade-mcp", "version": VERSION})


@mcp.custom_route("/", methods=["GET"])
async def service_metadata(_: Request) -> Response:
    return JSONResponse(
        {
            "name": "Yugalinks Trade MCP",
            "version": VERSION,
            "endpoint": f"{MCP_PUBLIC_URL}/mcp",
            "transport": "streamable-http",
            "authentication": "none for read-only public tools",
            "documentation": f"{PUBLIC_SITE_ORIGIN}/docs/mcp",
        }
    )


@mcp.custom_route("/.well-known/mcp.json", methods=["GET"])
async def discovery_metadata(_: Request) -> Response:
    return JSONResponse(
        {
            "name": "Yugalinks Trade MCP",
            "description": "Free read-only trade statistics and lane-risk research for AI assistants.",
            "url": f"{MCP_PUBLIC_URL}/mcp",
            "transport": "streamable-http",
            "documentation": f"{PUBLIC_SITE_ORIGIN}/docs/mcp",
        }
    )


class RateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        limit: int,
        window_seconds: int,
        redis_url: str,
    ) -> None:
        self.app = app
        self.limit = limit
        self.window_seconds = window_seconds
        self.redis = Redis.from_url(redis_url, decode_responses=True) if redis_url else None
        self.memory: dict[str, tuple[int, float]] = {}
        self.redis_warning_logged = False

    @staticmethod
    def _identity(scope: Scope) -> str:
        headers = {key.decode().lower(): value.decode() for key, value in scope.get("headers", [])}
        forwarded = headers.get("cf-connecting-ip") or headers.get("x-forwarded-for", "").split(",")[0].strip()
        client = scope.get("client")
        ip = forwarded or (client[0] if client else "unknown")
        return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:32]

    async def _consume(self, identity: str) -> tuple[bool, int, int]:
        now = time.time()
        bucket = int(now // self.window_seconds)
        reset_at = (bucket + 1) * self.window_seconds
        if self.redis:
            try:
                key = f"trade-mcp:rate:{bucket}:{identity}"
                count = int(await self.redis.incr(key))
                if count == 1:
                    await self.redis.expire(key, self.window_seconds + 10)
                return count <= self.limit, count, int(reset_at)
            except Exception:
                if not self.redis_warning_logged:
                    logger.warning("MCP Redis rate limiting unavailable; using process-local fallback.")
                    self.redis_warning_logged = True
                self.redis = None

        existing = self.memory.get(identity)
        if existing is None or existing[1] <= now:
            count, entry_reset = 1, reset_at
        else:
            count, entry_reset = existing[0] + 1, existing[1]
        self.memory[identity] = (count, entry_reset)
        if len(self.memory) > 5000:
            self.memory = {key: value for key, value in self.memory.items() if value[1] > now}
        return count <= self.limit, count, int(entry_reset)

    @staticmethod
    def _headers(limit: int, count: int, reset_at: int) -> dict[str, str]:
        return {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(max(0, limit - count)),
            "X-RateLimit-Reset": str(reset_at),
        }

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("path") != "/mcp":
            await self.app(scope, receive, send)
            return

        allowed, count, reset_at = await self._consume(self._identity(scope))
        headers = self._headers(self.limit, count, reset_at)
        if not allowed:
            headers["Retry-After"] = str(self.window_seconds)
            headers["Access-Control-Allow-Origin"] = "*"
            headers["Cache-Control"] = "no-store"
            response = JSONResponse({"error": "Public MCP rate limit exceeded."}, status_code=429, headers=headers)
            await response(scope, receive, send)
            return

        async def send_with_rate_headers(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                mutable = MutableHeaders(scope=message)
                for key, value in headers.items():
                    mutable[key] = value
                mutable["Cache-Control"] = "no-store"
            await send(message)

        await self.app(scope, receive, send_with_rate_headers)


transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=ALLOWED_HOSTS,
    allowed_origins=ALLOWED_ORIGINS,
)

app = mcp.streamable_http_app(
    json_response=True,
    stateless_http=True,
    max_request_body_size=MAX_BODY_BYTES,
    transport_security=transport_security,
)
app.add_middleware(
    RateLimitMiddleware,
    limit=RATE_LIMIT,
    window_seconds=RATE_WINDOW_SECONDS,
    redis_url=RATE_LIMIT_REDIS_URL,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Last-Event-ID",
        "Mcp-Method",
        "Mcp-Name",
        "Mcp-Protocol-Version",
        "Mcp-Session-Id",
    ],
    expose_headers=["Mcp-Session-Id", "Mcp-Protocol-Version", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)
