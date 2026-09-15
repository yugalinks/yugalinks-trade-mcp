# Production Routing

The MCP service uses the existing Cloudflare Tunnel rather than a new public load balancer.

The tunnel configuration routes:

```text
commerce-mcp.yugalinks.com -> trade-mcp.trade-mcp.svc.cluster.local:8002
```

The `trade-mcp-env` Secret must exist in the `trade-mcp` namespace with at least:

- `TRADE_SERVICE_API_KEY`: the existing trade-service service key.
- `REDIS_URL`: optional shared Redis URL for cross-replica rate limiting.

The GitHub Actions `Trade MCP CI` workflow owns the application rollout. It runs tests and
manifest validation, publishes an immutable `sha-<commit>` image to GHCR, attaches the
production manifests through Azure's AKS command runner, applies them, waits for the MCP
rollout, probes the private adapter, refreshes the existing Cloudflare tunnel workload, creates
or updates the canonical Cloudflare DNS record through the Cloudflare API, and runs the complete
public HTTPS preflight. Use a push to `main`, or manually dispatch the workflow from `main` with
`deploy_production=true`.

The production GitHub environment must provide:

- `GHCR_USERNAME` and `GHCR_PUSH_TOKEN` repository secrets.
- Either `CLOUDFLARE_API_TOKEN` production environment secret with DNS edit permission, or
  `CLOUDFLARE_EMAIL` and `CLOUDFLARE_GLOBAL_API_KEY` production environment secrets from the
  private Cloudflare runtime.
- `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AKS_RESOURCE_GROUP`, and `AKS_CLUSTER_NAME` environment variables.
- The existing `ghcr-registry-secret` and `trade-mcp-env` Kubernetes Secrets.
- The existing `trade-service-env` Kubernetes Secret.
- A `cloudflared` Deployment, StatefulSet, or DaemonSet in the `cloudflare` namespace labeled `app=cloudflared`.

The workflow also applies the least-privilege `trade-service-allow-trade-mcp` NetworkPolicy,
allowing only the MCP namespace to call the trade-service HTTP port, and probes the private
adapter through the deployed MCP pod before refreshing the public tunnel.

Do not apply the service manifests, edit the tunnel ConfigMap, or create DNS records from a
workstation. The protected production workflow is the only release path.

No DNS, Kubernetes, or Cloudflare change was executed while preparing this release.
