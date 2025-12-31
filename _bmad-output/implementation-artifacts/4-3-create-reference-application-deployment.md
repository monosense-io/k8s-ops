# Story 4.3: Create Reference Application Deployment

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform operator,
I want a reference application demonstrating all deployment patterns,
so that future applications follow consistent structure.

## Acceptance Criteria

1. **AC1**: `kubernetes/apps/observability/gatus/` directory exists with proper structure:
   - `app/` directory containing HelmRelease and all required manifests
   - `ks.yaml` Flux Kustomization entry point
   - Properly structured `kustomization.yaml` files

2. **AC2**: Gatus HelmRelease is configured with:
   - Latest stable version (v5.33.1 as of December 2025)
   - Proper remediation blocks (install retries: 3, upgrade strategy: rollback)
   - Interval: 1h (per project standards)
   - OCIRepository with `chartRef` pattern (preferred)

3. **AC3**: ExternalSecret for credentials is configured:
   - References 1Password via ClusterSecretStore `onepassword-connect`
   - Secret name follows `{app}-secret` pattern
   - Uses `external-secrets.io/v1` API version

4. **AC4**: HTTPRoute for external access is configured:
   - References `envoy-external` Gateway in `networking` namespace
   - Uses `${CLUSTER_DOMAIN}` variable substitution
   - Route hostname: `gatus.${CLUSTER_DOMAIN}`

5. **AC5**: CiliumNetworkPolicy for Tier 2 security is created:
   - Default deny with explicit ingress from Gateway
   - Egress allowed to monitored endpoints
   - Allow egress to DNS

6. **AC6**: ks.yaml uses `postBuild.substituteFrom` for cluster-vars:
   - References `cluster-vars` ConfigMap
   - Includes appropriate `dependsOn` declarations

7. **AC7**: Dependencies are declared via `spec.dependsOn`:
   - Depends on `envoy-gateway` (for ingress)
   - Depends on `external-secrets-stores` (for secrets)

8. **AC8**: Gatus is accessible via `gatus.${CLUSTER_DOMAIN}` and showing health checks

## Tasks / Subtasks

- [ ] Task 1: Create Gatus directory structure (AC: #1)
  - [ ] Subtask 1.1: Create `kubernetes/apps/observability/gatus/app/` directory
  - [ ] Subtask 1.2: Create `kubernetes/apps/observability/gatus/ks.yaml` Flux Kustomization
  - [ ] Subtask 1.3: Create `kubernetes/apps/observability/gatus/app/kustomization.yaml`

- [ ] Task 2: Create OCIRepository for Gatus (AC: #2)
  - [ ] Subtask 2.1: Create OCIRepository in `infrastructure/base/repositories/oci/` OR use app-template
  - [ ] Subtask 2.2: Configure `layerSelector` for Helm chart content type
  - [ ] Subtask 2.3: Reference appropriate OCI registry (TwiN or app-template pattern)

- [ ] Task 3: Deploy Gatus HelmRelease (AC: #2)
  - [ ] Subtask 3.1: Create HelmRelease for Gatus using app-template or dedicated chart
  - [ ] Subtask 3.2: Configure persistence for SQLite storage
  - [ ] Subtask 3.3: Set resource requests and limits
  - [ ] Subtask 3.4: Configure Prometheus metrics endpoint if needed

- [ ] Task 4: Create ExternalSecret (AC: #3)
  - [ ] Subtask 4.1: Create ExternalSecret `gatus-secret` referencing 1Password
  - [ ] Subtask 4.2: Use `external-secrets.io/v1` API version
  - [ ] Subtask 4.3: Configure refreshInterval to 1h

- [ ] Task 5: Create HTTPRoute (AC: #4)
  - [ ] Subtask 5.1: Create HTTPRoute for `gatus.${CLUSTER_DOMAIN}`
  - [ ] Subtask 5.2: Reference `envoy-external` Gateway with sectionName `https`
  - [ ] Subtask 5.3: Configure backend service reference

- [ ] Task 6: Create CiliumNetworkPolicy (AC: #5)
  - [ ] Subtask 6.1: Create default-deny ingress policy
  - [ ] Subtask 6.2: Allow ingress from Gateway namespace
  - [ ] Subtask 6.3: Allow egress to monitored service endpoints
  - [ ] Subtask 6.4: Allow egress to DNS (kube-dns)

- [ ] Task 7: Create Flux Kustomization (AC: #6, #7)
  - [ ] Subtask 7.1: Create `ks.yaml` with proper structure
  - [ ] Subtask 7.2: Configure `dependsOn` for envoy-gateway and external-secrets-stores
  - [ ] Subtask 7.3: Configure `postBuild.substituteFrom` for cluster-vars

- [ ] Task 8: Configure Gatus Health Checks (AC: #8)
  - [ ] Subtask 8.1: Create ConfigMap for Gatus configuration (ConfigMap approach per project standards)
  - [ ] Subtask 8.2: Define health check endpoints for core services
  - [ ] Subtask 8.3: Configure alerting if needed

- [ ] Task 9: Validate Deployment (AC: #8)
  - [ ] Subtask 9.1: Verify `kustomize build kubernetes/apps/observability/gatus --enable-helm` succeeds
  - [ ] Subtask 9.2: Verify Gatus pod is running
  - [ ] Subtask 9.3: Verify `gatus.${CLUSTER_DOMAIN}` is accessible
  - [ ] Subtask 9.4: Verify health checks are executing

## Dev Notes

### Architecture Context

**Technology Stack:**
- Gatus v5.33.1 (latest stable as of December 2025)
- Key Features: gRPC health endpoints, SSH private-key support, customizable dashboard, Markdown announcements
- Storage: SQLite (persistent) or PostgreSQL (optional)
- Prometheus metrics enabled for observability integration

**Purpose of This Story:**
This is a **reference application** that demonstrates ALL deployment patterns that future applications should follow. It serves as a template for:
- Directory structure
- HelmRelease configuration
- ExternalSecret integration
- HTTPRoute configuration
- CiliumNetworkPolicy for Tier 2 apps
- Flux Kustomization with dependencies

### Previous Story Context (Stories 4.1 & 4.2)

**Story 4.1 - Envoy Gateway Learnings:**
- Uses OCIRepository with `chartRef` pattern (preferred for new apps)
- Gateway naming: `envoy-external` (infra) / `envoy-gateway-external` (apps)
- HTTPRoute parentRefs must include `sectionName: https`
- Follows shared app structure in `kubernetes/apps/`

**Story 4.2 - CNPG Learnings:**
- Operators use `install.remediation.retries: -1`
- Regular apps use `install.remediation.retries: 3`
- healthCheckExprs for CRD-based resources
- Separate ks.yaml for operator vs cluster resources

### Implementation Patterns

**Directory Structure (Reference Pattern):**
```
kubernetes/apps/observability/gatus/
├── app/
│   ├── helmrelease.yaml          # HelmRelease definition
│   ├── kustomization.yaml        # Local kustomization
│   ├── externalsecret.yaml       # 1Password secret reference
│   ├── networkpolicy.yaml        # CiliumNetworkPolicy (Tier 2)
│   ├── httproute.yaml            # Gateway API route
│   └── configmap.yaml            # Gatus health check configuration
└── ks.yaml                       # Flux Kustomization entry point
```

**HelmRelease Pattern (REQUIRED - Standard App):**
```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: gatus
spec:
  interval: 1h
  chartRef:
    kind: OCIRepository
    name: app-template  # Using app-template pattern
    namespace: flux-system
  install:
    remediation:
      retries: 3
  upgrade:
    cleanupOnFail: true
    remediation:
      strategy: rollback
      retries: 3
  values:
    controllers:
      main:
        containers:
          main:
            image:
              repository: ghcr.io/twin/gatus
              tag: v5.33.1@sha256:<digest>  # Pin with digest
```

**ExternalSecret Pattern (REQUIRED):**
```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: gatus-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword-connect
  target:
    name: gatus-secret
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: gatus
```

**HTTPRoute Pattern (REQUIRED):**
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: gatus
spec:
  hostnames:
    - gatus.${CLUSTER_DOMAIN}
  parentRefs:
    - name: envoy-external
      namespace: networking
      sectionName: https
  rules:
    - backendRefs:
        - name: gatus
          port: 8080
```

**CiliumNetworkPolicy Pattern (REQUIRED for Tier 2):**
```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: gatus
spec:
  endpointSelector:
    matchLabels:
      app.kubernetes.io/name: gatus
  ingress:
    - fromEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: networking
  egress:
    - toEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: kube-system
            k8s-app: kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: UDP
    - toFQDNs:
        - matchPattern: "*.${CLUSTER_DOMAIN}"
```

**Flux Kustomization Pattern (ks.yaml):**
```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name gatus
  namespace: flux-system
spec:
  targetNamespace: observability
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./kubernetes/apps/observability/gatus/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: false
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  dependsOn:
    - name: envoy-gateway
      namespace: flux-system
    - name: external-secrets-stores
      namespace: flux-system
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

**Gatus ConfigMap Pattern (per project-context.md):**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gatus-config
  labels:
    gatus.io/enabled: "true"
data:
  config.yaml: |
    storage:
      type: sqlite
      path: /data/data.db
    endpoints:
      - name: CNPG PostgreSQL
        url: tcp://postgres-rw.databases.svc.cluster.local:5432
        interval: 5m
        conditions:
          - "[CONNECTED] == true"
      - name: Envoy Gateway
        url: https://envoy-external.networking.svc.cluster.local:443
        interval: 5m
        conditions:
          - "[STATUS] == 200"
```

### Critical Implementation Rules

**From project-context.md - MUST FOLLOW:**
1. Use `kustomization.yaml` (not `.yml`) for all Kustomize files
2. Use `helm.toolkit.fluxcd.io/v2` API version (not v2beta1 or v2beta2)
3. Use `external-secrets.io/v1` API version (ESO v1.0.0+)
4. Include remediation blocks in all HelmReleases
5. Use `${VARIABLE_NAME}` syntax for Flux substitution (NOT `$VAR` or `{{VAR}}`)
6. Use OCIRepository with `chartRef` for new apps (preferred pattern)
7. Pin images with `@sha256:` digest where possible
8. Use kebab-case for all resource names
9. Use `monosense.dev/` prefix for custom annotations
10. Include CiliumNetworkPolicy for Tier 2 applications
11. Declare dependencies for stateful apps
12. Use ConfigMap approach for Gatus health checks

**Variable Substitution:**
- `${CLUSTER_DOMAIN}` - `monosense.dev` for infra, `monosense.io` for apps
- `${CLUSTER_NAME}` - `infra` or `apps`
- `${CLUSTER_ID}` - `1` for infra, `2` for apps

**App Location Rules:**
| Deployment Target | Directory |
|-------------------|-----------|
| Both clusters | `kubernetes/apps/{category}/{app}/` |
| Infra cluster only | `clusters/infra/apps/{category}/{app}/` |
| Apps cluster only | `clusters/apps/apps/{category}/{app}/` |

Gatus is a **shared app** deployed to BOTH clusters → `kubernetes/apps/observability/gatus/`

### Project Structure Notes

- **Location**: `kubernetes/apps/observability/gatus/` (shared app for BOTH clusters)
- **Namespace**: `observability`
- **Dependencies**: envoy-gateway (for HTTPRoute), external-secrets-stores (for credentials)
- **Dependents**: None directly, but serves as template for all future apps

### Gateway Naming per Cluster (CRITICAL)

| Cluster | Gateway Name | Service Name |
|---------|--------------|--------------|
| infra | `envoy-external` | `envoy-external` |
| apps | `envoy-external` | `envoy-gateway-external` |

HTTPRoute must reference `envoy-external` Gateway in both cases.

### Gatus Configuration Patterns

**Health Check Types Supported:**
- HTTP/HTTPS endpoints
- TCP connections
- ICMP ping
- DNS resolution
- gRPC health endpoints (new in v5.31)
- SSH connections (new in v5.33)
- TLS/STARTTLS certificate checks

**Storage Options:**
- SQLite (default, requires persistence)
- PostgreSQL (optional, for HA setups)

**Prometheus Integration:**
```yaml
values:
  serviceMonitor:
    enabled: true
```

### Reloader Integration

For automatic pod restart on ConfigMap changes:
```yaml
annotations:
  reloader.stakater.com/auto: "true"
```

### References

- [Source: docs/project-context.md#Application Directory Structure] - Directory structure pattern
- [Source: docs/project-context.md#HelmRelease Standards] - Remediation blocks
- [Source: docs/project-context.md#Gateway API Routing] - HTTPRoute patterns
- [Source: docs/project-context.md#Critical Don't-Miss Rules] - Anti-patterns to avoid
- [Source: _bmad-output/planning-artifacts/architecture.md#App Location Rules] - Shared apps location
- [Source: _bmad-output/planning-artifacts/architecture.md#Pattern Examples] - Good examples
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.3] - Original acceptance criteria
- [Source: _bmad-output/implementation-artifacts/4-1-deploy-envoy-gateway-for-ingress.md] - Gateway patterns
- [Source: _bmad-output/implementation-artifacts/4-2-deploy-cloudnative-pg-operator-and-shared-cluster.md] - Operator patterns

### External Documentation

- [Gatus Official Docs](https://gatus.io/docs/)
- [Gatus GitHub](https://github.com/TwiN/gatus)
- [Gatus v5.33.1 Release](https://github.com/TwiN/gatus/releases/tag/v5.33.1)
- [TwiN Helm Chart](https://artifacthub.io/packages/helm/twin/gatus)
- [bjw-s app-template](https://github.com/bjw-s/helm-charts/tree/main/charts/library/common)

### Latest Version Information (December 2025)

- **Gatus**: v5.33.1 (released December 11, 2024)
- **Key Features in v5.33**:
  - SSH private-key support for client authentication
  - Customizable dashboard headings
  - Archived announcements with past section
  - Markdown formatting for announcements
  - gRPC health endpoint monitoring
  - Modernized response time charts
  - Human-readable certificate expiration formatting

### Verification Commands

```bash
# Validate kustomize build
kustomize build kubernetes/apps/observability/gatus --enable-helm

# Check pod status
kubectl get pods -n observability -l app.kubernetes.io/name=gatus

# Check HelmRelease status
kubectl get hr -n observability gatus

# Check HTTPRoute
kubectl get httproute -n observability gatus

# Test external access
curl -I https://gatus.${CLUSTER_DOMAIN}
```

### Component Usage Example

This story creates a reference that OTHER apps should follow. Key patterns:

**For Database-backed Apps (e.g., Odoo):**
```yaml
# ks.yaml
dependsOn:
  - name: cloudnative-pg-cluster
    namespace: flux-system
  - name: envoy-gateway
    namespace: flux-system
healthCheckExprs:
  - apiVersion: postgresql.cnpg.io/v1
    kind: Cluster
    failed: status.conditions.filter(e, e.type == 'Ready').all(e, e.status == 'False')
components:
  - ../../../../kubernetes/components/cnpg
  - ../../../../kubernetes/components/volsync/r2
```

**For SSO-integrated Apps:**
```yaml
dependsOn:
  - name: authentik
    namespace: flux-system
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

