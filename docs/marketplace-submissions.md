# Marketplace Submission Plan

This document prepares the Yugalinks Commerce Intelligence MCP listing for public directories. It does not submit forms, create accounts, pay listing fees, or change production infrastructure.

For the broader product and competitor assessment, see [Competitive Landscape](./competitive-landscape.md).

## Canonical Listing

- Display name: `Yugalinks Commerce Intelligence`
- Directory slug: `yugalinks-commerce-intelligence`
- Public endpoint: `https://commerce-mcp.yugalinks.com/mcp`
- Transport: Streamable HTTP
- Authentication: none for public read-only tools
- Documentation: `https://www.yugalinks.com/docs/mcp`
- Homepage: `https://www.yugalinks.com`
- Data sources: `https://www.yugalinks.com/data-sources`
- Methodology: `https://www.yugalinks.com/methodology`
- Support: `https://www.yugalinks.com/contact`
- Categories: Research & Data, Open Data, Government Data, Finance

## Listing Copy

### Short description

Free, read-only OECD-backed cross-border commerce research for AI assistants: countries, HS products, approved commerce datasets, corridors, lane risk, and export opportunities.

### Full description

Yugalinks Commerce Intelligence gives MCP-compatible AI clients bounded access to reported cross-border commerce research. Clients can look up countries and HS codes, discover all approved commerce-data dataset contracts, search up to eight named datasets at a time, compare global and country merchandise flows, inspect exporter-importer corridors, review lane-risk observations, and query calculated export-opportunity indicators. Some corridor and risk observations include market-access, tariff and FTA context. Responses include provider, dataset, edition, coverage and source links where available. The service is read-only and does not expose accounts, credentials, SQL, physical storage names or unrestricted bulk data. It is not a customs classification, tariff schedule, rules-of-origin or compliance service.

### Example prompts

- Which countries import the most of HS 870899?
- Compare India's exports and imports in 2024.
- What was the reported merchandise-flow value from India to Germany for HS 870899?
- Which export opportunities combine growing demand with low exporter share?
- Summarize the risk signals for the Bulgaria to United Kingdom vehicle-parts lane.
- Which approved datasets contain HS6 corridor or market-share observations?

## Preflight Gate

Do not submit until every item below is true:

- `https://commerce-mcp.yugalinks.com/health` returns `200`.
- `https://commerce-mcp.yugalinks.com/.well-known/mcp.json` returns the production HTTPS endpoint.
- `https://commerce-mcp.yugalinks.com/.well-known/mcp/server-card.json` returns the public tool card.
- MCP `initialize` returns protocol version `2025-06-18` or the current supported version.
- MCP `tools/list` returns all eleven documented tools.
- `list_trade_datasets` returns the complete approved dataset catalog without physical storage identifiers.
- `search_trade_datasets` succeeds for at least one core, risk, and opportunity dataset with bounded output.
- Unfiltered searches are rejected before any large dataset query is attempted.
- At least one lookup and one merchandise-flow query succeed through the public hostname.
- `https://www.yugalinks.com/docs/mcp` is live and contains copyable curl examples.
- `python3 preflight.py --base-url https://commerce-mcp.yugalinks.com` passes without failures.
- OECD attribution, terms and coverage language has been reviewed by the data owner.
- The production `trade-mcp-env` Secret exists and contains no values in Git.
- Cloudflare or other WAF rules do not block marketplace scanners.
- The support address and public privacy/legal pages are live.

## Target Directories

### Official MCP Registry

- Directory: `https://registry.modelcontextprotocol.io/`
- Documentation: `https://modelcontextprotocol.io/registry`
- Purpose: canonical metadata for downstream aggregators.
- Requirement: a publicly reachable remote server and a verified namespace.
- Namespace decision: choose one verified identifier before submission, such as `com.yugalinks/commerce` after domain verification or an `io.github.yugalinks/...` namespace after GitHub verification. Do not submit both identifiers.
- Metadata: prepare the official `server.json` entry only after the namespace is selected and verified.

### Smithery

- Submission: `https://smithery.ai/new`
- Publish mode: bring the existing hosted HTTPS server.
- Requirements: public Streamable HTTP endpoint; OAuth is not required for this server because the public tools do not require authentication.
- Scanner: Smithery can inspect the endpoint and extract the tool metadata. The server card is available as a fallback if automatic scanning cannot complete.
- WAF note: allow the Smithery scanner or use the static server card if automated scanning is blocked.

### Glama

- Directory: `https://glama.ai/mcp/servers`
- Submission: use the `Add Server` flow after signing in.
- Supply: repository URL, public endpoint, documentation URL, description, categories and source/provenance links.
- Suggested categories: Research & Data, Open Data, Government Data.

### MCP.so

- Submission: `https://mcp.so/submit`
- Submission type: Remote Server.
- Supply: the public repository URL, canonical endpoint, listing copy and documentation URL.
- The site currently displays a paid one-time publishing option. Do not purchase a listing or featured placement without explicit owner approval.

### Host-specific directories

Claude, ChatGPT, Copilot and other host connector catalogs have separate review and account requirements. A listing in the official MCP Registry or an aggregator does not automatically publish the server inside those products. Apply to those catalogs only after the public endpoint, legal pages, support route and rate-limit policy are stable.

## Release Order

1. Deploy the production image and route through the protected MCP repository workflow.
2. Run the preflight curl and MCP checks above.
3. Select and verify the official registry namespace.
4. Submit the official registry metadata.
5. Submit the same canonical listing to Smithery, Glama and MCP.so.
6. Record listing URLs, submission dates and review status in the repository.

Never place GitHub, GHCR, Azure, Cloudflare or private-service credentials in a marketplace listing or client configuration.

## Smithery Overlap Review

Reviewed 2026-09-06 against the Smithery registry entries and tool metadata. This is a positioning review, not an endorsement or an exhaustive audit of every Smithery result.

### Yugalinks surface

Yugalinks exposes a focused OECD BIMTS research surface: country and HS-code lookup, global/country/product/corridor merchandise flows, bounded lane-risk observations, calculated export-opportunity indicators, and one public lane page. The dataset is primarily HS 2017 bilateral merchandise statistics for 1995-2024 where observations are available.

### Closest overlaps

| Server | Overlap | Difference | Listing implication |
| --- | --- | --- | --- |
| [Trimtab AIS](https://smithery.ai/servers/mrigank86/trimtab-ais) | **Strong partial overlap.** `query_series` and `search_series` expose US Census port trade by partner country and commodity. | US-focused monthly port ledger plus live terrestrial AIS, eight container gateways, and vessel events; not a global OECD bilateral HS2/HS4/HS6 research service. | Mention global bilateral coverage, HS granularity, corridors, and opportunity/risk research. Do not describe Yugalinks as port or live-shipping data. |
| [FAOSTAT MCP](https://smithery.ai/servers/cyanheads/faostat-mcp-server) | **Partial overlap.** `faostat_query_observations` can query food/agriculture trade domains, and `faostat_commodity_profile` returns top exporters/importers. | FAO food, agriculture, production, and commodity cube over a local mirror; broader historical agriculture scope, not general merchandise BIMTS or lane-risk scoring. | Distinguish merchandise trade from agricultural production and commodity statistics. |
| [Africa Intelligence MCP](https://smithery.ai/servers/quantumskils/africa-intelligence-mcp) | **Partial overlap.** `trade_statistics`, `market_summary`, `country_dashboard`, and `search_all` include trade volumes, partners, commodity breakdowns, and trade balance. | Africa-focused business-intelligence bundle covering tenders, grants, jobs, companies, and commodities; trade is one module rather than the core global product. | Position Yugalinks as dedicated global trade research, not an Africa opportunities portal. |
| [Sugra API](https://smithery.ai/servers/sugra-systems/sugra-api) | **Adjacent platform overlap.** Trade is one of 36 domains and the gateway can search or call catalogued endpoints. | Generic 1,500+ endpoint, 160+ source gateway with generic `fetch_data`, `search_endpoints`, `describe_endpoint`, and `call_endpoint` tools; the registry metadata does not expose a dedicated bilateral-trade tool surface. | Emphasize purpose-built typed trade workflows instead of a general endpoint catalog. |

### Related but not direct substitutes

| Server | Relationship to Yugalinks |
| --- | --- |
| [LandedAPI](https://smithery.ai/servers/joshtnunnery/LandedAPI) | Customs and tariff workflow: HTS classification, CBP rulings, duty rates, and tariff optimization for US importers. It does not provide Yugalinks-style observed trade totals, corridors, or opportunity indicators. |
| [HS Code Classifier MCP](https://smithery.ai/servers/OjasKord/hs-code-classifier-mcp-server) | Classifies or validates product descriptions against tariff schedules. This overlaps only with the general HS vocabulary around `lookup_products`; Yugalinks does not classify products or validate customs filings. |
| [hts-classify](https://smithery.ai/servers/jeff-5lis/hts-classify) | One-tool US HTS candidate classifier using the USITC schedule. It is classification/compliance, not trade-flow research. |
| [ASEAN Trade Rules MCP](https://smithery.ai/servers/vdineshk/asean-trade-rules-mcp) | FTA eligibility, rules of origin, tariff savings, and documentation requirements. It answers whether preferential treatment may apply, not what reported trade flows occurred. |
| [Primary Source Commodities](https://smithery.ai/servers/sawftware-apps/commodities-sh) | EIA, FRED, CFTC, USDA, and USGS commodity data. It is adjacent to product-market research but does not expose bilateral trade corridors or HS trade rankings. |

### Positioning conclusion

- The strongest functional overlap reviewed is Trimtab's US port trade series and the trade modules in FAOSTAT and Africa Intelligence.
- No reviewed server presented the same combination of global OECD bilateral HS trade, exporter-importer corridors, lane-risk observations, and export-opportunity indicators.
- The listing should lead with the focused research workflow and precise coverage, not generic claims such as "trade data for any question."
- Keep HS classification, tariff optimization, FTA rules, live shipping, and commodity prices out of the Yugalinks feature claim unless a separate tool is actually added.

Source metadata reviewed from the Smithery registry entries for [Sugra](https://registry.smithery.ai/servers/sugra-systems/sugra-api), [Trimtab](https://registry.smithery.ai/servers/mrigank86/trimtab-ais), [FAOSTAT](https://registry.smithery.ai/servers/cyanheads/faostat-mcp-server), [Africa Intelligence](https://registry.smithery.ai/servers/quantumskils/africa-intelligence-mcp), [LandedAPI](https://registry.smithery.ai/servers/joshtnunnery/LandedAPI), [HS Code Classifier](https://registry.smithery.ai/servers/OjasKord/hs-code-classifier-mcp-server), [hts-classify](https://registry.smithery.ai/servers/jeff-5lis/hts-classify), and [ASEAN Trade Rules](https://registry.smithery.ai/servers/vdineshk/asean-trade-rules-mcp).
