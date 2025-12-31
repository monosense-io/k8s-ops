# prod-ops Repository Analysis

## Cluster Identity

| Property | Value |
|----------|-------|
| Cluster Name | prod |
| Primary Domain | monosense.io (public) |
| Secondary Domain | monosense.dev (private) |
| Node Network | 10.25.13.0/24 |
| Node IPs | 10.25.13.11-16 (6 nodes) |
| Control Plane | 3 nodes |

## Repository Structure

```
prod-ops/
├── bootstrap/              # Helmfile bootstrap
│   └── helmfile.yaml      # Bootstrap release order
├── kubernetes/
│   ├── apps/              # Application manifests (16 namespaces)
│   ├── flux/
│   │   ├── cluster/       # Cluster kustomizations
│   │   └── meta/          # Metadata and repositories
│   │       └── repositories/
│   └── components/        # Reusable kustomize components
├── talos/                  # Talos machine configs
│   ├── controlplane/      # Control plane node configs
│   └── schematic.yaml     # System extensions
├── terraform/
│   └── authentik/         # Authentik IDP configuration
├── docs/
│   ├── runbooks/          # Operational runbooks
│   └── src/               # Documentation source
├── .github/                # GitHub Actions workflows
├── .renovate/              # Renovate modules
└── .taskfiles/             # Task automation
```

## Namespaces & Applications (60 HelmReleases)

### kube-system (Core Infrastructure)
- cilium (v1.18.1) - eBPF networking
- coredns (v1.43.3) - DNS server
- metrics-server
- spegel - OCI registry mirror
- csi-driver-nfs
- descheduler
- generic-device-plugin
- intel-device-plugin
- reloader

### flux-system (GitOps)
- flux-operator (v0.28.0)
- flux-instance (v0.28.0)
- headlamp - K8s dashboard
- tofu-controller

### cert-manager
- cert-manager (v1.18.2)

### external-secrets
- external-secrets (v0.19.2)

### networking
- envoy-gateway
- external-dns (Cloudflare & BIND)
- cloudflared
- multus
- gateway-jwt
- external-services
- echo-server

### observability
- victoria-metrics
- victoria-logs
- fluent-bit
- grafana (v9.4.4)
- gatus
- keda
- kromgo
- silence-operator
- exporters (various)

### databases
- cloudnative-pg
- dragonfly
- pgadmin

### rook-ceph
- rook-ceph

### openebs-system
- openebs

### volsync-system
- volsync
- snapshot-controller

### system-upgrade
- system-upgrade-controller

### actions-runner-system
- actions-runner-controller

### security
- authentik (v2025.8.1) - Identity provider

### selfhosted
- n8n - Workflow automation

### pilar (Custom Application)
- pilar-backend
- pilar-frontend

### default
- odoo - ERP system

## Bootstrap Configuration

### Helmfile Deployment Order
1. Cilium - Network CNI
2. CoreDNS - DNS
3. Cert-Manager - Certificates
4. External-Secrets - Secrets management
5. Flux Operator
6. Flux Instance

### Talos Configuration
- 6 nodes total (3 control plane)
- Network: Bonded interfaces (802.3ad LACP)
- MTU: 9000 (jumbo frames)
- VLAN: 2512

#### System Extensions
- intel-ucode
- i915-ucode
- iscsi-tools

## Helm/OCI Repositories

### HelmRepositories (4)
- fluent
- harbor
- harbor-container-webhook
- (additional)

### OCI Repositories (85)
Major ones:
- app-template (v4.2.0)
- cilium (v1.18.1)
- grafana (v9.4.4)
- authentik (v2025.8.1)
- coredns (v1.43.3)
- cert-manager (v1.18.2)
- external-secrets (v0.19.2)
- flux-operator (v0.28.0)
- flux-instance (v0.28.0)

## Terraform Configuration

### Authentik Provider
- Provider version: 2025.8.0
- 1Password provider: 2.1.1
- Backend: Cloudflare R2 (S3-compatible)
- State path: prod/authentik/state.tfstate

## Infrastructure Patterns

### Flux Structure
- `cluster-meta` - Repository definitions (1h sync)
- `cluster-apps` - Application manifests (depends on cluster-meta)

### GitHub Actions (8 workflows)
- renovate.yaml - Dependency updates (hourly)
- flux-local.yaml - Flux validation
- terraform-diff.yaml - TF plan on changes
- terraform-publish.yaml - TF apply
- image-pull.yaml
- labeler.yaml
- label-sync.yaml
- tag.yaml

### Renovate Groups (10)
Same as home-ops:
- 1Password Connect
- Actions Runner Controller
- Cert-Manager
- Cilium
- CoreDNS
- External Secrets Operator
- Flux Operator
- Intel Device Plugins
- Rook-Ceph
- Spegel

## External Integrations

### 1Password Connect
- Endpoint: opconnect.monosense.dev
- Vaults: Prod, Infra
- Used for Terraform and ExternalSecrets

### Cloudflare
- R2 for Terraform state
- DNS management via External-DNS
- Tunnel via cloudflared

## Key Endpoints

| Service | URL |
|---------|-----|
| SSO | https://sso.monosense.io |
| Grafana | https://grafana.monosense.io |
| PgAdmin | https://pgadmin.monosense.io |
| Status | https://status.monosense.io |
| Headlamp | https://headlamp.monosense.io |
| n8n | https://wf.monosense.io |
| Logs | https://logs.monosense.io |
| Pilar API | https://api.pilar.monosense.io |
| Pilar Code | https://code.monosense.io |
| Kromgo | https://kromgo.monosense.io |
| 1Password | https://opconnect.monosense.dev |

## Operational Documentation

### Runbooks Available
- Gateway 401/403 error handling
- Rate limiting issues
- Latency surge responses
- JWT handling
- JWKS fetch error resolution
