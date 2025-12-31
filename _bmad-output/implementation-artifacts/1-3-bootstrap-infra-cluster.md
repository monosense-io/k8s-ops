# Story 1.3: Bootstrap Infra Cluster

Status: ready-for-dev

## Story

As a **platform operator**,
I want **to bootstrap the infra cluster using documented taskfile commands**,
So that **my cluster is running with Flux GitOps managing all resources**.

## Acceptance Criteria

1. **Given** Talos nodes are provisioned and helmfile bootstrap is configured
   **When** `task bootstrap:infra` is executed
   **Then** Talos control plane is bootstrapped via `talosctl bootstrap`

2. **And** kubeconfig is generated via `talosctl kubeconfig`

3. **And** helmfile installs components in order: CRDs → Cilium → CoreDNS → Spegel → cert-manager → Flux

4. **And** Flux connects to GitHub repository using deploy key

5. **And** `flux check` passes with all components healthy

6. **And** Cilium connectivity tests pass (`cilium connectivity test`)

7. **And** bootstrap completes within 30 minutes (NFR2)

## Tasks / Subtasks

- [ ] Task 1: Verify Prerequisites (AC: #1)
  - [ ] Confirm Talos machine configurations from Story 1.1 are complete and applied
  - [ ] Confirm helmfile bootstrap configuration from Story 1.2 is complete
  - [ ] Verify Talos nodes are powered on and reachable at 10.25.11.11-16
  - [ ] Verify Talos API is accessible on cluster endpoint 10.25.11.10:50000
  - [ ] Confirm 1Password CLI (`op`) is authenticated
  - [ ] Confirm SOPS AGE key is available for decryption

- [ ] Task 2: Bootstrap Talos Control Plane (AC: #1, #2)
  - [ ] Create `task talos:bootstrap` in `.taskfiles/talos/Taskfile.yaml` if not exists
  - [ ] Execute `talosctl bootstrap --nodes 10.25.11.11 --endpoints 10.25.11.10` on first control plane node
  - [ ] Wait for etcd cluster to form and become healthy
  - [ ] Verify control plane nodes report Ready status
  - [ ] Execute `talosctl kubeconfig --nodes 10.25.11.10 -f ~/.kube/k8s-ops-infra`
  - [ ] Configure kubectl context for infra cluster
  - [ ] Push kubeconfig to 1Password via `task op:push`

- [ ] Task 3: Execute CRD Installation Phase (AC: #3)
  - [ ] Run `task bootstrap:infra:secrets` to inject secrets from 1Password
  - [ ] Run `task bootstrap:infra:crds` to install CRDs first
  - [ ] Verify CRDs are established:
    - `ciliumnetworkpolicies.cilium.io`
    - `certificates.cert-manager.io`
    - `gateways.gateway.networking.k8s.io`
  - [ ] Log any CRD installation errors

- [ ] Task 4: Execute Helmfile Bootstrap Apps (AC: #3)
  - [ ] Run `task bootstrap:infra:apps` to install bootstrap applications
  - [ ] Verify Cilium pods are Running in kube-system
  - [ ] Verify CoreDNS pods are Running in kube-system
  - [ ] Verify Spegel pods are Running in kube-system
  - [ ] Verify cert-manager pods are Running in cert-manager namespace
  - [ ] Verify Flux pods are Running in flux-system namespace
  - [ ] Capture and log any failures during deployment

- [ ] Task 5: Configure Flux GitOps Connection (AC: #4)
  - [ ] Create GitHub deploy key secret in flux-system namespace
  - [ ] Apply GitRepository resource pointing to k8s-ops repo (branch: main)
  - [ ] Apply initial Flux Kustomization for `clusters/infra/flux/`
  - [ ] Verify GitRepository resource shows Ready status
  - [ ] Verify Flux can clone and access the repository
  - [ ] Confirm deploy key permissions are correct (read-only for production)

- [ ] Task 6: Verify Flux Health (AC: #5)
  - [ ] Run `flux check` and verify all components pass
  - [ ] Verify source-controller is healthy
  - [ ] Verify kustomize-controller is healthy
  - [ ] Verify helm-controller is healthy
  - [ ] Verify notification-controller is healthy
  - [ ] Check `flux get all -A` for any failures

- [ ] Task 7: Verify Cilium Connectivity (AC: #6)
  - [ ] Run `cilium status --wait` to verify Cilium is healthy
  - [ ] Verify cluster.id=1 and cluster.name=infra are set correctly
  - [ ] Run `cilium connectivity test` (full suite)
  - [ ] Verify eBPF datapath is operational
  - [ ] Verify BGP Control Plane is enabled (for future LoadBalancer IPs)
  - [ ] Check Hubble relay is accessible

- [ ] Task 8: Validate Bootstrap Timing (AC: #7)
  - [ ] Record start time at beginning of bootstrap
  - [ ] Record end time after all verifications pass
  - [ ] Calculate total bootstrap duration
  - [ ] Verify bootstrap completed within 30 minutes (NFR2)
  - [ ] Document actual bootstrap time for future reference

- [ ] Task 9: Create Unified Bootstrap Task (AC: #1-#7)
  - [ ] Create `task bootstrap:infra` that orchestrates all steps
  - [ ] Include validation, secrets injection, CRDs, apps, Flux, and verification
  - [ ] Add progress indicators and colored output
  - [ ] Add error handling and rollback guidance
  - [ ] Test complete bootstrap from scratch

- [ ] Task 10: Document Bootstrap Results
  - [ ] Update `docs/runbooks/bootstrap.md` with actual timings
  - [ ] Document any issues encountered and resolutions
  - [ ] Create troubleshooting section for common problems
  - [ ] Add verification commands for operators to check health

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document (architecture.md):**

1. **Bootstrap Sequence (Critical Path):**
   ```
   Phase 1: Talos Bootstrap
   talosctl bootstrap → etcd cluster → kubeconfig generation

   Phase 2: Pre-Flux (Helmfile) - CRD-FIRST PATTERN
   ┌──────────┐   ┌──────┐   ┌─────────┐   ┌────────┐   ┌────────────┐   ┌──────┐
   │ CRDs     │ → │Cilium│ → │ CoreDNS │ → │ Spegel │ → │cert-manager│ → │ Flux │
   │(separate)│   │      │   │         │   │        │   │            │   │      │
   └──────────┘   └──────┘   └─────────┘   └────────┘   └────────────┘   └──────┘

   Phase 3: Post-Flux (GitOps Reconciliation)
   external-secrets → Rook-Ceph → VictoriaMetrics → Applications
   ```

2. **Cilium Cluster Identity (Critical):**
   - infra cluster: cluster.id=1, cluster.name=infra
   - apps cluster: cluster.id=2, cluster.name=apps
   - Enables future Cluster Mesh capability

3. **NFR2: Bootstrap Performance Target**
   - Full cluster bootstrap < 30 minutes (time from empty cluster to all resources Ready)

4. **Network Configuration:**
   - Cluster endpoint: 10.25.11.10:6443 (API server VIP)
   - Node network: 10.25.11.0/24
   - MTU: 9000 (jumbo frames)
   - LACP bonding configured

5. **Technology Stack Versions (December 2025):**
   | Component | Version | Notes |
   |-----------|---------|-------|
   | Talos Linux | v1.12.0 | Immutable K8s OS, API-driven |
   | Kubernetes | v1.35.0 | Included with Talos 1.12.0 |
   | Cilium | v1.18.5 | eBPF native routing, BGP Control Plane |
   | cert-manager | v1.19.2 | TLS certificate management |
   | Flux CD | v2.7.5 | GitOps controller |
   | Spegel | v0.4.0 | P2P registry mirror |

### Talos Bootstrap Commands Reference

```bash
# Bootstrap first control plane node (only run once per cluster)
talosctl bootstrap \
  --nodes 10.25.11.11 \
  --endpoints 10.25.11.10 \
  --talosconfig clusters/infra/talos/clusterconfig/talosconfig

# Wait for etcd cluster health
talosctl health \
  --nodes 10.25.11.11,10.25.11.12,10.25.11.13 \
  --wait-timeout 10m

# Generate kubeconfig
talosctl kubeconfig \
  --nodes 10.25.11.10 \
  --force \
  -f ~/.kube/k8s-ops-infra

# Set kubectl context
export KUBECONFIG=~/.kube/k8s-ops-infra
kubectl config use-context admin@infra
```

### Helmfile Bootstrap Commands Reference

```bash
# Run from repository root with proper KUBECONFIG

# Step 1: Inject secrets from 1Password
task bootstrap:infra:secrets

# Step 2: Install CRDs
task bootstrap:infra:crds
# Equivalent to: helmfile -f bootstrap/infra/helmfile.d/00-crds.yaml sync

# Step 3: Wait for CRDs
kubectl wait --for condition=established --timeout=60s \
  crd/ciliumnetworkpolicies.cilium.io \
  crd/certificates.cert-manager.io \
  crd/gateways.gateway.networking.k8s.io

# Step 4: Install bootstrap apps
task bootstrap:infra:apps
# Equivalent to: helmfile -f bootstrap/infra/helmfile.d/01-apps.yaml sync

# Step 5: Apply Flux resources
kubectl apply -f bootstrap/infra/resources/

# Step 6: Wait for Flux reconciliation
kubectl -n flux-system wait --for=condition=Ready --timeout=300s \
  kustomization/flux-system
```

### Verification Commands Reference

```bash
# Cilium health check
cilium status --wait
cilium connectivity test

# Verify Cilium cluster identity
cilium config view | grep -E "cluster-id|cluster-name"
# Expected output:
# cluster-id: 1
# cluster-name: infra

# Flux health check
flux check
flux get all -A

# Overall cluster health
kubectl get nodes -o wide
kubectl get pods -A | grep -v Running
kubectl top nodes
```

### Taskfile Structure

**.taskfiles/bootstrap/Taskfile.yaml additions:**
```yaml
tasks:
  infra:
    desc: Complete infra cluster bootstrap
    cmds:
      - task: :talos:bootstrap
        vars: { CLUSTER: infra }
      - task: infra:validate
      - task: infra:secrets
      - task: infra:crds
      - task: infra:wait-crds
      - task: infra:apps
      - task: infra:flux
      - task: infra:verify

  infra:wait-crds:
    desc: Wait for CRDs to be established
    cmds:
      - |
        echo "Waiting for CRDs to be established..."
        kubectl wait --for condition=established --timeout=120s \
          crd/ciliumnetworkpolicies.cilium.io \
          crd/ciliumclusterwidenetworkpolicies.cilium.io \
          crd/ciliumloadbalancerippools.cilium.io \
          crd/certificates.cert-manager.io \
          crd/clusterissuers.cert-manager.io \
          crd/gateways.gateway.networking.k8s.io \
          crd/httproutes.gateway.networking.k8s.io
      - echo "✓ All CRDs established"
```

**.taskfiles/talos/Taskfile.yaml additions:**
```yaml
tasks:
  bootstrap:
    desc: Bootstrap Talos control plane
    vars:
      CLUSTER: '{{ .CLUSTER | default "infra" }}'
      FIRST_CP_NODE: '{{ if eq .CLUSTER "infra" }}10.25.11.11{{ else }}10.25.13.11{{ end }}'
      ENDPOINT: '{{ if eq .CLUSTER "infra" }}10.25.11.10{{ else }}10.25.13.10{{ end }}'
    cmds:
      - |
        echo "Bootstrapping {{ .CLUSTER }} cluster control plane..."
        talosctl bootstrap \
          --nodes {{ .FIRST_CP_NODE }} \
          --endpoints {{ .ENDPOINT }} \
          --talosconfig clusters/{{ .CLUSTER }}/talos/clusterconfig/talosconfig
      - task: health
        vars: { CLUSTER: "{{ .CLUSTER }}" }
      - task: kubeconfig
        vars: { CLUSTER: "{{ .CLUSTER }}" }
      - echo "✓ Talos {{ .CLUSTER }} cluster bootstrapped"

  health:
    desc: Check Talos cluster health
    vars:
      CLUSTER: '{{ .CLUSTER | default "infra" }}'
    cmds:
      - |
        talosctl health \
          --talosconfig clusters/{{ .CLUSTER }}/talos/clusterconfig/talosconfig \
          --wait-timeout 10m

  kubeconfig:
    desc: Generate kubeconfig
    vars:
      CLUSTER: '{{ .CLUSTER | default "infra" }}'
      ENDPOINT: '{{ if eq .CLUSTER "infra" }}10.25.11.10{{ else }}10.25.13.10{{ end }}'
    cmds:
      - |
        talosctl kubeconfig \
          --nodes {{ .ENDPOINT }} \
          --force \
          --talosconfig clusters/{{ .CLUSTER }}/talos/clusterconfig/talosconfig \
          -f ~/.kube/k8s-ops-{{ .CLUSTER }}
      - echo "✓ Kubeconfig saved to ~/.kube/k8s-ops-{{ .CLUSTER }}"
```

### Project Structure Notes

**Files required before this story:**
```
k8s-ops/
├── clusters/
│   └── infra/
│       ├── talos/                    # From Story 1.1
│       │   ├── talconfig.yaml
│       │   ├── talsecret.sops.yaml
│       │   └── clusterconfig/
│       │       ├── talosconfig
│       │       └── *.yaml (machine configs)
│       └── flux/                     # From Story 0.3
│           ├── kustomization.yaml
│           ├── cluster-vars.yaml
│           └── config/
├── bootstrap/
│   └── infra/                        # From Story 1.2
│       ├── helmfile.yaml
│       ├── helmfile.d/
│       │   ├── 00-crds.yaml
│       │   └── 01-apps.yaml
│       ├── templates/
│       │   └── *.yaml.gotmpl
│       ├── resources/
│       │   ├── gitrepository.yaml
│       │   └── flux-system-kustomization.yaml
│       └── secrets.yaml.tpl
└── .taskfiles/
    ├── bootstrap/Taskfile.yaml       # From Story 1.2
    └── talos/Taskfile.yaml           # Extend for bootstrap
```

**Files to create/modify in this story:**
- Extend `.taskfiles/talos/Taskfile.yaml` with bootstrap task
- Extend `.taskfiles/bootstrap/Taskfile.yaml` with wait-crds task
- Create/update `docs/runbooks/bootstrap.md` with actual procedure

### Previous Story Intelligence

**From Story 1.1 (Talos Machine Configurations):**
- Talos configured with CNI: none (requires Cilium via helmfile)
- kube-proxy disabled (Cilium eBPF replacement)
- Cluster endpoint: 10.25.11.10:6443
- Node network: 10.25.11.0/24 with MTU 9000
- Control plane nodes: 10.25.11.11, 10.25.11.12, 10.25.11.13
- Worker nodes: 10.25.11.14, 10.25.11.15, 10.25.11.16
- SOPS AGE key: `age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek`

**From Story 1.2 (Helmfile Bootstrap Configuration):**
- CRD-first pattern: 00-crds.yaml runs before 01-apps.yaml
- Dependency chain: Cilium → CoreDNS → Spegel → cert-manager → Flux
- Cilium cluster.id=1, cluster.name=infra
- Values templates match GitOps HelmRelease patterns
- 1Password secrets integration via `op inject`

**Key learnings:**
- Always install CRDs before applications that use them
- Use `.yaml` extension consistently (not `.yml`)
- All secrets must be SOPS encrypted before commit
- Helmfile values must match Flux HelmRelease values for seamless handoff
- Talos provides API-driven management only (no SSH)

### Critical Implementation Rules

1. **Bootstrap Order is Critical:**
   - Talos bootstrap FIRST (creates etcd, API server)
   - CRDs SECOND (Cilium, cert-manager, Gateway API)
   - CNI (Cilium) THIRD (pods can't schedule without CNI)
   - CoreDNS FOURTH (DNS resolution)
   - Remaining apps in dependency order

2. **Cilium Configuration Verification:**
   - cluster.id MUST be 1 for infra cluster
   - kubeProxyReplacement MUST be true (Talos disables kube-proxy)
   - k8sServiceHost MUST point to 10.25.11.10
   - Native routing mode with 10.25.11.0/24 CIDR

3. **Flux GitOps Connection:**
   - Deploy key must have repository read access
   - GitRepository must point to main branch for infra
   - Initial Kustomization path: ./clusters/infra/flux

4. **Error Recovery:**
   - If Talos bootstrap fails, `talosctl reset` and retry
   - If helmfile fails, check CRD establishment first
   - If Flux fails, verify deploy key permissions

5. **Timing Verification:**
   - Record actual bootstrap time
   - Target: < 30 minutes from empty cluster to Flux reconciling
   - Document bottlenecks if target exceeded

### Environment Variables Required

```bash
# Talos configuration
export TALOSCONFIG=clusters/infra/talos/clusterconfig/talosconfig

# Kubernetes configuration (after kubeconfig generation)
export KUBECONFIG=~/.kube/k8s-ops-infra

# 1Password (must be signed in)
eval $(op signin)

# SOPS AGE key (for decrypting secrets)
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
```

### Troubleshooting Guide

**Issue: Talos bootstrap fails with "etcd unavailable"**
- Cause: Network connectivity issues between control plane nodes
- Fix: Verify MTU settings match (9000), check LACP bonding status
- Command: `talosctl -n 10.25.11.11 logs etcd`

**Issue: Cilium pods stuck in ContainerCreating**
- Cause: Missing CRDs or image pull issues
- Fix: Verify CRDs installed, check Spegel is running for image caching
- Command: `kubectl describe pod -n kube-system -l app.kubernetes.io/name=cilium`

**Issue: CoreDNS not resolving**
- Cause: Cilium CNI not ready
- Fix: Wait for Cilium to be healthy first
- Command: `cilium status --wait`

**Issue: Flux can't clone repository**
- Cause: Deploy key not added to GitHub or wrong permissions
- Fix: Verify deploy key in GitHub repo settings, check secret content
- Command: `kubectl logs -n flux-system deploy/source-controller`

**Issue: Bootstrap exceeds 30 minutes**
- Cause: Slow image pulls, network latency, or resource constraints
- Fix: Ensure Spegel is running for P2P image caching
- Check: `kubectl get events --sort-by='.lastTimestamp' -A`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3: Bootstrap Infra Cluster]
- [Source: _bmad-output/planning-artifacts/architecture.md#Bootstrap Sequence]
- [Source: _bmad-output/planning-artifacts/architecture.md#Core Architectural Decisions]
- [Source: docs/project-context.md#Technology Stack & Versions]
- [Talos Linux Documentation](https://www.talos.dev/latest/)
- [Cilium Getting Started](https://docs.cilium.io/en/stable/gettingstarted/)
- [Flux Bootstrap Guide](https://fluxcd.io/docs/installation/)

### Validation Checklist

Before marking complete, verify:
- [ ] `talosctl bootstrap` completed successfully
- [ ] Kubeconfig generated and pushed to 1Password
- [ ] All CRDs are established and Ready
- [ ] Cilium pods running with correct cluster.id=1
- [ ] CoreDNS pods running and resolving cluster DNS
- [ ] Spegel pods running for P2P image caching
- [ ] cert-manager pods running
- [ ] Flux pods running and healthy
- [ ] `flux check` passes all checks
- [ ] `cilium connectivity test` passes
- [ ] GitRepository shows Ready status
- [ ] Bootstrap completed in < 30 minutes
- [ ] All nodes show Ready status
- [ ] `kubectl get pods -A | grep -v Running` returns no failing pods

### Git Commit Message Format

```
feat(bootstrap): bootstrap infra cluster with Flux GitOps

- Bootstrap Talos control plane via talosctl
- Install CRDs, Cilium, CoreDNS, Spegel, cert-manager, Flux via helmfile
- Configure Flux GitOps connection to k8s-ops repository
- Verify Cilium connectivity and cluster health
- Bootstrap completed in XX minutes (target: <30min)
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

