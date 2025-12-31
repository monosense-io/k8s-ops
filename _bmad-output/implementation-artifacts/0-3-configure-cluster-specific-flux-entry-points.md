# Story 0.3: Configure Cluster-Specific Flux Entry Points

Status: ready-for-dev

## Story

As a **platform operator**,
I want **cluster-specific Flux configuration directories**,
So that **each cluster can reference shared bases while maintaining its own configuration**.

## Acceptance Criteria

1. **Given** the shared infrastructure base from Story 0.2
   **When** cluster Flux entry points are configured
   **Then** `clusters/infra/flux/` contains:
   - `kustomization.yaml` as root Flux entry point
   - `cluster-vars.yaml` ConfigMap with CLUSTER_NAME=infra, CLUSTER_ID=1, CLUSTER_DOMAIN=monosense.dev
   - `config/` directory with `cluster-infrastructure.yaml`, `cluster-apps.yaml`, `cluster-local.yaml`
   - `repositories/kustomization.yaml` referencing `infrastructure/base/repositories`

2. **And** `clusters/apps/flux/` contains equivalent structure with CLUSTER_NAME=apps, CLUSTER_ID=2

3. **And** `kustomize build clusters/infra/flux` succeeds

4. **And** `kustomize build clusters/apps/flux` succeeds

## Tasks / Subtasks

- [ ] Task 1: Create infra cluster Flux directory structure (AC: #1)
  - [ ] Create `clusters/infra/flux/` directory (if not exists)
  - [ ] Create `clusters/infra/flux/config/` directory
  - [ ] Create `clusters/infra/flux/repositories/` directory

- [ ] Task 2: Create infra cluster-vars ConfigMap (AC: #1)
  - [ ] Create `clusters/infra/flux/cluster-vars.yaml` with cluster-specific variables
  - [ ] Set CLUSTER_NAME=infra, CLUSTER_ID=1, CLUSTER_DOMAIN=monosense.dev
  - [ ] Set CLUSTER_CIDR=10.25.11.0/24
  - [ ] Set CLUSTER_POD_CIDR=10.42.0.0/16, CLUSTER_SVC_CIDR=10.43.0.0/16
  - [ ] Set CLUSTER_API_ENDPOINT=https://10.25.11.10:6443
  - [ ] Set OBSERVABILITY_ROLE=hub

- [ ] Task 3: Create infra cluster Flux Kustomizations (AC: #1)
  - [ ] Create `clusters/infra/flux/config/cluster-infrastructure.yaml` Flux Kustomization
  - [ ] Create `clusters/infra/flux/config/cluster-apps.yaml` Flux Kustomization
  - [ ] Create `clusters/infra/flux/config/cluster-local.yaml` Flux Kustomization
  - [ ] Ensure proper dependency chain: repositories → infrastructure → apps → local

- [ ] Task 4: Create infra repositories reference (AC: #1)
  - [ ] Create `clusters/infra/flux/repositories/kustomization.yaml`
  - [ ] Reference `../../../../infrastructure/base/repositories` as resource

- [ ] Task 5: Create infra root kustomization.yaml (AC: #1)
  - [ ] Create `clusters/infra/flux/kustomization.yaml` as root entry point
  - [ ] Include cluster-vars.yaml
  - [ ] Include repositories directory
  - [ ] Include config directory resources

- [ ] Task 6: Create apps cluster Flux directory structure (AC: #2)
  - [ ] Create `clusters/apps/flux/` directory (if not exists)
  - [ ] Create `clusters/apps/flux/config/` directory
  - [ ] Create `clusters/apps/flux/repositories/` directory

- [ ] Task 7: Create apps cluster-vars ConfigMap (AC: #2)
  - [ ] Create `clusters/apps/flux/cluster-vars.yaml` with cluster-specific variables
  - [ ] Set CLUSTER_NAME=apps, CLUSTER_ID=2, CLUSTER_DOMAIN=monosense.dev
  - [ ] Set CLUSTER_CIDR=10.25.13.0/24
  - [ ] Set CLUSTER_POD_CIDR=10.44.0.0/16, CLUSTER_SVC_CIDR=10.45.0.0/16
  - [ ] Set CLUSTER_API_ENDPOINT=https://10.25.13.10:6443
  - [ ] Set OBSERVABILITY_ROLE=spoke
  - [ ] Set OBSERVABILITY_TARGET=http://vmsingle.observability.svc.infra.local:8429

- [ ] Task 8: Create apps cluster Flux Kustomizations (AC: #2)
  - [ ] Create `clusters/apps/flux/config/cluster-infrastructure.yaml` Flux Kustomization
  - [ ] Create `clusters/apps/flux/config/cluster-apps.yaml` Flux Kustomization
  - [ ] Create `clusters/apps/flux/config/cluster-local.yaml` Flux Kustomization
  - [ ] Ensure proper dependency chain matching infra cluster

- [ ] Task 9: Create apps repositories reference (AC: #2)
  - [ ] Create `clusters/apps/flux/repositories/kustomization.yaml`
  - [ ] Reference `../../../../infrastructure/base/repositories` as resource

- [ ] Task 10: Create apps root kustomization.yaml (AC: #2)
  - [ ] Create `clusters/apps/flux/kustomization.yaml` as root entry point
  - [ ] Include cluster-vars.yaml
  - [ ] Include repositories directory
  - [ ] Include config directory resources

- [ ] Task 11: Validate Kustomize builds (AC: #3, #4)
  - [ ] Run `kustomize build clusters/infra/flux` - must succeed
  - [ ] Run `kustomize build clusters/apps/flux` - must succeed
  - [ ] Fix any validation errors

## Dev Notes

### Architecture Patterns & Constraints

**Flux Kustomization Hierarchy (from Architecture doc):**
```
clusters/{cluster}/flux/kustomization.yaml
    │
    ├── references → config/cluster-infrastructure.yaml
    │                    └── path: ./infrastructure/base
    │                    └── dependsOn: [repositories]
    │
    ├── references → config/cluster-apps.yaml
    │                    └── path: ./kubernetes/apps
    │                    └── dependsOn: [cluster-infrastructure]
    │
    └── references → config/cluster-local.yaml
                         └── path: ./clusters/{cluster}/apps
                         └── dependsOn: [cluster-apps]
```

**Critical Implementation Rules:**

1. **File naming:** Use `kustomization.yaml` (NOT `.yml`) - enforced across entire repository
2. **API versions:**
   - Flux Kustomization: `kustomize.toolkit.fluxcd.io/v1`
   - Kustomize: `kustomize.config.k8s.io/v1beta1`
   - ConfigMap: `v1`
3. **Namespace:** All Flux resources in `flux-system` namespace
4. **Variable substitution:** Use `${VARIABLE_NAME}` syntax (NOT `$VAR` or `{{VAR}}`)
5. **Dependencies:** Use `dependsOn` for proper ordering

### Cluster Variables ConfigMap Template

**Infra Cluster (from Architecture doc):**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-vars
  namespace: flux-system
data:
  CLUSTER_NAME: infra
  CLUSTER_ID: "1"
  CLUSTER_DOMAIN: monosense.dev
  CLUSTER_CIDR: 10.25.11.0/24
  CLUSTER_POD_CIDR: 10.42.0.0/16
  CLUSTER_SVC_CIDR: 10.43.0.0/16
  CLUSTER_API_ENDPOINT: https://10.25.11.10:6443
  OBSERVABILITY_ROLE: hub
```

**Apps Cluster (from Architecture doc):**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-vars
  namespace: flux-system
data:
  CLUSTER_NAME: apps
  CLUSTER_ID: "2"
  CLUSTER_DOMAIN: monosense.dev
  CLUSTER_CIDR: 10.25.13.0/24
  CLUSTER_POD_CIDR: 10.44.0.0/16
  CLUSTER_SVC_CIDR: 10.45.0.0/16
  CLUSTER_API_ENDPOINT: https://10.25.13.10:6443
  OBSERVABILITY_ROLE: spoke
  OBSERVABILITY_TARGET: http://vmsingle.observability.svc.infra.local:8429
```

### Flux Kustomization Standard Template

**From project-context.md:**
```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name cluster-infrastructure
  namespace: flux-system
spec:
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  prune: true
  wait: false
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  path: ./infrastructure/base
  dependsOn:
    - name: repositories
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

### postBuild.substituteFrom Pattern (from FluxCD docs)

The `substituteFrom` field allows loading variables from ConfigMaps and Secrets:
- ConfigMap/Secret data keys become variable names
- Use `optional: true` to tolerate missing ConfigMaps
- Variables in manifests use `${VARIABLE_NAME}` format
- Default values: `${var:=default}` syntax supported
- Later values overwrite earlier ones when multiple sources specified

**Reference:** [FluxCD Kustomization postBuild](https://fluxcd.io/flux/components/kustomize/kustomizations/)

### Repositories Reference Pattern

**From Story 0.2:**
```yaml
# clusters/infra/flux/repositories/kustomization.yaml
---
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../../../infrastructure/base/repositories
```

### Dependency Chain Requirements

1. **repositories** - Must be deployed first (Helm/OCI sources)
2. **cluster-infrastructure** - Depends on repositories (shared CRDs, controllers)
3. **cluster-apps** - Depends on cluster-infrastructure (shared apps)
4. **cluster-local** - Depends on cluster-apps (cluster-specific apps)

### Project Structure Notes

**Directory Structure to Create:**
```
clusters/
├── infra/
│   └── flux/
│       ├── kustomization.yaml          # Root entry point
│       ├── cluster-vars.yaml           # Cluster variables ConfigMap
│       ├── config/
│       │   ├── cluster-infrastructure.yaml
│       │   ├── cluster-apps.yaml
│       │   └── cluster-local.yaml
│       └── repositories/
│           └── kustomization.yaml      # References shared repos
└── apps/
    └── flux/
        ├── kustomization.yaml
        ├── cluster-vars.yaml
        ├── config/
        │   ├── cluster-infrastructure.yaml
        │   ├── cluster-apps.yaml
        │   └── cluster-local.yaml
        └── repositories/
            └── kustomization.yaml
```

### Observability Role Difference

| Cluster | OBSERVABILITY_ROLE | Behavior |
|---------|-------------------|----------|
| infra | `hub` | Full VictoriaMetrics stack (storage, query, alerting) |
| apps | `spoke` | VMAgent + Fluent-bit (collection only, remote-write to infra) |

### Network Configuration

| Cluster | CIDR | Pod CIDR | Service CIDR | API Endpoint |
|---------|------|----------|--------------|--------------|
| infra | 10.25.11.0/24 | 10.42.0.0/16 | 10.43.0.0/16 | https://10.25.11.10:6443 |
| apps | 10.25.13.0/24 | 10.44.0.0/16 | 10.45.0.0/16 | https://10.25.13.10:6443 |

### References

- [Source: docs/project-context.md#Kubernetes/GitOps Patterns]
- [Source: docs/project-context.md#Flux Variable Substitution]
- [Source: _bmad-output/planning-artifacts/architecture.md#Cluster Variables (cluster-vars.yaml)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Flux Kustomization Hierarchy]
- [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 0.3: Configure Cluster-Specific Flux Entry Points]
- [FluxCD Kustomization docs](https://fluxcd.io/flux/components/kustomize/kustomizations/)
- [FluxCD Multi-cluster Architecture](https://medium.com/@stefanprodan/fluxcd-multi-cluster-architecture-e426fb2bca0f)

### Previous Story Intelligence

**From Story 0.1 - Initialize Repository Structure:**
- Repository structure established with `clusters/infra/` and `clusters/apps/` directories
- Directory naming follows kebab-case convention
- All YAML files use `.yaml` extension

**From Story 0.2 - Create Shared Infrastructure Base:**
- `infrastructure/base/repositories/` contains HelmRepository and OCIRepository definitions
- Repositories are in `flux-system` namespace
- Use `kustomize.config.k8s.io/v1beta1` for local kustomization.yaml files
- Relative path reference: `../../../../infrastructure/base/repositories`

**Key Learnings from Previous Stories:**
- Strict adherence to `.yaml` extension (never `.yml`)
- All Flux resources go in `flux-system` namespace
- Use exact directory structure from architecture document
- Validate with `kustomize build` before considering complete

### Staged Rollout Configuration

| Cluster | Branch | Reconciliation |
|---------|--------|----------------|
| infra | `main` | Immediate |
| apps | `release` | 24h delayed (auto fast-forward) |

**Note:** The apps cluster Flux configuration will reference the `release` branch in the GitRepository source, enabling staged rollout pattern.

### Validation Commands

```bash
# Validate infra cluster Flux entry point
kustomize build clusters/infra/flux

# Validate apps cluster Flux entry point
kustomize build clusters/apps/flux

# Check for YAML syntax errors
for f in clusters/*/flux/**/*.yaml; do
  yamllint "$f" 2>/dev/null || echo "Check: $f"
done
```

### Git Commit Message Format

```
feat(flux): configure cluster-specific Flux entry points

- Add cluster-vars ConfigMap for infra and apps clusters
- Create Flux Kustomization hierarchy (infrastructure → apps → local)
- Reference shared repositories from infrastructure/base
- Enable postBuild variable substitution from cluster-vars
```

### Common Gotchas

1. **Flux substitution syntax** - Use `${VAR}` NOT `$VAR` or `{{VAR}}`
2. **kustomization.yaml** - Use `.yaml` extension, never `.yml`
3. **CLUSTER_ID must be string** - Quote the number: `"1"` not `1`
4. **Namespace is flux-system** - All Flux resources must be in this namespace
5. **dependsOn uses name only** - Reference by name, not full metadata
6. **sourceRef.name matches GitRepository** - Must match the bootstrapped GitRepository name (typically `k8s-ops` or `flux-system`)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

