# Directory Submission Brief

This is the submission copy for directories and connector reviews. It is not a directory API payload and does not publish anything by itself.

See `docs/marketplace-submissions.md` for target directories, preflight checks and release order.

## Identity

- Name: `Yugalinks Commerce Intelligence`
- Directory slug: `yugalinks-commerce-intelligence`
- Official MCP Registry name: pending verified namespace selection
- Endpoint: `https://commerce-mcp.yugalinks.com/mcp`
- Transport: Streamable HTTP
- Authentication: none for public read-only tools
- Homepage: `https://www.yugalinks.com`
- Documentation: `https://www.yugalinks.com/docs/mcp`
- Data sources: `https://www.yugalinks.com/data-sources`
- Methodology: `https://www.yugalinks.com/methodology`
- Support: `https://www.yugalinks.com/contact`

## Description

Yugalinks Commerce Intelligence gives research assistants free, read-only access to country, HS product, global merchandise flows, approved commerce datasets, corridors, lane-risk, and export-opportunity research. Some corridor and risk observations include market-access, tariff and FTA context. Results include provider and coverage context, and public lane-page links where available. The service does not expose accounts, private dashboards, credentials, SQL, physical storage names, or unrestricted bulk data. It is not a customs classification, tariff schedule, rules-of-origin or compliance service.

## Tools

- `lookup_countries`: Find country names and ISO3 codes.
- `lookup_products`: Find HS codes and product descriptions.
- `list_trade_datasets`: List all approved commerce-data dataset contracts and public columns.
- `search_trade_datasets`: Search up to eight named approved datasets with bounded filters.
- `get_global_trade`: Retrieve global yearly merchandise-flow totals.
- `get_country_trade`: Retrieve country imports, exports, balance, and growth.
- `get_product_trade`: Retrieve product-level yearly merchandise flows.
- `get_corridor_trade`: Retrieve exporter-importer goods corridors.
- `get_lane_risk`: Retrieve bounded lane-risk observations.
- `get_export_opportunities`: Retrieve bounded calculated opportunity indicators.
- `get_lane_page`: Retrieve one public machine-readable lane page and its source URL.

## Example Requests

- "Which countries import the most of HS 870899?"
- "Compare India's exports and imports in 2024."
- "What is the reported merchandise-flow value from India to Germany for HS 870899?"
- "Which export opportunities have high reported demand but low exporter share?"
- "Summarize the risk signals for the Bulgaria to UK vehicle-parts lane."
- "List the approved datasets for product, corridor and risk research."

## Review Notes

- The service is read-only and all tools are marked with MCP read-only annotations.
- Historical observations and calculated indicators are labeled separately where the source payload provides that distinction.
- Coverage is OECD bilateral merchandise statistics for 1995-2024 where observations are available.
- Fair-use limits are `60` MCP requests per IP per minute, with request and response size caps. Commerce-data searches allow up to eight named datasets and 25 rows per dataset.
- Each dataset search requires an applicable year, country, product, corridor, or text filter.
- Human documentation is available at `https://www.yugalinks.com/docs/mcp`; machine-readable discovery is available at `/.well-known/mcp.json` and `/.well-known/mcp/server-card.json`.
- Directory publication should wait until the production DNS route, GHCR image, required private-service secret, and OECD attribution/licensing review are complete.
