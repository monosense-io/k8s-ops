# Story 0.2: Create Shared Infrastructure Base

Status: ready-for-dev

## Story

As a **platform operator**,
I want **shared infrastructure component definitions in a base directory**,
So that **both clusters can reference common CRDs, controllers, and repositories**.

## Acceptance Criteria

1. **Given** the repository structure from Story 0.1
   **When** shared infrastructure base is created
   **Then** `infrastructure/base/repositories/` contains:
   - `kustomization.yaml` listing all repository sources
   - `helm/` directory with HelmRepository definitions (bitnami, cilium, jetstack, etc.)
   - `oci/` directory with OCIRepository definitions (ghcr-flux, ghcr-sidero, etc.)

2. **And** repository definitions are valid Flux v2 resources

3. **And** `kustomize build infrastructure/base/repositories` succeeds without errors

## Tasks / Subtasks

- [ ] Task 1: Create repositories directory structure (AC: #1)
  - [ ] Create `infrastructure/base/repositories/` directory
  - [ ] Create `infrastructure/base/repositories/helm/` directory
  - [ ] Create `infrastructure/base/repositories/oci/` directory
  - [ ] Create `infrastructure/base/repositories/kustomization.yaml`

- [ ] Task 2: Create HelmRepository definitions (AC: #1, #2)
  - [ ] Create `helm/bitnami.yaml` - Bitnami Helm charts
  - [ ] Create `helm/cilium.yaml` - Cilium CNI charts
  - [ ] Create `helm/jetstack.yaml` - cert-manager charts
  - [ ] Create `helm/prometheus-community.yaml` - Prometheus/VictoriaMetrics charts
  - [ ] Create `helm/rook-ceph.yaml` - Rook-Ceph charts
  - [ ] Create `helm/external-secrets.yaml` - External Secrets charts
  - [ ] Create `helm/stakater.yaml` - Reloader charts
  - [ ] Create `helm/dragonfly.yaml` - Dragonfly charts
  - [ ] Create `helm/strimzi.yaml` - Strimzi Kafka charts
  - [ ] Create `helm/cnpg.yaml` - CloudNative PostgreSQL charts
  - [ ] Create `helm/authentik.yaml` - Authentik SSO charts
  - [ ] Create `helm/envoy-gateway.yaml` - Envoy Gateway charts

- [ ] Task 3: Create OCIRepository definitions (AC: #1, #2)
  - [ ] Create `oci/ghcr-flux.yaml` - Flux OCI images
  - [ ] Create `oci/ghcr-sidero.yaml` - Sidero/Talos OCI images
  - [ ] Create `oci/app-template.yaml` - bjw-s app-template
  - [ ] Create `oci/cloudflared.yaml` - Cloudflare Tunnel OCI
  - [ ] Create `oci/victoria-metrics.yaml` - VictoriaMetrics OCI charts
  - [ ] Create `oci/victoria-logs.yaml` - VictoriaLogs OCI charts
  - [ ] Create `oci/grafana.yaml` - Grafana OCI charts
  - [ ] Create `oci/external-dns.yaml` - External-DNS OCI charts

- [ ] Task 4: Create root kustomization.yaml for repositories (AC: #1)
  - [ ] Create `infrastructure/base/repositories/kustomization.yaml` listing all resources
  - [ ] Use `kustomize.config.k8s.io/v1beta1` API version

- [ ] Task 5: Validate Kustomize build (AC: #3)
  - [ ] Run `kustomize build infrastructure/base/repositories`
  - [ ] Verify all resources are valid Flux v2 resources
  - [ ] Fix any validation errors

## Dev Notes

### Architecture Patterns & Constraints

**Repository Structure (from Architecture doc):**
```
infrastructure/
└── base/                               # Shared infrastructure
    └── repositories/                   # Shared HelmRepository/OCIRepository
        ├── kustomization.yaml
        ├── helm/
        │   ├── bitnami.yaml
        │   ├── cilium.yaml
        │   └── jetstack.yaml
        └── oci/
            ├── ghcr-flux.yaml
            └── ghcr-sidero.yaml
```

**Critical Implementation Rules:**

1. **File naming:** Use `kustomization.yaml` (NOT `.yml`) - this is enforced across the entire repository
2. **API versions:**
   - HelmRepository: `source.toolkit.fluxcd.io/v1`
   - OCIRepository: `source.toolkit.fluxcd.io/v1beta2`
   - Kustomization: `kustomize.config.k8s.io/v1beta1`
3. **Namespace:** All repositories should be in `flux-system` namespace
4. **Naming convention:** kebab-case for all resource names

**Chart Source Pattern (from project-context.md):**
- **Prefer OCIRepository** with `chartRef` for all new apps
- HelmRepository only for charts not available as OCI
- OCIRepository needs `layerSelector` for Helm charts:
```yaml
layerSelector:
  mediaType: application/vnd.cncf.helm.chart.content.v1.tar+gzip
  operation: copy
```

### Technology Stack Versions

| Component | Version | Chart Source |
|-----------|---------|--------------|
| Cilium | v1.18.5 | HelmRepository (quay.io) |
| Flux CD | v2.7.5 | OCIRepository (ghcr.io) |
| cert-manager | v1.19.2 | HelmRepository (charts.jetstack.io) |
| External Secrets | v1.0.0 | HelmRepository |
| Rook-Ceph | v1.18.8 | HelmRepository |
| OpenEBS | v4.4 | HelmRepository |
| Envoy Gateway | v1.6.1 | HelmRepository |
| VictoriaMetrics | v1.131.0 | OCIRepository (ghcr.io) |
| CloudNative-PG | Latest | HelmRepository |
| Dragonfly | v1.3.0 | HelmRepository |
| Grafana | Latest | OCIRepository (ghcr.io) |

### HelmRepository Template

```yaml
---
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: <repo-name>
  namespace: flux-system
spec:
  interval: 5m
  url: https://<repository-url>
```

### OCIRepository Template (for Helm charts)

```yaml
---
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: OCIRepository
metadata:
  name: <repo-name>
  namespace: flux-system
spec:
  interval: 5m
  url: oci://<registry>/<path>
  layerSelector:
    mediaType: application/vnd.cncf.helm.chart.content.v1.tar+gzip
    operation: copy
```

### OCIRepository Template (for container images)

```yaml
---
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: OCIRepository
metadata:
  name: <repo-name>
  namespace: flux-system
spec:
  interval: 5m
  url: oci://<registry>/<path>
```

### Known Repository URLs

**HelmRepository URLs:**
| Repository | URL |
|------------|-----|
| bitnami | https://charts.bitnami.com/bitnami |
| cilium | https://helm.cilium.io |
| jetstack (cert-manager) | https://charts.jetstack.io |
| prometheus-community | https://prometheus-community.github.io/helm-charts |
| rook-release | https://charts.rook.io/release |
| external-secrets | https://charts.external-secrets.io |
| stakater | https://stakater.github.io/stakater-charts |
| dragonfly | https://dragonflydb.github.io/helm-charts |
| strimzi | https://strimzi.io/charts |
| cnpg | https://cloudnative-pg.github.io/charts |
| authentik | https://charts.goauthentik.io |
| envoy-gateway | oci://docker.io/envoyproxy/gateway-helm |
| openebs | https://openebs.github.io/openebs |

**OCIRepository URLs:**
| Repository | URL |
|------------|-----|
| ghcr-flux | oci://ghcr.io/fluxcd |
| ghcr-sidero | oci://ghcr.io/siderolabs |
| app-template | oci://ghcr.io/bjw-s/helm |
| cloudflared | oci://ghcr.io/cloudflare |
| victoria-metrics | oci://ghcr.io/victoriametrics/helm-charts |
| grafana | oci://ghcr.io/grafana/helm-charts |
| external-dns | oci://ghcr.io/external-dns/external-dns |

### Project Structure Notes

**Dependency in Flux Kustomization hierarchy:**
The repositories will be referenced by:
- `clusters/infra/flux/repositories/kustomization.yaml` → references `../../../../infrastructure/base/repositories`
- `clusters/apps/flux/repositories/kustomization.yaml` → references `../../../../infrastructure/base/repositories`

**From architecture.md - Flux Kustomization Hierarchy:**
```
clusters/{cluster}/flux/kustomization.yaml
    │
    └── references → repositories/kustomization.yaml
                         └── resources: - ../../../../infrastructure/base/repositories
```

### References

- [Source: docs/project-context.md#Chart Source Pattern]
- [Source: docs/project-context.md#Kubernetes/GitOps Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure]
- [Source: _bmad-output/planning-artifacts/architecture.md#Technology Stack]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 0.2: Create Shared Infrastructure Base]

### Previous Story Intelligence (Story 0.1)

**From Story 0.1 - Initialize Repository Structure:**
- Repository is not yet initialized as a Git repo
- Directory structure is planned but not created
- This story depends on Story 0.1 being completed first
- Use exact directory structure from architecture document

**Key learnings from 0.1 design:**
- All `.yaml` files should use `.yaml` extension (not `.yml`)
- Follow kebab-case naming for all directories and files
- Maintain structure exactly as specified in architecture

### Kustomization.yaml Pattern

```yaml
---
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - helm/bitnami.yaml
  - helm/cilium.yaml
  - helm/jetstack.yaml
  # ... list all helm/*.yaml files
  - oci/ghcr-flux.yaml
  - oci/ghcr-sidero.yaml
  # ... list all oci/*.yaml files
```

### Validation Commands

```bash
# Validate the repositories kustomization builds successfully
kustomize build infrastructure/base/repositories

# Validate individual YAML files
kubectl apply --dry-run=client -f infrastructure/base/repositories/helm/bitnami.yaml

# Validate all files in a directory
for f in infrastructure/base/repositories/helm/*.yaml; do
  kubectl apply --dry-run=client -f "$f"
done
```

### Git Commit Message Format

```
feat(infra): create shared infrastructure base with repository definitions

- Add HelmRepository definitions for Helm chart sources
- Add OCIRepository definitions for OCI-based charts
- Create kustomization.yaml for repository aggregation
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
