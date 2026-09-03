# Directory Submission Brief

This is the submission copy for directories and AI connector reviews. It is not a directory API payload and does not publish anything by itself.

## Identity

- Name: `Yugalinks Trade Intelligence`
- Server ID: `yugalinks-trade`
- Endpoint: `https://mcp.yugalinks.com/mcp`
- Transport: Streamable HTTP
- Authentication: none for public read-only tools
- Homepage: `https://www.yugalinks.com`
- Documentation: `https://www.yugalinks.com/docs/mcp`
- Data sources: `https://www.yugalinks.com/data-sources`
- Methodology: `https://www.yugalinks.com/methodology`
- Support: `https://www.yugalinks.com/contact`

## Description

Yugalinks Trade Intelligence gives AI assistants free, read-only access to country, HS product, global trade, corridor, lane-risk, and export-opportunity research. Results include provider and coverage context, and public lane-page links where available. The service does not expose accounts, private dashboards, credentials, SQL, or unrestricted bulk data.

## Tools

- `lookup_countries`: Find country names and ISO3 codes.
- `lookup_products`: Find HS codes and product descriptions.
- `get_global_trade`: Retrieve global yearly trade totals.
- `get_country_trade`: Retrieve country exports, imports, balance, and growth.
- `get_product_trade`: Retrieve product-level yearly trade.
- `get_corridor_trade`: Retrieve exporter-importer trade corridors.
- `get_lane_risk`: Retrieve bounded lane-risk observations.
- `get_export_opportunities`: Retrieve bounded calculated opportunity indicators.
- `get_lane_page`: Retrieve one public machine-readable lane page and its source URL.

## Example Requests

- "Which countries import the most of HS 870899?"
- "Compare India's exports and imports in 2024."
- "What is the reported trade value from India to Germany for HS 870899?"
- "Which export opportunities have high reported demand but low exporter share?"
- "Summarize the risk signals for the Bulgaria to UK vehicle-parts lane."

## Review Notes

- The service is read-only and all tools are marked with MCP read-only annotations.
- Historical observations and calculated indicators are labeled separately where the source payload provides that distinction.
- Coverage is OECD bilateral merchandise trade statistics for 1995-2024 where observations are available.
- Fair-use limits are `60` MCP requests per IP per minute, with request and response size caps.
- Directory publication should wait until the production DNS route, GHCR image, required trade-service secret, and OECD attribution/licensing review are complete.
