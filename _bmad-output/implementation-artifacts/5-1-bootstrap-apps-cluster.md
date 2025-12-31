# Story 5.1: Bootstrap Apps Cluster

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform operator,
I want the apps cluster bootstrapped using the same patterns as infra,
so that I have a consistent second cluster for business applications.

## Acceptance Criteria

1. **AC1**: `clusters/apps/talos/` contains machine configs for nodes 10.25.13.11-16:
   - `talconfig.yaml` with cluster settings (name: apps, endpoint: 10.25.13.10, nodes: 10.25.13.11-16)
   - `clusterconfig/` directory with generated machine configs (encrypted with SOPS)
   - `patches/` directory for node-specific customizations
   - talconfig.yaml specifies Talos v1.12.0, Kubernetes v1.35.0
   - Network configuration includes MTU 9000, LACP bonding (matching infra pattern)
   - `talhelper genconfig` produces valid machine configurations
   - Secrets are encrypted in `talsecret.sops.yaml`

2. **AC2**: `bootstrap/apps/` mirrors infra bootstrap with cluster.id=2, cluster.name=apps:
   - `helmfile.d/00-crds.yaml` installing CRDs separately (Cilium, cert-manager, Gateway API)
   - `helmfile.d/01-apps.yaml` with dependency chain: Cilium → CoreDNS → Spegel → cert-manager → Flux
   - `templates/values.yaml.gotmpl` extracts values from HelmRelease pattern
   - `secrets.yaml.tpl` references 1Password secrets
   - Cilium configured with cluster.id=2, cluster.name=apps, eBPF native routing
   - GitHub deploy key in `github-deploy-key.sops.yaml`

3. **AC3**: `task bootstrap:apps` successfully bootstraps the cluster:
   - Talos control plane is bootstrapped via `talosctl bootstrap`
   - kubeconfig is generated via `talosctl kubeconfig`
   - helmfile installs components in order: CRDs → Cilium → CoreDNS → Spegel → cert-manager → Flux
   - Flux connects to GitHub repository using deploy key
   - Bootstrap completes within 30 minutes (NFR2)

4. **AC4**: Flux connects to repository using `release` branch (not `main`):
   - `clusters/apps/flux/kustomization.yaml` references `release` branch
   - GitRepository resource configured for `release` branch reconciliation
   - Verify with `flux get sources git -n flux-system`

5. **AC5**: `flux check` passes on apps cluster:
   - All Flux controllers are healthy and running
   - Source controller successfully connected to GitRepository
   - Kustomize controller successfully reconciling

6. **AC6**: Shared infrastructure from `infrastructure/base/` is deployed:
   - Repositories from `infrastructure/base/repositories/` are available
   - cert-manager issuers deployed and Ready
   - External Secrets Operator syncing from 1Password
   - Rook-Ceph cluster initialized (if applicable to apps cluster)

7. **AC7**: Cilium connectivity tests pass:
   - `cilium --context apps connectivity test` passes
   - BGP session establishes with upstream router (Juniper SRX 320)
   - `cilium bgp peers` shows established session

8. **AC8**: Apps cluster cluster-vars ConfigMap is configured correctly:
   - `CLUSTER_NAME: apps`
   - `CLUSTER_ID: "2"`
   - `CLUSTER_DOMAIN: monosense.dev`
   - `CLUSTER_CIDR: 10.25.13.0/24`
   - `OBSERVABILITY_ROLE: spoke`

## Tasks / Subtasks

- [ ] Task 1: Create Talos machine configurations for apps cluster (AC: #1)
  - [ ] Subtask 1.1: Create `clusters/apps/talos/talconfig.yaml` with apps cluster settings
    - Cluster name: `apps`
    - API endpoint: `https://10.25.13.10:6443`
    - Node range: 10.25.13.11-16 (3 control plane, 3 worker)
    - Talos v1.12.0, Kubernetes v1.35.0
  - [ ] Subtask 1.2: Create node-specific patches in `patches/` directory
    - Control plane patches
    - Worker node patches
    - Network patches (MTU 9000, LACP bonding)
  - [ ] Subtask 1.3: Run `talhelper genconfig` to generate machine configs
  - [ ] Subtask 1.4: Encrypt secrets with SOPS in `talsecret.sops.yaml`
  - [ ] Subtask 1.5: Store generated configs in `clusterconfig/` directory

- [ ] Task 2: Create helmfile bootstrap configuration (AC: #2)
  - [ ] Subtask 2.1: Create `bootstrap/apps/helmfile.d/00-crds.yaml` for CRDs
    - Cilium CRDs
    - cert-manager CRDs
    - Gateway API CRDs
  - [ ] Subtask 2.2: Create `bootstrap/apps/helmfile.d/01-apps.yaml` with dependency chain
    - Cilium (cluster.id=2, cluster.name=apps, eBPF native routing)
    - CoreDNS
    - Spegel
    - cert-manager
    - Flux
  - [ ] Subtask 2.3: Create `bootstrap/apps/templates/values.yaml.gotmpl`
  - [ ] Subtask 2.4: Create `bootstrap/apps/secrets.yaml.tpl` referencing 1Password
  - [ ] Subtask 2.5: Create `bootstrap/apps/github-deploy-key.sops.yaml`

- [ ] Task 3: Configure Flux for release branch (AC: #4)
  - [ ] Subtask 3.1: Create `clusters/apps/flux/kustomization.yaml` referencing release branch
  - [ ] Subtask 3.2: Configure GitRepository to track `release` branch
  - [ ] Subtask 3.3: Ensure staged rollout pattern is properly configured

- [ ] Task 4: Create apps cluster cluster-vars ConfigMap (AC: #8)
  - [ ] Subtask 4.1: Create `clusters/apps/flux/cluster-vars.yaml` with apps cluster variables
  - [ ] Subtask 4.2: Configure observability role as `spoke`
  - [ ] Subtask 4.3: Verify all required cluster variables are present

- [ ] Task 5: Configure Flux config directory (AC: #6)
  - [ ] Subtask 5.1: Create `clusters/apps/flux/config/cluster-infrastructure.yaml`
  - [ ] Subtask 5.2: Create `clusters/apps/flux/config/cluster-apps.yaml`
  - [ ] Subtask 5.3: Create `clusters/apps/flux/config/cluster-local.yaml`
  - [ ] Subtask 5.4: Create `clusters/apps/flux/repositories/kustomization.yaml`

- [ ] Task 6: Update bootstrap taskfile (AC: #3)
  - [ ] Subtask 6.1: Ensure `.taskfiles/bootstrap/Taskfile.yaml` contains `bootstrap:apps` task
  - [ ] Subtask 6.2: Verify bootstrap sequence matches infra pattern
  - [ ] Subtask 6.3: Add verification steps after each bootstrap phase

- [ ] Task 7: Bootstrap and verify apps cluster (AC: #3, #5, #7)
  - [ ] Subtask 7.1: Execute `task bootstrap:apps`
  - [ ] Subtask 7.2: Run `flux check --context apps` and verify all checks pass
  - [ ] Subtask 7.3: Run `cilium --context apps connectivity test`
  - [ ] Subtask 7.4: Verify BGP session with `cilium bgp peers`
  - [ ] Subtask 7.5: Verify bootstrap completes within 30 minutes

## Dev Notes

### Architecture Context

**Purpose of This Story:**
Bootstrap the apps cluster as the second Kubernetes cluster in the k8s-ops multi-cluster architecture. This cluster will run business-critical production workloads (Odoo, n8n, ArsipQ) with a 24-hour staged rollout delay after infra cluster validates changes.

**Cluster Architecture:**
| Attribute | Infra Cluster | Apps Cluster |
|-----------|---------------|--------------|
| Purpose | Platform services, observability hub | Business applications |
| Network | 10.25.11.0/24 | 10.25.13.0/24 |
| API Endpoint | https://10.25.11.10:6443 | https://10.25.13.10:6443 |
| Cilium cluster.id | 1 | 2 |
| Domain | monosense.dev | monosense.dev |
| Branch | main | release |
| Observability | Hub (full stack) | Spoke (remote-write to infra) |

**Technology Stack:**
| Component | Version | Notes |
|-----------|---------|-------|
| Talos Linux | v1.12.0 | Includes K8s 1.35.0, reproducible images |
| Cilium | v1.18.5 | eBPF, BGP Control Plane, cluster.id=2 |
| Flux CD | v2.7.5 | OTel tracing, image automation GA |
| External Secrets | v1.0.0 | 1Password Connect integration |
| cert-manager | v1.19.2 | DNS-01 with Cloudflare |

### Previous Story Context (Story 4.5)

**Runbooks Created:**
- `docs/runbooks/bootstrap.md` - Reference for bootstrap procedure
- `docs/runbooks/cluster-upgrade.md` - Reference for Talos operations
- `docs/runbooks/cilium.md` - Reference for network verification

**Taskfiles Available:**
| Category | Key Tasks |
|----------|-----------|
| `bootstrap:*` | `bootstrap:infra` (reference pattern) |
| `talos:*` | `apply-node`, `upgrade-node`, `reset-cluster` |
| `flux:*` | `reconcile`, `suspend`, `resume` |

### Infra Cluster Bootstrap Pattern (Reference)

**Directory Structure to Replicate:**
```
clusters/infra/
├── flux/
│   ├── kustomization.yaml          # Root Flux entry point
│   ├── cluster-vars.yaml           # Cluster variables
│   ├── config/
│   │   ├── cluster-infrastructure.yaml
│   │   ├── cluster-apps.yaml
│   │   └── cluster-local.yaml
│   └── repositories/
│       └── kustomization.yaml
├── talos/
│   ├── talconfig.yaml
│   ├── clusterconfig/
│   ├── patches/
│   └── talsecret.sops.yaml
└── apps/                            # Cluster-specific apps (observability hub)
```

**Bootstrap Sequence (CRD-First Pattern):**
```
Phase 1: Pre-Flux (Helmfile)
┌──────────┐   ┌──────┐   ┌─────────┐   ┌────────┐   ┌────────────┐   ┌──────┐
│ CRDs     │ → │Cilium│ → │ CoreDNS │ → │ Spegel │ → │cert-manager│ → │ Flux │
│(separate)│   │      │   │         │   │        │   │            │   │      │
└──────────┘   └──────┘   └─────────┘   └────────┘   └────────────┘   └──────┘

Phase 2: Post-Flux (GitOps Reconciliation)
external-secrets → Rook-Ceph → Applications
```

### Staged Rollout Configuration

**Branch-Based Staging (Critical):**
```
main branch     → infra cluster (immediate reconciliation)
release branch  → apps cluster (reconciles from release branch)

GitHub Action (release-promote.yaml):
1. On merge to main, wait 24 hours
2. Fast-forward release branch to main
3. Apps cluster automatically reconciles
4. Manual override via workflow_dispatch
```

**Flux GitRepository Configuration for Apps Cluster:**
```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: k8s-ops
  namespace: flux-system
spec:
  interval: 1m
  ref:
    branch: release  # CRITICAL: Apps cluster uses release branch
  url: ssh://git@github.com/monosense/k8s-ops.git
  secretRef:
    name: github-deploy-key
```

### Cilium Configuration Differences

**Apps Cluster Cilium Values (cluster.id=2):**
```yaml
cluster:
  name: apps
  id: 2
bpf:
  masquerade: true
  tproxy: true
bgp:
  enabled: true
  announce:
    loadbalancerIP: true
    podCIDR: false
hubble:
  enabled: true
  relay:
    enabled: true
  ui:
    enabled: false  # UI only on infra cluster
k8sServiceHost: 10.25.13.10
k8sServicePort: 6443
```

### Network Configuration

**Apps Cluster Network:**
| Setting | Value |
|---------|-------|
| Node Network | 10.25.13.0/24 |
| Control Plane VIP | 10.25.13.10 |
| Control Plane Nodes | 10.25.13.11-13 |
| Worker Nodes | 10.25.13.14-16 |
| Pod CIDR | 10.44.0.0/16 |
| Service CIDR | 10.45.0.0/16 |
| BGP Peer | Juniper SRX 320 |

**Talos Network Configuration:**
```yaml
machine:
  network:
    interfaces:
      - interface: bond0
        bond:
          mode: 802.3ad
          lacpRate: fast
          miimon: 100
        mtu: 9000
        addresses:
          - 10.25.13.X/24
        routes:
          - network: 0.0.0.0/0
            gateway: 10.25.13.1
```

### cluster-vars.yaml Template

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

### Observability Configuration (Spoke Pattern)

**Apps cluster is a spoke - it does NOT run:**
- VictoriaMetrics (hub is on infra)
- VictoriaLogs (hub is on infra)
- Grafana (hub is on infra)

**Apps cluster DOES run:**
- VMAgent with remote-write to infra cluster
- Fluent-bit with remote-write to infra VictoriaLogs
- Gatus for local health checks

**VMAgent Remote-Write Target:**
```yaml
remoteWrite:
  - url: http://vmsingle.observability.svc.infra.local:8429/api/v1/write
```

### SOPS Encryption

**AGE Public Key:**
```
age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek
```

**.sops.yaml Rules (should already exist):**
```yaml
creation_rules:
  - path_regex: clusters/apps/talos/.*\.sops\.yaml$
    age: age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek
  - path_regex: bootstrap/apps/.*\.sops\.yaml$
    age: age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek
```

### Project Structure Notes

**Directories to Create:**
- `clusters/apps/talos/` - Talos machine configurations
- `clusters/apps/flux/` - Flux configuration
- `clusters/apps/flux/config/` - Flux Kustomization configs
- `clusters/apps/flux/repositories/` - Repository references
- `clusters/apps/apps/` - Apps cluster-specific applications
- `bootstrap/apps/` - Helmfile bootstrap
- `bootstrap/apps/helmfile.d/` - Helmfile charts
- `bootstrap/apps/templates/` - Helmfile templates

**Alignment with Unified Project Structure:**
This story creates the apps cluster directory structure that mirrors the infra cluster pattern, ensuring consistency across both clusters.

### Critical Technical Details

**Talos Node Configuration:**
| Node Type | IP Range | Count | Storage |
|-----------|----------|-------|---------|
| Control Plane | 10.25.13.11-13 | 3 | NVMe |
| Worker | 10.25.13.14-16 | 3 | NVMe + Ceph |

**Bootstrap Task Dependencies:**
1. Talos nodes must be powered on and accessible
2. 1Password Connect credentials available
3. GitHub deploy key created and encrypted
4. SOPS AGE key configured locally

### Verification Commands

```bash
# Verify Talos configuration
talhelper genconfig --dry-run -c clusters/apps/talos/talconfig.yaml

# Verify bootstrap task exists
task --list | grep bootstrap:apps

# Post-bootstrap verification
flux --context apps check
flux --context apps get sources git -n flux-system
cilium --context apps connectivity test
cilium --context apps bgp peers

# Verify cluster-vars
kubectl --context apps get configmap cluster-vars -n flux-system -o yaml

# Verify release branch configuration
kubectl --context apps get gitrepository k8s-ops -n flux-system -o jsonpath='{.spec.ref.branch}'
# Expected: release
```

### Anti-Patterns to Avoid

1. **DO NOT** configure apps cluster to use `main` branch - it MUST use `release`
2. **DO NOT** set cluster.id=1 for Cilium - apps cluster MUST use cluster.id=2
3. **DO NOT** configure observability hub components - apps is a spoke
4. **DO NOT** skip CRD installation in bootstrap (CRD-first pattern required)
5. **DO NOT** hardcode cluster-specific values - use `${VARIABLE_NAME}` substitution
6. **DO NOT** copy infra cluster Talos secrets - generate new secrets for apps

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Starter Template Evaluation] - Repository structure
- [Source: _bmad-output/planning-artifacts/architecture.md#Bootstrap Sequence] - CRD-first pattern
- [Source: _bmad-output/planning-artifacts/architecture.md#Staged Rollout Pattern] - Branch-based staging
- [Source: _bmad-output/planning-artifacts/architecture.md#Cluster Identity Configuration] - Cilium cluster.id
- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.1] - Original acceptance criteria
- [Source: docs/project-context.md#Technology Stack & Versions] - Component versions
- [Source: docs/project-context.md#Kubernetes/GitOps Patterns] - GitOps patterns

### External Documentation

- [Talos Linux Installation](https://www.talos.dev/latest/introduction/getting-started/)
- [talhelper Documentation](https://budimanjojo.github.io/talhelper/latest/)
- [Cilium Installation](https://docs.cilium.io/en/v1.18/gettingstarted/k8s-install-helm/)
- [Flux Bootstrap](https://fluxcd.io/flux/installation/bootstrap/)
- [Helmfile](https://helmfile.readthedocs.io/en/latest/)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
