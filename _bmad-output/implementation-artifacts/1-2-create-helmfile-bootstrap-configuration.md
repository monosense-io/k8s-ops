# Story 1.2: Create Helmfile Bootstrap Configuration

Status: ready-for-dev

## Story

As a **platform operator**,
I want **a helmfile-based bootstrap sequence for pre-Flux components**,
So that **I can install critical infrastructure before Flux takes over**.

## Acceptance Criteria

1. **Given** Talos machine configurations from Story 1.1
   **When** helmfile bootstrap is configured
   **Then** `bootstrap/infra/helmfile.d/` contains:
   - `00-crds.yaml` installing CRDs separately (Cilium, cert-manager, Gateway API)
   - `01-apps.yaml` with dependency chain: Cilium → CoreDNS → Spegel → cert-manager → Flux

2. **And** `bootstrap/infra/templates/values.yaml.gotmpl` extracts values from HelmRelease pattern

3. **And** `bootstrap/infra/secrets.yaml.tpl` references 1Password secrets

4. **And** Cilium configured with cluster.id=1, cluster.name=infra, eBPF native routing

5. **And** `.taskfiles/bootstrap/Taskfile.yaml` contains `bootstrap:infra` task

## Tasks / Subtasks

- [ ] Task 1: Create bootstrap directory structure (AC: #1)
  - [ ] Create `bootstrap/infra/` directory
  - [ ] Create `bootstrap/infra/helmfile.d/` directory for helmfile configurations
  - [ ] Create `bootstrap/infra/templates/` directory for gotmpl files
  - [ ] Create `bootstrap/infra/resources/` directory for additional manifests (GitRepository, etc.)
  - [ ] Create `.taskfiles/bootstrap/` directory for bootstrap tasks

- [ ] Task 2: Create CRDs-first helmfile (AC: #1)
  - [ ] Create `bootstrap/infra/helmfile.d/00-crds.yaml`
  - [ ] Add Cilium CRDs release (from Cilium Helm chart with CRD-only values)
  - [ ] Add cert-manager CRDs release (separate chart: `cert-manager-crds`)
  - [ ] Add Gateway API CRDs release (from OCI artifact or chart)
  - [ ] Configure releases to skip hooks and wait for CRD availability
  - [ ] Set `disableValidation: true` for CRD releases

- [ ] Task 3: Create bootstrap apps helmfile (AC: #1, #4)
  - [ ] Create `bootstrap/infra/helmfile.d/01-apps.yaml`
  - [ ] Add Cilium release with dependencies on 00-crds
    - Set cluster.id=1, cluster.name=infra
    - Enable eBPF native routing
    - Enable kubeProxyReplacement=true
    - Configure IPAM in kubernetes mode
    - Enable hubble for observability
    - Set MTU 9000
  - [ ] Add CoreDNS release (Talos default is disabled when CNI=none)
  - [ ] Add Spegel release (P2P registry mirror)
  - [ ] Add cert-manager release (depends on CRDs)
  - [ ] Add Flux release (final bootstrap component)
  - [ ] Configure proper `needs:` dependencies between releases

- [ ] Task 4: Create values templates (AC: #2)
  - [ ] Create `bootstrap/infra/templates/values.yaml.gotmpl` base template
  - [ ] Create `bootstrap/infra/templates/cilium-values.yaml.gotmpl`
    - Extract values that match Flux HelmRelease pattern
    - Configure cluster identity, eBPF, and networking
  - [ ] Create `bootstrap/infra/templates/coredns-values.yaml.gotmpl`
  - [ ] Create `bootstrap/infra/templates/cert-manager-values.yaml.gotmpl`
  - [ ] Create `bootstrap/infra/templates/spegel-values.yaml.gotmpl`
  - [ ] Create `bootstrap/infra/templates/flux-values.yaml.gotmpl`
  - [ ] Ensure values match what will be in GitOps HelmReleases for consistency

- [ ] Task 5: Configure secrets integration (AC: #3)
  - [ ] Create `bootstrap/infra/secrets.yaml.tpl` template
  - [ ] Configure 1Password references for:
    - GitHub deploy key (for Flux git access)
    - Cloudflare API token (for cert-manager DNS-01)
  - [ ] Document `op` CLI usage for secret injection
  - [ ] Add instructions for SOPS-encrypted fallback

- [ ] Task 6: Create Flux bootstrap resources (AC: #1)
  - [ ] Create `bootstrap/infra/resources/gitrepository.yaml`
    - Configure GitRepository pointing to k8s-ops repo
    - Set branch: main
    - Configure deploy key secret reference
  - [ ] Create `bootstrap/infra/resources/flux-system-kustomization.yaml`
    - Bootstrap Kustomization for flux-system
    - Path: ./clusters/infra/flux

- [ ] Task 7: Create bootstrap Taskfile (AC: #5)
  - [ ] Create `.taskfiles/bootstrap/Taskfile.yaml`
  - [ ] Add `bootstrap:infra` task with steps:
    1. Validate kubeconfig exists
    2. Inject secrets from 1Password
    3. Run `helmfile sync` for 00-crds.yaml
    4. Wait for CRDs to be established
    5. Run `helmfile sync` for 01-apps.yaml
    6. Verify Cilium is healthy
    7. Apply Flux resources
    8. Wait for Flux to reconcile
  - [ ] Add `bootstrap:infra:crds` task (CRDs only)
  - [ ] Add `bootstrap:infra:apps` task (apps only)
  - [ ] Add `bootstrap:infra:verify` task (health checks)
  - [ ] Configure CLUSTER variable for multi-cluster support

- [ ] Task 8: Create helmfile.yaml root file
  - [ ] Create `bootstrap/infra/helmfile.yaml` that includes helmfile.d/*.yaml
  - [ ] Configure common settings (kubeContext, repositories)
  - [ ] Add repository definitions:
    - cilium: https://helm.cilium.io/
    - jetstack: https://charts.jetstack.io/
    - fluxcd: oci://ghcr.io/fluxcd-community/charts
    - spegel: oci://ghcr.io/spegel-org/helm-charts
  - [ ] Configure helmDefaults for consistent behavior

- [ ] Task 9: Document bootstrap procedure
  - [ ] Add comments in helmfiles explaining the bootstrap order
  - [ ] Document prerequisites (kubeconfig, 1Password access, SOPS key)
  - [ ] Add troubleshooting section for common issues
  - [ ] Reference runbook location: `docs/runbooks/bootstrap.md`

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document (architecture.md):**

1. **Bootstrap Sequence (Critical Path):**
   ```
   Phase 1: Pre-Flux (Helmfile) - CRD-FIRST PATTERN
   ┌──────────┐   ┌──────┐   ┌─────────┐   ┌────────┐   ┌────────────┐   ┌──────┐
   │ CRDs     │ → │Cilium│ → │ CoreDNS │ → │ Spegel │ → │cert-manager│ → │ Flux │
   │(separate)│   │      │   │         │   │        │   │            │   │      │
   └──────────┘   └──────┘   └─────────┘   └────────┘   └────────────┘   └──────┘

   Phase 2: Post-Flux (GitOps Reconciliation)
   external-secrets → Rook-Ceph → VictoriaMetrics → Applications
   ```

2. **Cilium Cluster Identity (Critical):**
   - infra cluster: cluster.id=1, cluster.name=infra
   - apps cluster: cluster.id=2, cluster.name=apps
   - Enables future Cluster Mesh capability

3. **Key Decision: CRD-First Pattern**
   - CRDs MUST be installed before applications that use them
   - Separate helmfile for CRDs prevents race conditions
   - `disableValidation: true` required during CRD installation

4. **Technology Stack Versions (December 2025):**
   | Component | Version | Notes |
   |-----------|---------|-------|
   | Cilium | v1.18.5 | eBPF native routing, BGP Control Plane |
   | cert-manager | v1.19.2 | Security fixes |
   | Flux CD | v2.7.5 | Image automation GA |
   | Spegel | v0.4.0 | P2P registry mirror |

### Helmfile Structure Reference

**bootstrap/infra/helmfile.yaml:**
```yaml
---
helmDefaults:
  atomic: true
  cleanupOnFail: true
  createNamespace: true
  wait: true
  timeout: 600

repositories:
  - name: cilium
    url: https://helm.cilium.io/
  - name: jetstack
    url: https://charts.jetstack.io/
  - name: fluxcd
    url: oci://ghcr.io/fluxcd-community/charts
  - name: spegel
    url: oci://ghcr.io/spegel-org/helm-charts

helmfiles:
  - path: helmfile.d/*.yaml
```

**bootstrap/infra/helmfile.d/00-crds.yaml:**
```yaml
---
releases:
  - name: cilium-crds
    namespace: kube-system
    chart: cilium/cilium
    version: 1.18.5
    values:
      - operator:
          enabled: false
        agent:
          enabled: false
    set:
      - name: crd.install
        value: true

  - name: cert-manager-crds
    namespace: cert-manager
    chart: jetstack/cert-manager
    version: v1.19.2
    set:
      - name: installCRDs
        value: true
      - name: crds.enabled
        value: true
      - name: crds.keep
        value: true
    hooks:
      - events: ["presync"]
        command: "sh"
        args: ["-c", "kubectl create namespace cert-manager --dry-run=client -o yaml | kubectl apply -f -"]

  - name: gateway-api-crds
    namespace: gateway-system
    chart: oci://ghcr.io/envoyproxy/gateway-helm
    version: v1.6.1
    set:
      - name: deployment.envoyGateway.enabled
        value: false
```

**bootstrap/infra/helmfile.d/01-apps.yaml:**
```yaml
---
releases:
  - name: cilium
    namespace: kube-system
    chart: cilium/cilium
    version: 1.18.5
    needs:
      - kube-system/cilium-crds
    values:
      - ../templates/cilium-values.yaml.gotmpl

  - name: coredns
    namespace: kube-system
    chart: coredns/coredns
    version: 1.36.1
    needs:
      - kube-system/cilium

  - name: spegel
    namespace: kube-system
    chart: spegel/spegel
    version: v0.4.0
    needs:
      - kube-system/coredns

  - name: cert-manager
    namespace: cert-manager
    chart: jetstack/cert-manager
    version: v1.19.2
    needs:
      - cert-manager/cert-manager-crds
      - kube-system/cilium
    values:
      - ../templates/cert-manager-values.yaml.gotmpl

  - name: flux
    namespace: flux-system
    chart: fluxcd/flux2
    version: 2.7.5
    needs:
      - cert-manager/cert-manager
    values:
      - ../templates/flux-values.yaml.gotmpl
```

### Cilium Configuration (Critical)

**templates/cilium-values.yaml.gotmpl:**
```yaml
---
# Cluster identity for future Cluster Mesh
cluster:
  id: 1
  name: infra

# eBPF native routing (no overlay)
routingMode: native
ipv4NativeRoutingCIDR: "10.25.11.0/24"
autoDirectNodeRoutes: true

# Replace kube-proxy
kubeProxyReplacement: true
k8sServiceHost: "10.25.11.10"
k8sServicePort: "6443"

# IPAM configuration
ipam:
  mode: kubernetes

# MTU settings
mtu: 9000

# Hubble for observability
hubble:
  enabled: true
  relay:
    enabled: true
  ui:
    enabled: true

# BGP Control Plane for LoadBalancer IPs
bgpControlPlane:
  enabled: true

# Security
securityContext:
  capabilities:
    ciliumAgent:
      - CHOWN
      - KILL
      - NET_ADMIN
      - NET_RAW
      - IPC_LOCK
      - SYS_ADMIN
      - SYS_RESOURCE
      - DAC_OVERRIDE
      - FOWNER
      - SETGID
      - SETUID
    cleanCiliumState:
      - NET_ADMIN
      - SYS_ADMIN
      - SYS_RESOURCE

# Operator configuration
operator:
  replicas: 1
  resources:
    limits:
      cpu: 500m
      memory: 256Mi
    requests:
      cpu: 100m
      memory: 128Mi
```

### Secrets Integration Pattern

**bootstrap/infra/secrets.yaml.tpl:**
```yaml
# Secrets template - populated from 1Password via `op` CLI
# Usage: op inject -i secrets.yaml.tpl -o secrets.yaml
---
github_deploy_key: |
  {{ op://k8s-ops/github-deploy-key/private_key }}

cloudflare_api_token: {{ op://k8s-ops/cloudflare/api_token }}
```

**Injection command:**
```bash
op inject -i bootstrap/infra/secrets.yaml.tpl -o bootstrap/infra/secrets.yaml
```

### Taskfile Structure

**.taskfiles/bootstrap/Taskfile.yaml:**
```yaml
---
version: "3"

vars:
  CLUSTER: '{{ .CLUSTER | default "infra" }}'
  KUBECONFIG: '{{ .KUBECONFIG | default "~/.kube/config" }}'

tasks:
  infra:
    desc: Bootstrap the infra cluster with pre-Flux components
    cmds:
      - task: infra:validate
      - task: infra:secrets
      - task: infra:crds
      - task: infra:apps
      - task: infra:flux
      - task: infra:verify

  infra:validate:
    desc: Validate prerequisites for bootstrap
    cmds:
      - |
        if ! kubectl cluster-info &>/dev/null; then
          echo "ERROR: Cannot connect to cluster. Check KUBECONFIG."
          exit 1
        fi
      - echo "✓ Kubernetes cluster accessible"

  infra:secrets:
    desc: Inject secrets from 1Password
    cmds:
      - |
        if ! command -v op &>/dev/null; then
          echo "ERROR: 1Password CLI (op) not installed"
          exit 1
        fi
      - op inject -i bootstrap/infra/secrets.yaml.tpl -o bootstrap/infra/secrets.yaml
      - echo "✓ Secrets injected from 1Password"

  infra:crds:
    desc: Install CRDs (Phase 1)
    dir: bootstrap/infra
    cmds:
      - helmfile -f helmfile.d/00-crds.yaml sync
      - |
        echo "Waiting for CRDs to be established..."
        kubectl wait --for condition=established --timeout=60s crd/ciliumnetworkpolicies.cilium.io
        kubectl wait --for condition=established --timeout=60s crd/certificates.cert-manager.io
        kubectl wait --for condition=established --timeout=60s crd/gateways.gateway.networking.k8s.io
      - echo "✓ CRDs installed and established"

  infra:apps:
    desc: Install bootstrap applications (Phase 2)
    dir: bootstrap/infra
    cmds:
      - helmfile -f helmfile.d/01-apps.yaml sync
      - echo "✓ Bootstrap applications installed"

  infra:flux:
    desc: Apply Flux resources and wait for reconciliation
    cmds:
      - kubectl apply -f bootstrap/infra/resources/
      - |
        echo "Waiting for Flux to reconcile..."
        kubectl -n flux-system wait --for=condition=Ready --timeout=300s kustomization/flux-system
      - echo "✓ Flux reconciled"

  infra:verify:
    desc: Verify bootstrap health
    cmds:
      - |
        echo "Verifying Cilium..."
        cilium status --wait
      - |
        echo "Verifying cert-manager..."
        kubectl -n cert-manager wait --for=condition=Available --timeout=120s deployment/cert-manager
      - |
        echo "Verifying Flux..."
        flux check
      - echo "✓ Bootstrap verification complete"
```

### Project Structure Notes

**Files to create:**
```
k8s-ops/
├── bootstrap/
│   └── infra/
│       ├── helmfile.yaml              # Root helmfile
│       ├── helmfile.d/
│       │   ├── 00-crds.yaml           # CRDs first
│       │   └── 01-apps.yaml           # Bootstrap apps
│       ├── templates/
│       │   ├── cilium-values.yaml.gotmpl
│       │   ├── coredns-values.yaml.gotmpl
│       │   ├── spegel-values.yaml.gotmpl
│       │   ├── cert-manager-values.yaml.gotmpl
│       │   └── flux-values.yaml.gotmpl
│       ├── resources/
│       │   ├── gitrepository.yaml
│       │   └── flux-system-kustomization.yaml
│       ├── secrets.yaml.tpl           # 1Password template
│       └── github-deploy-key.sops.yaml # SOPS encrypted fallback
│
└── .taskfiles/
    └── bootstrap/
        └── Taskfile.yaml              # Bootstrap tasks
```

### Alignment with Existing Patterns

**Matching Flux HelmRelease Pattern:**
The values in helmfile templates should match the values in GitOps HelmReleases so that when Flux takes over, no drift occurs.

From `kubernetes/apps/` HelmRelease patterns:
- Cilium values should match `infrastructure/base/cilium/`
- cert-manager values should match `infrastructure/base/cert-manager/`
- This ensures helmfile bootstrap → Flux GitOps is seamless

### Previous Story Intelligence

**From Story 1.1 (Talos Machine Configurations):**
- Talos configured with CNI: none (Cilium via helmfile)
- kube-proxy disabled (Cilium eBPF replacement)
- Cluster endpoint: 10.25.11.10:6443
- Node network: 10.25.11.0/24 with MTU 9000
- SOPS AGE key: `age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek`

**Key learnings from Story 1.1:**
- Use `.yaml` extension consistently
- All secrets must be SOPS encrypted before commit
- Validate configurations before considering complete
- Talos provides API-driven management only

**From Epic 0 Stories:**
- Repository structure at `clusters/infra/flux/` ready for Flux
- `.sops.yaml` configured at repository root
- GitHub workflows validate changes before merge

### Critical Implementation Rules

1. **CRDs before Applications:** Always install CRDs in separate helmfile (00-crds.yaml)
2. **Cilium cluster.id:** MUST be 1 for infra cluster (2 for apps cluster)
3. **Dependency Chain:** Cilium → CoreDNS → Spegel → cert-manager → Flux
4. **Values Parity:** Helmfile values must match GitOps HelmRelease values
5. **No hardcoded secrets:** Use 1Password injection or SOPS encryption
6. **Native routing:** Cilium eBPF with no overlay network

### Helmfile/Helm Commands Reference

```bash
# Validate helmfile syntax
helmfile -f bootstrap/infra/helmfile.yaml lint

# Diff before applying
helmfile -f bootstrap/infra/helmfile.yaml diff

# Sync (install/upgrade)
helmfile -f bootstrap/infra/helmfile.yaml sync

# Sync specific helmfile
helmfile -f bootstrap/infra/helmfile.d/00-crds.yaml sync

# Destroy (for cleanup/retry)
helmfile -f bootstrap/infra/helmfile.yaml destroy
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2: Create Helmfile Bootstrap Configuration]
- [Source: _bmad-output/planning-artifacts/architecture.md#Bootstrap Sequence]
- [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions]
- [Source: docs/project-context.md#Technology Stack & Versions]
- [Helmfile Documentation](https://helmfile.readthedocs.io/)
- [Cilium Helm Chart](https://docs.cilium.io/en/stable/installation/k8s-install-helm/)
- [Flux Bootstrap](https://fluxcd.io/docs/installation/)

### Technology Stack Versions

| Tool | Version | Notes |
|------|---------|-------|
| Helmfile | Latest | Configuration-as-code for Helm |
| Helm | v3.x | Package manager |
| Cilium | v1.18.5 | CNI with eBPF |
| cert-manager | v1.19.2 | TLS certificate management |
| Flux CD | v2.7.5 | GitOps controller |
| Spegel | v0.4.0 | P2P registry mirror |
| Envoy Gateway | v1.6.1 | Gateway API implementation |

### Validation Checklist

Before marking complete, verify:
- [ ] `bootstrap/infra/helmfile.yaml` exists and is valid YAML
- [ ] `bootstrap/infra/helmfile.d/00-crds.yaml` installs CRDs separately
- [ ] `bootstrap/infra/helmfile.d/01-apps.yaml` has correct dependency chain
- [ ] Cilium values include cluster.id=1, cluster.name=infra
- [ ] Cilium configured with eBPF native routing and kubeProxyReplacement=true
- [ ] cert-manager version is v1.19.2
- [ ] Flux version is v2.7.5
- [ ] `.taskfiles/bootstrap/Taskfile.yaml` contains `bootstrap:infra` task
- [ ] `helmfile lint` passes without errors
- [ ] secrets.yaml.tpl references 1Password correctly
- [ ] Values templates match Flux HelmRelease patterns

### Common Gotchas

1. **CRD timing:** CRDs must be fully established before apps that use them
2. **Helm repository credentials:** OCI repositories may need authentication
3. **Cilium kubeProxyReplacement:** Requires k8sServiceHost/Port to be set
4. **Namespace creation:** Helmfile creates namespaces, don't duplicate
5. **Secrets lifecycle:** secrets.yaml is generated, not committed (add to .gitignore)
6. **Flux bootstrap vs install:** Use Flux helm chart, not `flux bootstrap` command
7. **CoreDNS:** Talos disables default CoreDNS when CNI=none, must install via helmfile

### Git Commit Message Format

```
feat(bootstrap): create helmfile configuration for infra cluster

- Add CRD-first helmfile pattern (00-crds.yaml)
- Configure Cilium with cluster.id=1 and eBPF native routing
- Add bootstrap apps: CoreDNS, Spegel, cert-manager, Flux
- Create Taskfile for automated bootstrap process
- Add 1Password integration for secrets
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

