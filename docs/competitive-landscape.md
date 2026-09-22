# Competitive Landscape

Reviewed 2026-09-06. This is a research note for product positioning and launch decisions, not customer-facing copy. Claims below are based on the linked product pages and published capabilities; competitor coverage and pricing can change.

## Executive Conclusion

- **Closest direct competitor: [OEC](https://oec.world/en).** It combines global trade profiles, bilateral country/product analysis, economic-complexity methods, export-potential modeling, an API, and [OEC BotMarket](https://botmarket.oec.world/) for research agents. BotMarket is free in public beta, exposes a machine-readable manifest, and allows free queries up to 1,000 rows per request with an email-issued API key.
- **Closest opportunity-model competitors: [ITC Trade Map](https://www.trademap.org/) and [ITC Export Potential Map](https://exportpotential.intracen.org/en/).** They already serve country/product/partner analysis and market-selection or export-potential workflows with institutional credibility.
- **Closest enterprise competitors: [Trademo](https://www.trademo.com/), [Panjiva](https://www.panjiva.com/), [ImportGenius](https://www.importgenius.com/), and [Descartes Datamyne](https://www.datamyne.com/).** They sell current shipment and company intelligence, supplier discovery, competitor monitoring, prospecting, compliance, tariffs, and alerts rather than only aggregate trade statistics.
- **Closest data substitutes: [WITS](https://wits.worldbank.org/), [UN Comtrade](https://comtradeplus.un.org/TradeFlow), [TrendEconomy](https://trendeconomy.com/), and [Trade Data Monitor](https://www.tradedatamonitor.com/).** They can answer much of the underlying country/product/partner trade-data question, with different access, freshness, and licensing models.

Yugalinks is not entering an empty market. The strongest defensible entry is a focused, agent-native workflow for MSMEs, not a claim to own global commerce data.

## Yugalinks Baseline

The current MCP exposes eleven bounded, read-only tools over primarily OECD Balanced International Merchandise Trade Statistics:

- Country and HS product lookup.
- Complete approved commerce-data dataset catalog discovery and bounded searches across named contracts.
- Global, country, product, and exporter-importer merchandise flows.
- Lane-risk observations.
- Calculated export-opportunity indicators.
- One public machine-readable lane page.

The current public coverage is HS 2017 bilateral merchandise statistics for 1995-2024 where observations are available. Some corridor and risk records include tariff and FTA context, but the service does not provide firm identities, buyer/supplier records, bills of lading, tariff schedules, rules of origin, sanctions, live shipping, or current shipment events.

## Direct Global Research Competitors

| Competitor | What it is doing | Overlap with Yugalinks | Competitive strength |
| --- | --- | --- | --- |
| [OEC](https://oec.world/en) | Provides country, product, bilateral, rankings, visualizations, economic-complexity analysis, tariff simulation, forecasts, API access, bulk datasets, and an export-potential model. Free users get historical global trade; its published plans list Pro at $299/month and Premium at $1,999/month. | **Very high.** Country/product/country-to-country analysis, opportunity discovery, API access, and agent distribution overlap directly. | Best combination of recognizable product, visual analysis, methodology, current data, and automated-client distribution. OEC BotMarket lists 1,276 datasets across 19 domains and is free in public beta. |
| [ITC Trade Map](https://www.trademap.org/) | Country and product trade statistics, partner analysis, trends, and market research for international trade users. | **High.** It answers the same basic market, product, partner, and trade-flow questions. | Institutional authority, long-standing adoption, and established trade-analysis workflows. |
| [ITC Export Potential Map](https://exportpotential.intracen.org/en/) | Identifies products and destination markets with export potential using supply capacity, demand, market-access, and related trade factors. | **High for `get_export_opportunities`.** | Directly owns the export-potential concept and has strong institutional credibility. |
| [WITS](https://wits.worldbank.org/) | World Bank platform for merchandise trade, tariffs, non-tariff measures, country and HS6 analysis, downloads, APIs, and tariff-cut simulations. Custom analysis requires registration. | **High for country/product/corridor research; broader for tariffs and NTMs.** | Official World Bank/UN/ITC/WTO ecosystem and extensive reference data. The user experience is more analyst-oriented than agent-native. |
| [UN Comtrade](https://comtradeplus.un.org/TradeFlow) | Official UN merchandise trade database and API with reporter, partner, product, flow, and period dimensions. | **High as an underlying/free substitute.** | First-party statistical authority and broad raw coverage; users still need to resolve codes, normalize data, and build the research workflow. |
| [Trade Data Monitor](https://www.tradedatamonitor.com/) | Aggregates monthly customs/statistical releases from 120+ monthly-reporting countries and 182+ annual-reporting countries, with HS codes, values, weights, prices, currencies, exports, and downloads. | **High for trade-flow research.** | Fresher commercial data, broad country coverage, custom groups, and paid professional workflows. |
| [TrendEconomy](https://trendeconomy.com/) | Open-data portal for imports, exports, and trade queries. | **Moderate.** It is a direct data-discovery substitute but exposes less of the Yugalinks opportunity/lane workflow. | Low-friction trade-data access and search-oriented presentation. |

## Enterprise Shipment and Trade-Intelligence Competitors

These are not exact dataset matches, but they compete for the same business decision: which markets, suppliers, buyers, products, or lanes deserve attention.

| Competitor | What it is doing | Why it matters |
| --- | --- | --- |
| [Trademo](https://www.trademo.com/) | Combines trade management, tariffs, sanctions, product classification, FTA and origin workflows with `Intel` for demand/prospecting and `Source Atlas` for supplier discovery. It advertises 3B+ shipment records, 15M companies, 190+ countries, 100M+ multi-tier relationships, 880K+ tariff/control records, and trade-specific automated agents such as Hermes and Clara. | Strongest enterprise benchmark for combining trade data, compliance, sourcing, prospecting, and automation. Yugalinks should not compete on breadth without a narrower wedge. |
| [Panjiva](https://www.panjiva.com/) | S&P Global platform for supplier/customer discovery, company profiles, competitor monitoring, alerts, network views, contacts, and supply-chain risk. It advertises 9M companies, 2B+ shipment records, and coverage representing 35% of global trade flows. | Strong company and shipment network moat. Yugalinks is cheaper and more transparent for aggregate statistical research, but cannot currently identify companies or shipments. |
| [ImportGenius](https://www.importgenius.com/) | Bill-of-lading and customs intelligence for supplier discovery, customer discovery, competitive intelligence, compliance, market sizing, automated company profiles, and alerts. It advertises 3.3B+ shipment records across 25+ countries and 20+ years of insights. | Strongest practical comparison for users who want current buyers, suppliers, shipment activity, and market leads rather than country-level statistics. |
| [Descartes Datamyne](https://www.datamyne.com/) | Global trade database, market insight, supplier and sales-lead generation, analytics, tariff insights, API access, and an announced automated trade-data agent. It advertises access to 190+ countries and 500M+ records added annually. | Mature enterprise distribution, API/data licensing, tariff integration, and current shipment detail. |
| [ImportYeti](https://www.importyeti.com/) | Free search over US customs shipment records, updated daily, aimed at finding suppliers and inspecting shipping relationships. The homepage currently advertises more than 710M records. | Important free alternative for supplier discovery, but primarily US shipment records rather than global bilateral trade and export-opportunity analysis. |

## What Competitors Are Winning On

- **Freshness:** commercial platforms emphasize daily, monthly, or near-current shipment and customs records. Yugalinks currently ends at 2024, which is a serious weakness for a product described as market intelligence.
- **Actionable identity:** Trademo, Panjiva, ImportGenius, and Datamyne connect trade activity to companies, suppliers, buyers, contacts, alerts, and workflows. Yugalinks currently stops at countries, products, corridors, and calculated indicators.
- **Opportunity modeling:** OEC and ITC already make export-potential or market-selection claims. Yugalinks needs to explain why its opportunity score is useful, reproducible, and different rather than simply renaming a ranking.
- **Agent distribution:** OEC BotMarket is the clearest direct response to the MCP strategy: structured datasets, a manifest, agent instructions, free discovery, and free bounded queries.
- **Trust and institutional data:** OEC, ITC, World Bank/WITS, UN Comtrade, OECD, and Trade Data Monitor all compete on source attribution, methodology, and coverage disclosures.

## Where Yugalinks Can Still Win

- A **small, typed tool surface** that gives an agent a complete commerce-research path without requiring the user to learn dataset schemas, HS dimensions, or generic API endpoints.
- A focused **MSME export workflow** that moves from product and country lookup to partner/corridor comparison, lane observations, and an opportunity shortlist.
- Clear separation between reported merchandise statistics and calculated research indicators, with provenance in every response.
- A free remote MCP endpoint and public machine-readable lane pages that are easier to use from research clients than analyst portals built around dashboards and exports.
- A niche where the combination of OECD coverage, HS6 corridors, lane-risk context, and bounded opportunity results is more useful than a general data marketplace.

These are positioning hypotheses, not established moats. They require usage evidence and customer interviews.

## Deployment Assessment

### Recommendation

**Yes, deploy it as a controlled public beta. Do not treat the deployment as proof of product-market fit or as the finished competitive product.**

Deployment is worthwhile if the goal is to validate whether research clients and MSME users actually use the workflow, collect tool/query feedback, and create a distribution point for the broader Yugalinks product. It is not worthwhile as a standalone launch if the expectation is to beat OEC, ITC, Trademo, Panjiva, or Datamyne on data freshness, firm-level coverage, tariffs, or enterprise breadth.

### Why the beta is relatively inexpensive

- The production manifests already use the existing AKS application pool and Cloudflare Tunnel rather than adding a public load balancer.
- The deployment requests 100m CPU and 256Mi memory per pod, limits each pod to 500m CPU and 512Mi memory, starts with two replicas, and can autoscale to four.
- The repository workflow already runs protocol tests, builds and pushes GHCR images, and rolls out through the existing Azure OIDC/AKS command path.
- The MCP service is a thin read-only proxy to the existing trade-service, so it does not require another trade-data store.

### Current blockers before public beta

1. `commerce-mcp.yugalinks.com` does not currently resolve; health and discovery requests fail before reaching the service.
2. The production Cloudflare Tunnel DNS route still needs to be created for `commerce-mcp.yugalinks.com`.
3. The new `/docs/mcp` page is implemented locally; it must be included in the next `webapp` production release before marketplace preflight.
4. The production `trade-mcp-env` Secret and GHCR pull secret must be verified without exposing values.
5. The 2024 data ceiling must be stated prominently. Do not market the beta as current trade intelligence until refresh coverage exists.
6. Usage measurement should be added or confirmed before launch: tool-call counts, errors, latency, repeat clients, and documentation referrals, without storing sensitive prompts or credentials.

### Recommended launch sequence

1. Deploy the existing server privately through CI and verify the production service, secret, probes, and trade-service connectivity.
2. Create the DNS route and verify the public health, discovery, server-card, initialize, tools/list, lookup, and trade-query paths.
3. Release the MCP documentation page and a clear historical-coverage notice through `webapp`.
4. Run a 30-day public beta through Smithery and the official registry only after preflight passes.
5. Measure actual usage and user requests before adding tariffs, supplier data, current releases, or more tools.

No production deployment, DNS change, marketplace submission, or payment was made during this review.

## Sources

- [OEC plans and capabilities](https://oec.world/en/plans)
- [OEC API](https://oec.world/en/resources/api)
- [OEC BotMarket](https://botmarket.oec.world/)
- [World Bank WITS](https://wits.worldbank.org/)
- [Trade Data Monitor](https://www.tradedatamonitor.com/)
- [Panjiva](https://www.panjiva.com/)
- [ImportGenius](https://www.importgenius.com/)
- [Descartes Datamyne](https://www.datamyne.com/)
- [Trademo](https://www.trademo.com/)
- [ImportYeti](https://www.importyeti.com/)
- [UN Comtrade](https://comtradeplus.un.org/TradeFlow)
