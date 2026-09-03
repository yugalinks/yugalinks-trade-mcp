# Production Routing

The MCP service is intended to use the existing Cloudflare Tunnel rather than a new public load balancer.

The tunnel configuration routes:

```text
mcp.yugalinks.com -> trade-mcp.trade-mcp.svc.cluster.local:8002
```

Before rollout, create the DNS route for the existing tunnel from an authenticated operator session:

```bash
cloudflared tunnel route dns 3a212204-f9b4-4aef-bc5d-7e3d39c28361 mcp.yugalinks.com
```

The `trade-mcp-env` Secret must exist in the `trade-mcp` namespace with at least:

- `TRADE_SERVICE_API_KEY`: the existing trade-service service key.
- `REDIS_URL`: optional shared Redis URL for cross-replica rate limiting.

Apply the service manifests only after the image is available in GHCR:

```bash
kubectl apply -k trade-mcp/deploy/production
kubectl -n trade-mcp rollout status deployment/trade-mcp
```

This file is preparation only. No DNS, Kubernetes, or Cloudflare change was executed by the development workflow.
