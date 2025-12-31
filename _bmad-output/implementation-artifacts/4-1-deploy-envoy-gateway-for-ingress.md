# Story 4.1: Deploy Envoy Gateway for Ingress

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform operator,
I want Envoy Gateway managing ingress via Gateway API,
so that applications can expose HTTP routes with consistent configuration.

## Acceptance Criteria

1. **AC1**: `kubernetes/apps/networking/envoy-gateway/` directory exists with:
   - `app/` directory containing operator HelmRelease
   - `ks.yaml` Flux Kustomization entry point
   - Properly structured `kustomization.yaml`

2. **AC2**: Envoy Gateway Operator HelmRelease is configured with:
   - Envoy Gateway v1.6.1
   - Proper remediation blocks (install retries: 3, upgrade strategy: rollback)
   - Interval: 1h (per project standards)

3. **AC3**: GatewayClass `envoy-gateway` resource is created and accepted by the controller

4. **AC4**: Two Gateway resources are configured:
   - `envoy-external` - for public internet traffic (via Cloudflare Tunnel)
   - `envoy-internal` - for internal services

5. **AC5**: Gateways reference wildcard TLS certificates from cert-manager:
   - External Gateway: `*.${CLUSTER_DOMAIN}` certificate
   - Certificate is issued and valid

6. **AC6**: Gateway reaches Ready status and is accepting connections

7. **AC7**: HTTPRoute resources can successfully reference the Gateway and route traffic

8. **AC8**: CiliumNetworkPolicy is created for Tier 1 platform service access patterns

## Tasks / Subtasks

- [ ] Task 1: Create Envoy Gateway directory structure (AC: #1)
  - [ ] Subtask 1.1: Create `kubernetes/apps/networking/envoy-gateway/app/` directory
  - [ ] Subtask 1.2: Create `kubernetes/apps/networking/envoy-gateway/ks.yaml` Flux Kustomization
  - [ ] Subtask 1.3: Create `kubernetes/apps/networking/envoy-gateway/app/kustomization.yaml`

- [ ] Task 2: Deploy Envoy Gateway Operator (AC: #2)
  - [ ] Subtask 2.1: Create HelmRelease for envoy-gateway controller
  - [ ] Subtask 2.2: Configure using OCIRepository with `chartRef` pattern (preferred)
  - [ ] Subtask 2.3: Ensure CRD handling with `install.crds: CreateReplace`
  - [ ] Subtask 2.4: Set namespace to `networking` (per project namespace patterns)

- [ ] Task 3: Create GatewayClass resource (AC: #3)
  - [ ] Subtask 3.1: Define GatewayClass `envoy-gateway` with controllerName `gateway.envoyproxy.io/gatewayclass-controller`
  - [ ] Subtask 3.2: Verify GatewayClass is accepted

- [ ] Task 4: Create Gateway resources (AC: #4, #5, #6)
  - [ ] Subtask 4.1: Create `envoy-external` Gateway for public traffic with HTTPS listener on port 443
  - [ ] Subtask 4.2: Create `envoy-internal` Gateway for internal traffic
  - [ ] Subtask 4.3: Reference wildcard certificate `${CLUSTER_DOMAIN}-tls` from cert-manager
  - [ ] Subtask 4.4: Configure Gateway with appropriate annotations for LoadBalancer IP allocation from Cilium pool

- [ ] Task 5: Configure network policies (AC: #8)
  - [ ] Subtask 5.1: Create CiliumNetworkPolicy allowing ingress from Cloudflare Tunnel
  - [ ] Subtask 5.2: Allow egress to backend services in application namespaces

- [ ] Task 6: Validate deployment (AC: #6, #7)
  - [ ] Subtask 6.1: Verify Gateway reaches Ready status
  - [ ] Subtask 6.2: Create test HTTPRoute and verify traffic routing
  - [ ] Subtask 6.3: Verify `kustomize build kubernetes/apps/networking/envoy-gateway --enable-helm` succeeds

## Dev Notes

### Architecture Context

**Technology Stack:**
- Envoy Gateway v1.6.1 (latest stable as of December 2025)
- Gateway API v1.4.1 (bundled with Envoy Gateway)
- cert-manager v1.19.2 for TLS certificate management
- Cilium BGP Control Plane for LoadBalancer IP allocation

**Domain Architecture (from project-context.md):**
| Cluster | Domain | Tunnel Origin | Envoy Gateway Service |
|---------|--------|---------------|----------------------|
| infra | `monosense.dev` | `external.monosense.dev` | `envoy-external` |
| apps | `monosense.io` | `external.monosense.io` | `envoy-gateway-external` |

**Key Architectural Decisions:**
1. This is a **shared app** deployed to BOTH clusters - use `kubernetes/apps/networking/envoy-gateway/`
2. Uses Gateway API (not Ingress) for modern routing capabilities
3. Two Gateways per cluster: external (public via Cloudflare) and internal
4. Tier 1 platform service - requires explicit CiliumNetworkPolicy

### Implementation Patterns

**Directory Structure:**
```
kubernetes/apps/networking/envoy-gateway/
├── app/
│   ├── helmrelease.yaml          # Envoy Gateway operator
│   ├── kustomization.yaml        # Local kustomization
│   ├── gatewayclass.yaml         # GatewayClass resource
│   ├── gateway-external.yaml     # External Gateway
│   ├── gateway-internal.yaml     # Internal Gateway
│   └── networkpolicy.yaml        # CiliumNetworkPolicy
└── ks.yaml                       # Flux Kustomization entry point
```

**HelmRelease Pattern (REQUIRED):**
```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: envoy-gateway
spec:
  interval: 1h
  chartRef:
    kind: OCIRepository
    name: envoy-gateway  # Define OCIRepository for this
    namespace: flux-system
  install:
    crds: CreateReplace
    remediation:
      retries: 3
  upgrade:
    crds: CreateReplace
    cleanupOnFail: true
    remediation:
      strategy: rollback
      retries: 3
```

**Gateway API Pattern:**
```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: envoy-external
  namespace: networking
spec:
  gatewayClassName: envoy-gateway
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      tls:
        mode: Terminate
        certificateRefs:
          - kind: Secret
            name: ${CLUSTER_DOMAIN}-tls  # From cert-manager
```

**HTTPRoute Gateway Reference (for apps to use):**
```yaml
parentRefs:
  - name: envoy-external  # or envoy-internal
    namespace: networking
    sectionName: https
```

### Flux Kustomization (ks.yaml) Pattern

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name envoy-gateway
  namespace: flux-system
spec:
  targetNamespace: networking
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./kubernetes/apps/networking/envoy-gateway/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: false
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  dependsOn:
    - name: cert-manager-issuers  # Need TLS certs
      namespace: flux-system
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

### Critical Implementation Rules

**From project-context.md - MUST FOLLOW:**
1. Use `kustomization.yaml` (not `.yml`) for all Kustomize files
2. Use `helm.toolkit.fluxcd.io/v2` API version (not v2beta1 or v2beta2)
3. Include remediation blocks in all HelmReleases
4. Use `${VARIABLE_NAME}` syntax for Flux substitution (NOT `$VAR` or `{{VAR}}`)
5. Use OCIRepository with `chartRef` for new apps (preferred pattern)
6. Pin images with `@sha256:` digest where possible
7. Use kebab-case for all resource names
8. Use `monosense.dev/` prefix for custom annotations

**Variable Substitution:**
- `${CLUSTER_DOMAIN}` - `monosense.dev` for infra, `monosense.io` for apps
- `${CLUSTER_NAME}` - `infra` or `apps`
- `${CLUSTER_ID}` - `1` for infra, `2` for apps

**Gateway Naming per Cluster:**
- Infra cluster: Gateway service name is `envoy-external`
- Apps cluster: Gateway service name is `envoy-gateway-external`
- This distinction is critical for Cloudflare Tunnel configuration

### Project Structure Notes

- **Location**: `kubernetes/apps/networking/envoy-gateway/` (shared app for BOTH clusters)
- **Namespace**: `networking`
- **Dependencies**: cert-manager (for TLS certificates)
- **Cilium Integration**: Gateway receives LoadBalancer IP from Cilium IP pool

### References

- [Source: docs/project-context.md#Gateway API Routing] - Gateway API patterns and naming
- [Source: docs/project-context.md#Technology Stack] - Envoy Gateway v1.6.1
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 5] - Network Policy patterns
- [Source: _bmad-output/planning-artifacts/architecture.md#App Location Rules] - Shared apps in kubernetes/apps/
- [Source: _bmad-output/planning-artifacts/architecture.md#Technology Stack] - Envoy Gateway v1.6.1, Gateway API v1.4.1
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.1] - Original acceptance criteria

### External Documentation

- [Envoy Gateway Official Docs](https://gateway.envoyproxy.io/docs/)
- [Envoy Gateway Quickstart](https://gateway.envoyproxy.io/docs/tasks/quickstart/)
- [Envoy Gateway v1.6.1 Release](https://github.com/envoyproxy/gateway/releases/tag/v1.6.1)
- [Gateway API Support](https://gateway.envoyproxy.io/v1.4/tasks/traffic/gatewayapi-support/)

### Latest Version Information (December 2025)

- **Envoy Gateway**: v1.6.1 (released December 5, 2025)
- **Gateway API CRDs**: v1.4.1 (bundled with Envoy Gateway)
- **Key Features in v1.6**:
  - Zone-aware load balancing
  - Admin console with resource exploration
  - Enhanced TLS configuration options
  - ClusterTrustBundle support
  - Improved HTTP/3 listener support

### Installation Methods

**Helm (Recommended for GitOps):**
```bash
helm install eg oci://docker.io/envoyproxy/gateway-helm --version v1.6.1 -n envoy-gateway-system --create-namespace
```

**Gateway API CRDs (if not bundled):**
```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.0/standard-install.yaml
```

### OCIRepository Configuration

Create OCIRepository for Envoy Gateway Helm chart:
```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: OCIRepository
metadata:
  name: envoy-gateway
  namespace: flux-system
spec:
  interval: 5m
  url: oci://docker.io/envoyproxy/gateway-helm
  layerSelector:
    mediaType: application/vnd.cncf.helm.chart.content.v1.tar+gzip
    operation: copy
  ref:
    tag: v1.6.1
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

