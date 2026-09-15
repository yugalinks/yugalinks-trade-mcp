# Yugalinks Commerce Intelligence MCP

Public, read-only Model Context Protocol service for Yugalinks cross-border commerce statistics and lane-risk research.

The service uses the official MCP Python SDK and Streamable HTTP. It calls the private data adapter using a server-side API key and never exposes SQL, table names, credentials, or unrestricted proxy access.

Public integration documentation: `https://www.yugalinks.com/docs/mcp`.

## Architecture Boundary

`trade-mcp` is an independently deployable service. It does not require the Next.js webapp, authentication, or the AI service to run.

The MCP service deliberately uses `trade-service` as its private data adapter. This keeps ClickHouse credentials and query logic out of the public MCP boundary while allowing the MCP image, rate limits, deployment, and public URL to be managed separately. Making MCP query ClickHouse directly would be a separate architecture with duplicated query logic and a larger public-data security surface.

## Tools

- `lookup_countries`: find country names and ISO3 codes.
- `lookup_products`: find HS codes and product descriptions.
- `list_trade_datasets`: list all approved commerce-data dataset contracts and their public columns.
- `search_trade_datasets`: search one to eight named dataset contracts with bounded common filters.
- `get_global_trade`: retrieve global yearly merchandise flows.
- `get_country_trade`: retrieve country imports, exports, balance, and growth.
- `get_product_trade`: retrieve product-level yearly merchandise flows.
- `get_corridor_trade`: retrieve exporter-importer goods corridors.
- `get_lane_risk`: retrieve bounded lane-risk observations.
- `get_export_opportunities`: retrieve bounded calculated opportunity indicators.
- `get_lane_page`: retrieve one public machine-readable lane page with its source URL.

The public catalog currently mirrors all configured commerce-data contracts from the private adapter. A search must name one to eight keys returned by `list_trade_datasets`, include a year, country, product, corridor, or text filter applicable to each selected dataset, return at most 25 rows per dataset, and never expose physical storage identifiers. The `hs_code` filter accepts HS2, HS4, or HS6 values; detailed HS requests are safely reduced to the matching HS2/HS4 prefix for aggregate contracts. The MCP boundary remains tool-based rather than an arbitrary SQL or table browser; adding a contract requires typed filters, bounded pagination, safe payload projection, provenance, and review.

## Local Runtime

Start the normal development services first, then run the MCP service:

```bash
docker compose --profile dev up -d trade-service redis trade-mcp
```

The local endpoint is `http://localhost:8002/mcp`.

On this VM, clients on the same private network can use `http://10.1.2.4:8002/mcp`. The development Compose profile explicitly allows that VM address; override `MCP_ALLOWED_HOSTS` when using a different local address. Discovery defaults to the localhost URL, so a remote private-network client should use the VM URL directly or set `MCP_PUBLIC_URL` for its environment.

Required runtime variables when calling the trade-service:

- `TRADE_SERVICE_URL`
- `TRADE_SERVICE_API_KEY`

The root workspace `.env` must provide the private trade-service variables used by Compose, including `CLICKHOUSE_PASSWORD` and `TRADE_SERVICE_API_KEY`. Do not put those values in this README or in a client configuration file.

Optional variables:

- `MCP_RATE_LIMIT_REDIS_URL` or `REDIS_URL`
- `MCP_PUBLIC_URL`
- `PUBLIC_SITE_ORIGIN`
- `MCP_ALLOWED_HOSTS`
- `MCP_ALLOWED_ORIGINS`
- `MCP_RATE_LIMIT` (default `60` per window)
- `MCP_RATE_WINDOW_SECONDS` (default `60`)
- `MCP_MAX_BODY_BYTES` (default `131072`)

The public commerce-data search is deliberately bounded to eight datasets and 25 rows per dataset. For example, first call `list_trade_datasets`, then call `search_trade_datasets` with `dataset_keys` such as `core_product_year` or `risk_monitor_lane_all` and a product, country, or year filter.

## Tests

Run the protocol and projection tests in a local virtual environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

Run the live release preflight against the local service or a deployed HTTPS endpoint:

```bash
python3 preflight.py --base-url http://127.0.0.1:8002
python3 preflight.py --base-url https://commerce-mcp.yugalinks.com
```

The preflight verifies discovery metadata, MCP initialization, all 11 tools, read-only annotations, resources, the complete 43-dataset catalog, a bounded query probe for every catalog contract, representative core/risk/opportunity queries, provenance and payload projection, and route-specific lane-page semantics. It must pass against the production hostname before directory submission.

Check the local service:

```bash
curl http://localhost:8002/health
curl http://localhost:8002/.well-known/mcp.json
curl http://localhost:8002/.well-known/mcp/server-card.json
```

The MCP endpoint is `http://localhost:8002/mcp`. A local MCP client on the same machine can use a Streamable HTTP entry similar to:

```json
{
  "mcpServers": {
    "yugalinks-commerce-local": {
      "url": "http://127.0.0.1:8002/mcp"
    }
  }
}
```

Cloud-hosted clients cannot reach `localhost`. They need the production HTTPS endpoint after DNS, tunnel routing, deployment, and attribution/licensing review are complete.

## Production Shape

The intended production URL is `https://commerce-mcp.yugalinks.com/mcp`.

Cloudflare terminates the public connection and routes the existing tunnel to the `trade-mcp` ClusterIP service. The protected repository workflow manages the tunnel ConfigMap and canonical DNS record; the service then calls `trade-service.trade-service.svc.cluster.local:8000` over the cluster network.

The service is intentionally stateless so multiple AKS replicas do not require session affinity.
