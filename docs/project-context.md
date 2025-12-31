---
project_name: 'k8s-ops'
user_name: 'monosense'
date: '2025-12-28'
sections_completed: ['technology_stack', 'kubernetes_gitops_patterns', 'flux_helmrelease_rules', 'naming_structure_rules', 'development_workflow_rules', 'critical_rules']
status: 'complete'
rule_count: 52
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

### Core Platform
- **Talos Linux v1.12.0** - Immutable K8s OS, API-driven (no SSH)
- **Cilium v1.18.5** - CNI with eBPF datapath, BGP Control Plane
- **Flux CD v2.7.5** - GitOps with Kustomize + Helm controllers
- **Kustomize** - Native base/overlay pattern

### Networking
- **Envoy Gateway v1.6.1** - Gateway API v1.4.1 implementation
- **external-dns v0.19.0** - Dual provider: Cloudflare (external) + bind (internal)
- **Cloudflared** - Per-cluster Cloudflare Tunnels:
  - infra: 2025.9.1 → `monosense.dev` → `envoy-external`
  - apps: 2025.8.1 → `monosense.io` → `envoy-gateway-external`
  - Features: QUIC transport, post-quantum, 2 replicas
- **Tailscale Operator 1.88.3** - Mesh VPN access
- **SMTP Relay (Maddy 0.8.1)** - Email relay for apps
- **Multus** - CNI chaining for multi-network pods

### Infrastructure Services
- **Rook-Ceph v1.18.8** - Block storage (`ceph-block` StorageClass)
- **OpenEBS v4.4** - LocalPV (`openebs-hostpath` for CNPG)
- **NFS CSI Driver** - Shared storage mounts
- **cert-manager v1.19.2** - TLS with Let's Encrypt
- **External Secrets Operator v1.0.0** - 1Password Connect integration

### Database & Cache
- **CloudNative PostgreSQL** - Shared cluster pattern per cluster
- **Dragonfly Operator v1.3.0** - Redis-compatible in-memory cache

### Observability
- **VictoriaMetrics v1.131.0** - Centralized metrics on infra cluster
- **VictoriaLogs** - Log aggregation on infra cluster
- **Grafana** - Dashboards and alerting
- **Gatus** - Health check endpoints
- **KEDA 2.17.2** - Event-driven autoscaling
- **Fluent-bit** - Log shipping (remote-write to infra)

### Operations
- **Reloader 2.2.3** - Auto-reload on ConfigMap/Secret changes
- **Spegel 0.4.0** - P2P registry mirror (reduces egress)
- **Actions Runner Controller 0.12.1** - Self-hosted GitHub runners
- **Tofu Controller 0.16.0-rc.5** - OpenTofu GitOps automation
- **Descheduler** - Pod rebalancing for resource optimization

### Domain Architecture
| Cluster | Domain | Tunnel Origin | Envoy Gateway Service |
|---------|--------|---------------|----------------------|
| infra | `monosense.dev` | `external.monosense.dev` | `envoy-external` |
| apps | `monosense.io` | `external.monosense.io` | `envoy-gateway-external` |

### Version Constraints
- Cilium cluster.id: infra=1, apps=2 (for future Cluster Mesh)
- SOPS AGE key: `age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek`
- Cloudflare R2 endpoint: `eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`

---

## Kubernetes/GitOps Patterns

### CNPG Shared Cluster Pattern
- **One `postgres` cluster per Kubernetes cluster** - NOT per-app clusters
- Database name = `${APP}` (matches application name)
- Host endpoint: `postgres-rw.databases.svc.cluster.local`
- Credentials: `${APP}-pguser-secret` (from External Secrets)
- Init credentials: `${APP}-initdb-secret`
- Backup CronJob: `${APP}-pg-backups`

### App Location Rules
| Deployment Target | Directory |
|-------------------|-----------|
| Both clusters | `kubernetes/apps/{category}/{app}/` |
| Infra cluster only | `clusters/infra/apps/{category}/{app}/` |
| Apps cluster only | `clusters/apps/apps/{category}/{app}/` |

### Storage Class Selection
| Use Case | StorageClass | Notes |
|----------|--------------|-------|
| General stateful apps | `ceph-block` | Rook-Ceph RWO |
| CNPG PostgreSQL | `openebs-hostpath` | Local NVMe performance |
| Shared files (RWX) | NFS mount | Via csi-driver-nfs |
| Backups | Cloudflare R2 | VolSync + CNPG Barman |

### Flux Variable Substitution
- **ALWAYS** use `${VARIABLE_NAME}` syntax
- Variables come from `cluster-vars` ConfigMap via `postBuild.substituteFrom`
- Common variables: `${CLUSTER_NAME}`, `${CLUSTER_DOMAIN}`, `${CLUSTER_CIDR}`, `${CLUSTER_ID}`
- **NEVER** hardcode cluster-specific values

### Gateway API Routing
| Gateway | Service Name | Use Case |
|---------|--------------|----------|
| External | `envoy-external` (infra) / `envoy-gateway-external` (apps) | Public internet via Cloudflare Tunnel |
| Internal | `envoy-internal` | Internal services, no tunnel |

```yaml
# HTTPRoute gateway reference
parentRefs:
  - name: envoy-external  # or envoy-internal
    namespace: networking
    sectionName: https
```

### Component Usage Pattern
- Use `kubernetes/components/` for **reusable cross-app patterns**
- Components: cnpg, volsync, gatus, dragonfly, secpol
- Reference via relative path in kustomization.yaml:
```yaml
components:
  - ../../../../components/cnpg
```
- Use inline configuration for **app-specific one-off settings**

### Chart Source Pattern
- **Prefer OCIRepository** with `chartRef` for all new apps
- HelmRepository only for charts not available as OCI
```yaml
# Correct - OCIRepository
chartRef:
  kind: OCIRepository
  name: app-template
  namespace: flux-system

# Legacy - HelmRepository (avoid for new apps)
chart:
  spec:
    chart: app-name
    sourceRef:
      kind: HelmRepository
```

### Image Pinning Pattern
- **ALWAYS** pin production images with `@sha256:` digest
```yaml
image:
  repository: docker.io/cloudflare/cloudflared
  tag: 2025.9.1@sha256:4604b477520dc8322af5427da68b44f0bf814938e9d2e4814f2249ee4b03ffdf
```

### ExternalSecret API Version
- **Use `external-secrets.io/v1`** (ESO v1.0.0+)
- Migrate any `v1beta1` to `v1`

### Namespace Creation
- Flux Kustomization creates namespace via `targetNamespace`
- Do NOT create separate Namespace manifests
```yaml
spec:
  targetNamespace: business  # Flux creates if missing
```

### Dependency Rules
| App Type | Must Depend On |
|----------|----------------|
| Database-backed apps | `cloudnative-pg-cluster` |
| SSO-integrated apps | `authentik` |
| Apps using Dragonfly | `dragonfly-operator` |
| Apps using Kafka | `strimzi-kafka` |
| Apps with Ceph storage | `rook-ceph-cluster` |

### healthCheckExprs Patterns
```yaml
# CNPG
healthCheckExprs:
  - apiVersion: postgresql.cnpg.io/v1
    kind: Cluster
    failed: status.conditions.filter(e, e.type == 'Ready').all(e, e.status == 'False')

# Dragonfly
healthCheckExprs:
  - apiVersion: dragonflydb.io/v1alpha1
    kind: Dragonfly
    failed: status.phase != 'Ready'

# Strimzi Kafka
healthCheckExprs:
  - apiVersion: kafka.strimzi.io/v1beta2
    kind: Kafka
    failed: status.conditions.filter(e, e.type == 'Ready').all(e, e.status == 'False')
```

### Observability Pattern
| Cluster | Role | Components |
|---------|------|------------|
| infra | Hub | VictoriaMetrics, VictoriaLogs, Grafana |
| apps | Spoke | VMAgent + Fluent-bit (remote-write to infra) |

### Validation Command
```bash
# Validate Kustomize builds for both clusters
for cluster in infra apps; do
  kustomize build clusters/${cluster}/flux --enable-helm
done
```

---

## Flux CD & HelmRelease Rules

### HelmRelease API Version
- **ALWAYS** use `helm.toolkit.fluxcd.io/v2` (not v2beta1 or v2beta2)

### Required Remediation Block
Every HelmRelease MUST include:
```yaml
install:
  remediation:
    retries: 3
upgrade:
  cleanupOnFail: true
  remediation:
    strategy: rollback
    retries: 3
```

### Operator Exceptions
Operators use `retries: -1` for install (infinite retry):
```yaml
install:
  remediation:
    retries: -1  # Operators must succeed
```

### Flux Kustomization Standards
```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name app-name
  namespace: flux-system
spec:
  targetNamespace: category-namespace
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./kubernetes/apps/category/app-name/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: false
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

### YAML Anchor Pattern
Use `&name` anchor for DRY naming:
```yaml
metadata:
  name: &name odoo
spec:
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
```

### Reloader Integration
Apps with secrets/configmaps should include:
```yaml
annotations:
  reloader.stakater.com/auto: "true"
```

### Interval Standards
| Resource Type | Interval |
|---------------|----------|
| HelmRelease | `1h` |
| Kustomization | `30m` |
| OCIRepository | `5m` |
| GitRepository | `1m` |

### CRD Handling for Operators
```yaml
install:
  crds: CreateReplace
upgrade:
  crds: CreateReplace
```

---

## Naming & Structure Rules

### Kubernetes Resource Naming
| Resource Type | Convention | Example |
|---------------|------------|---------|
| Namespace | kebab-case, purpose-based | `databases`, `business`, `observability` |
| HelmRelease | kebab-case, matches chart | `odoo`, `n8n`, `authentik` |
| ConfigMap/Secret | kebab-case with suffix | `odoo-config`, `odoo-pguser-secret` |
| Service | kebab-case | `odoo`, `keycloak-http` |

### File Naming Standards
| File Type | Name | Example Path |
|-----------|------|--------------|
| Kustomization | `kustomization.yaml` | `kubernetes/apps/business/odoo/app/kustomization.yaml` |
| HelmRelease | `helmrelease.yaml` | `kubernetes/apps/business/odoo/app/helmrelease.yaml` |
| Flux Kustomization | `ks.yaml` | `kubernetes/apps/business/odoo/ks.yaml` |
| ExternalSecret | `externalsecret.yaml` | `kubernetes/apps/business/odoo/app/externalsecret.yaml` |
| NetworkPolicy | `networkpolicy.yaml` | `kubernetes/apps/business/odoo/app/networkpolicy.yaml` |
| HTTPRoute | `httproute.yaml` | `kubernetes/apps/business/odoo/app/httproute.yaml` |
| Helm values | `values.yaml` | `kubernetes/apps/business/odoo/app/values.yaml` |

### Application Directory Structure
```
kubernetes/apps/{category}/{app-name}/
├── app/                          # Main application
│   ├── helmrelease.yaml
│   ├── kustomization.yaml
│   ├── externalsecret.yaml       # If secrets needed
│   ├── networkpolicy.yaml        # If Tier 2 app
│   └── httproute.yaml            # If external access
├── components/                   # App-specific components (optional)
└── ks.yaml                       # Flux Kustomization entry point
```

### Multi-Secret Naming
| Purpose | Pattern | Example |
|---------|---------|---------|
| Database credentials | `{app}-pguser-secret` | `odoo-pguser-secret` |
| SMTP credentials | `{app}-smtp-secret` | `odoo-smtp-secret` |
| API keys | `{app}-api-secret` | `odoo-api-secret` |
| General secrets | `{app}-secret` | `odoo-secret` |

### Custom Annotations/Labels
- **Prefix:** `monosense.dev/`
- Examples:
  - `monosense.dev/backup: "true"`
  - `monosense.dev/snapshot.schedule: "0 */8 * * *"`

### YAML Extension
- **ALWAYS** use `.yaml` (not `.yml`)

---

## Development Workflow Rules

### Git Commit Messages
```
<type>(<scope>): <description>

Types: feat, fix, refactor, chore, docs, ci
Scopes: infra, apps, flux, talos, bootstrap, renovate

Examples:
feat(apps): add ArsipQ deployment
fix(infra): correct CNPG backup retention policy
chore(renovate): update Cilium to v1.18.5
```

### Staged Rollout Pattern
| Cluster | Branch | Reconciliation |
|---------|--------|----------------|
| infra | `main` | Immediate |
| apps | `release` | 24h delayed (auto fast-forward) |

Manual override: `flux suspend/resume` or GitHub Actions workflow_dispatch

### PR Review Checklist
- [ ] `kustomize build --enable-helm` passes for affected paths
- [ ] HelmRelease has install + upgrade remediation configured
- [ ] Secrets use ExternalSecret (no hardcoded values)
- [ ] Network policies present for Tier 2 apps
- [ ] Dependencies declared in ks.yaml
- [ ] HTTPRoute uses correct Gateway reference
- [ ] Variable substitution uses `${VAR}` syntax
- [ ] CNPG apps include healthCheckExprs
- [ ] Image tags pinned with `@sha256:` digest

### Renovate Strategy
- Single PR updates version in `infrastructure/base/` or `kubernetes/apps/`
- Base/overlay inheritance propagates to both clusters
- Staged rollout handles timing between clusters

### Backup Verification in Stories
Every story involving stateful apps MUST include:
```markdown
## Acceptance Criteria
- [ ] VolSync ReplicationSource created and first snapshot completed
- [ ] CNPG database accessible via ${APP}-pguser-secret
- [ ] Backup CronJob ${APP}-pg-backups runs successfully
```

### Taskfile Operations
| Task Category | Key Operations |
|---------------|----------------|
| `bootstrap:*` | Talos bootstrap, K8s apps bootstrap |
| `talos:*` | apply-node, upgrade-node, upgrade-k8s |
| `kubernetes:*` | sync-secrets, hr-restart, cleanse-pods |
| `volsync:*` | snapshot, restore, unlock |
| `op:*` | push/pull kubeconfig to 1Password |

---

## Critical Don't-Miss Rules

### NEVER Do These (Anti-Patterns)

**CNPG Anti-Pattern:**
```yaml
# WRONG - Per-app CNPG cluster
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: odoo-postgres  # NO! Use shared 'postgres' cluster
```

**Hardcoded Values Anti-Pattern:**
```yaml
# WRONG - Hardcoded cluster-specific values
host: odoo.monosense.io  # NO! Use ${CLUSTER_DOMAIN}
```

**Missing Remediation Anti-Pattern:**
```yaml
# WRONG - No remediation block
spec:
  chart: ...
  values: ...
  # Missing install/upgrade remediation!
```

**Wrong API Version Anti-Pattern:**
```yaml
# WRONG - Old API versions
apiVersion: helm.toolkit.fluxcd.io/v2beta1  # NO! Use v2
apiVersion: external-secrets.io/v1beta1     # NO! Use v1
```

### Security Rules
- **NEVER** commit secrets to Git (use ExternalSecret + 1Password)
- **NEVER** skip SOPS encryption for sensitive files
- **ALWAYS** include CiliumNetworkPolicy for Tier 2 apps
- **ALWAYS** set `readOnlyRootFilesystem: true` where possible
- **ALWAYS** drop all capabilities: `capabilities: { drop: ["ALL"] }`
- **ALWAYS** run as non-root: `runAsNonRoot: true`

### Common Gotchas
1. **Flux substitution syntax** - Use `${VAR}` not `$VAR` or `{{VAR}}`
2. **kustomization.yaml** - Use `.yaml` extension, never `.yml`
3. **Gateway name differs per cluster** - `envoy-external` vs `envoy-gateway-external`
4. **CNPG host is always the same** - `postgres-rw.databases.svc.cluster.local`
5. **Backups go to R2** - Not MinIO (MinIO is general S3 only)
6. **OCIRepository needs layerSelector** for Helm charts:
```yaml
layerSelector:
  mediaType: application/vnd.cncf.helm.chart.content.v1.tar+gzip
  operation: copy
```

### Enforcement Summary
AI agents MUST:
1. Use `kustomization.yaml` (not `.yml`)
2. Include remediation blocks in all HelmReleases
3. Use `external-secrets.io/v1` API version
4. Reference `cluster-vars` via `postBuild.substituteFrom`
5. Use kebab-case for all resource names
6. Use `monosense.dev/` prefix for custom annotations
7. Follow commit message format
8. Include CiliumNetworkPolicy for Tier 2 apps
9. Use `${VARIABLE_NAME}` syntax for substitution
10. Declare dependencies for stateful apps
11. Pin images with `@sha256:` digest
12. Use OCIRepository with `chartRef` for new apps

---

## Usage Guidelines

**For AI Agents:**
- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**
- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

---

_Last Updated: 2025-12-28_
