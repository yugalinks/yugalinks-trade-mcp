# Yugalinks Trade MCP

Public, read-only Model Context Protocol service for Yugalinks trade statistics and lane-risk research.

The service uses the official MCP Python SDK and Streamable HTTP. It calls the private trade-service using a server-side API key and never exposes SQL, table names, credentials, or unrestricted proxy access.

## Tools

- `lookup_countries`: find country names and ISO3 codes.
- `lookup_products`: find HS codes and product descriptions.
- `get_global_trade`: retrieve global yearly trade totals.
- `get_country_trade`: retrieve country exports, imports, balance, and growth.
- `get_product_trade`: retrieve product-level yearly trade.
- `get_corridor_trade`: retrieve exporter-importer trade corridors.
- `get_lane_risk`: retrieve bounded lane-risk observations.
- `get_export_opportunities`: retrieve bounded calculated opportunity indicators.
- `get_lane_page`: retrieve one public machine-readable lane page with its source URL.

## Local Runtime

Start the normal development services first, then run the MCP service:

```bash
docker compose --profile dev up -d trade-service redis trade-mcp
```

The local endpoint is `http://localhost:8002/mcp`.

Required runtime variables when calling the trade-service:

- `TRADE_SERVICE_URL`
- `TRADE_SERVICE_API_KEY`

Optional variables:

- `MCP_RATE_LIMIT_REDIS_URL` or `REDIS_URL`
- `MCP_PUBLIC_URL`
- `PUBLIC_SITE_ORIGIN`
- `MCP_ALLOWED_HOSTS`
- `MCP_ALLOWED_ORIGINS`
- `MCP_RATE_LIMIT` (default `60` per window)
- `MCP_RATE_WINDOW_SECONDS` (default `60`)
- `MCP_MAX_BODY_BYTES` (default `131072`)

## Production Shape

The intended production URL is `https://mcp.yugalinks.com/mcp`.

Cloudflare terminates the public connection and routes the existing tunnel to the `trade-mcp` ClusterIP service. The service then calls `trade-service.trade-service.svc.cluster.local:8000` over the cluster network.

The service is intentionally stateless so multiple AKS replicas do not require session affinity.
