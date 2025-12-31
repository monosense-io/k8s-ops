# Story 1.1: Create Talos Machine Configurations

Status: ready-for-dev

## Story

As a **platform operator**,
I want **Talos machine configurations generated from templates using talhelper**,
So that **I can provision consistent, reproducible cluster nodes**.

## Acceptance Criteria

1. **Given** the repository structure from Epic 0
   **When** Talos configurations are created for infra cluster
   **Then** `clusters/infra/talos/` contains:
   - `talconfig.yaml` with cluster settings (name: infra, endpoint: 10.25.11.10, nodes: 10.25.11.11-16)
   - `clusterconfig/` directory with generated machine configs (encrypted with SOPS)
   - `patches/` directory for node-specific customizations

2. **And** talconfig.yaml specifies Talos v1.12.0, Kubernetes v1.35.0

3. **And** network configuration includes MTU 9000, LACP bonding

4. **And** `talhelper genconfig` produces valid machine configurations

5. **And** secrets are encrypted in `talsecret.sops.yaml`

## Tasks / Subtasks

- [ ] Task 1: Create Talos directory structure (AC: #1)
  - [ ] Create `clusters/infra/talos/` directory
  - [ ] Create `clusters/infra/talos/clusterconfig/` directory for generated configs
  - [ ] Create `clusters/infra/talos/patches/` directory for customizations
  - [ ] Create `clusters/infra/talos/.gitignore` to exclude sensitive unencrypted files

- [ ] Task 2: Create talconfig.yaml base configuration (AC: #1, #2)
  - [ ] Define cluster name: `infra`
  - [ ] Set clusterPodNets: `10.42.0.0/16`
  - [ ] Set clusterSvcNets: `10.43.0.0/16`
  - [ ] Configure endpoint: `https://10.25.11.10:6443`
  - [ ] Set talosVersion: `v1.12.0`
  - [ ] Set kubernetesVersion: `v1.35.0`
  - [ ] Configure allowSchedulingOnControlPlane: true (home lab)
  - [ ] Enable CNI: none (Cilium managed)
  - [ ] Enable cluster discovery
  - [ ] Configure 6 nodes (10.25.11.11-16)

- [ ] Task 3: Configure node definitions (AC: #1, #3)
  - [ ] Define 3 control plane nodes (10.25.11.11-13)
  - [ ] Define 3 worker nodes (10.25.11.14-16)
  - [ ] Configure hostnames following pattern: `infra-cp-{n}`, `infra-wk-{n}`
  - [ ] Set installDisk for each node (identify NVMe device paths)
  - [ ] Configure network interfaces with LACP bonding
  - [ ] Set MTU 9000 for all interfaces
  - [ ] Enable DHCP or static IP assignment per node

- [ ] Task 4: Create node-specific patches (AC: #1, #3)
  - [ ] Create `patches/controlplane.yaml` for control plane specific configs
  - [ ] Create `patches/worker.yaml` for worker specific configs
  - [ ] Create `patches/common.yaml` for shared configurations:
    - Kernel modules (e.g., for Ceph, NFS)
    - Sysctl settings for network performance
    - Extra mounts for Rook-Ceph OSD paths
  - [ ] Create hostname-specific patches if needed for hardware variations

- [ ] Task 5: Configure encryption and security (AC: #5)
  - [ ] Generate Talos secrets using `talhelper gensecret`
  - [ ] Encrypt secrets to `talsecret.sops.yaml` using AGE key
  - [ ] Verify `.sops.yaml` rules apply to talos secrets
  - [ ] Configure talosconfig output location
  - [ ] Test decryption with `sops -d talsecret.sops.yaml`

- [ ] Task 6: Configure Cilium integration (AC: #2)
  - [ ] Set CNI: none in Talos config (Cilium installed via Helmfile)
  - [ ] Disable kube-proxy (Cilium eBPF replacement)
  - [ ] Configure cluster.id=1 preparation for Cilium
  - [ ] Set appropriate feature flags for eBPF

- [ ] Task 7: Generate and validate configurations (AC: #4)
  - [ ] Run `talhelper genconfig` to generate machine configs
  - [ ] Verify all 6 machine configs are generated
  - [ ] Validate generated configs with `talosctl validate`
  - [ ] Encrypt generated machine configs with SOPS
  - [ ] Test that configs can be decrypted successfully

- [ ] Task 8: Create .gitignore for sensitive files
  - [ ] Exclude unencrypted `talosconfig`
  - [ ] Exclude unencrypted machine configs (keep `.sops.yaml` versions)
  - [ ] Exclude temporary files from talhelper

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document (architecture.md):**

1. **Bootstrap Sequence (Critical Path):**
   ```
   Phase 1: Pre-Flux (Helmfile) - CRD-FIRST PATTERN
   CRDs → Cilium → CoreDNS → Spegel → cert-manager → Flux
   ```
   - Talos provides base OS, CNI set to none
   - Cilium installed via Helmfile in Phase 1

2. **Cilium Cluster Identity:**
   - infra cluster: cluster.id=1, cluster.name=infra
   - This enables future Cluster Mesh capability

3. **Network Topology:**
   - Infra cluster: 10.25.11.0/24
   - MTU 9000 for jumbo frames
   - LACP bonding for network resilience

4. **Technology Stack Versions (December 2025):**
   - Talos Linux v1.12.0 (includes K8s 1.35.0)
   - SOPS AGE key: `age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek`

### Talos Configuration Structure

**talconfig.yaml Template:**
```yaml
---
clusterName: infra
talosVersion: v1.12.0
kubernetesVersion: v1.35.0
endpoint: https://10.25.11.10:6443

# Disable default CNI - Cilium installed via helmfile
cniConfig:
  name: none

# Allow pods on control plane (home lab)
allowSchedulingOnControlPlane: true

# Pod and Service CIDRs
clusterPodNets:
  - 10.42.0.0/16
clusterSvcNets:
  - 10.43.0.0/16

# Node definitions
nodes:
  - hostname: infra-cp-1
    ipAddress: 10.25.11.11
    controlPlane: true
    installDisk: /dev/nvme0n1
    networkInterfaces:
      - interface: bond0
        dhcp: true
        mtu: 9000
        bond:
          mode: 802.3ad
          lacpRate: fast
          interfaces:
            - enp0s1
            - enp0s2
  # ... additional nodes
```

### Talos Patches (Critical for Rook-Ceph)

**patches/common.yaml:**
```yaml
# Kernel modules for Rook-Ceph
machine:
  kernel:
    modules:
      - name: rbd
      - name: ceph

  # Sysctl for network performance
  sysctls:
    net.core.rmem_max: "2500000"
    net.core.wmem_max: "2500000"
    vm.max_map_count: "262144"

  # Extra mounts for Rook-Ceph OSDs
  kubelet:
    extraMounts:
      - destination: /var/lib/rook
        type: bind
        source: /var/lib/rook
        options:
          - bind
          - rshared
          - rw
```

**patches/controlplane.yaml:**
```yaml
# Control plane specific configurations
machine:
  features:
    kubePrism:
      enabled: true
      port: 7445

cluster:
  # Disable kube-proxy (Cilium replaces it)
  proxy:
    disabled: true

  # Enable discovery
  discovery:
    enabled: true
```

### Encryption with SOPS

**SOPS Configuration for Talos Secrets:**
The `.sops.yaml` in repository root should include rules for Talos:
```yaml
creation_rules:
  - path_regex: .*talsecret\.sops\.yaml$
    age: age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek
  - path_regex: clusters/.*/talos/clusterconfig/.*\.sops\.yaml$
    age: age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek
```

**Generate and encrypt secrets:**
```bash
# Generate secrets
talhelper gensecret > talsecret.sops.yaml

# Encrypt with SOPS
sops -e -i talsecret.sops.yaml

# Verify decryption
sops -d talsecret.sops.yaml
```

### Node Hardware Expectations

Based on PRD analysis (6 nodes per cluster):
- Control plane nodes: 3 (10.25.11.11-13)
- Worker nodes: 3 (10.25.11.14-16)
- All nodes have NVMe storage
- Dual network interfaces for LACP bonding

### Critical Implementation Rules

1. **File naming:** Use `.yaml` extension for all config files
2. **SOPS encryption:** All secrets MUST be encrypted before commit
3. **No SSH:** Talos is API-driven only - no SSH access
4. **CNI: none:** Cilium is installed via Helmfile, not Talos
5. **kube-proxy: disabled:** Cilium eBPF replaces kube-proxy

### talhelper Commands Reference

```bash
# Generate secrets (one-time)
talhelper gensecret > talsecret.sops.yaml

# Generate machine configurations
talhelper genconfig

# Generate single node config
talhelper genconfig --node infra-cp-1

# Validate generated configs
talosctl validate --mode metal -c clusterconfig/infra-cp-1.yaml
```

### Project Structure Notes

**Files to create:**
```
k8s-ops/
└── clusters/
    └── infra/
        └── talos/
            ├── talconfig.yaml           # Main configuration
            ├── talsecret.sops.yaml       # Encrypted secrets
            ├── clusterconfig/            # Generated machine configs
            │   └── .gitkeep
            ├── patches/                  # Node customizations
            │   ├── common.yaml
            │   ├── controlplane.yaml
            │   └── worker.yaml
            └── .gitignore                # Exclude unencrypted files
```

### .gitignore for Talos directory

```gitignore
# Unencrypted secrets (always encrypt with SOPS)
talosconfig
*.talosconfig

# Unencrypted machine configs (keep .sops.yaml versions)
!*.sops.yaml

# talhelper temporary files
.talenv
```

### Previous Story Intelligence

**From Epic 0 Stories (Stories 0.1-0.5):**
- Repository structure established at `clusters/infra/`
- SOPS/AGE encryption configured in Story 0.4
- AGE public key: `age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek`
- `.sops.yaml` exists at repository root
- GitHub workflows validate changes before merge

**Key learnings from Epic 0:**
- Use `.yaml` extension consistently
- All sensitive files must be SOPS encrypted
- Validate configurations before considering complete
- Follow kebab-case naming for resources

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1: Create Talos Machine Configurations]
- [Source: _bmad-output/planning-artifacts/architecture.md#Technical Constraints & Dependencies]
- [Source: _bmad-output/planning-artifacts/architecture.md#Bootstrap Sequence]
- [Source: docs/project-context.md#Technology Stack & Versions]
- [Talos v1.12 Documentation](https://www.talos.dev/v1.12/introduction/what-is-talos/)
- [talhelper Documentation](https://budimanjojo.github.io/talhelper/latest/)
- [SOPS AGE Encryption](https://github.com/getsops/sops)

### Technology Stack Versions

| Tool | Version | Notes |
|------|---------|-------|
| Talos Linux | v1.12.0 | Immutable K8s OS |
| Kubernetes | v1.35.0 | Bundled with Talos 1.12.0 |
| talhelper | Latest | Configuration generator |
| SOPS | Latest | Secret encryption |
| AGE | Latest | Encryption key format |

### Validation Checklist

Before marking complete, verify:
- [ ] `clusters/infra/talos/talconfig.yaml` exists and is valid YAML
- [ ] `clusters/infra/talos/talsecret.sops.yaml` is encrypted
- [ ] All 6 node definitions are present in talconfig.yaml
- [ ] Network config includes MTU 9000 and LACP bonding
- [ ] Talos version is v1.12.0, Kubernetes version is v1.35.0
- [ ] CNI is set to none (Cilium via Helmfile)
- [ ] kube-proxy is disabled (Cilium eBPF)
- [ ] `talhelper genconfig` succeeds without errors
- [ ] Generated configs validate with `talosctl validate`
- [ ] Patches exist for controlplane, worker, and common configurations

### Common Gotchas

1. **Install disk paths vary** - Verify actual device paths on each node (may be `/dev/sda`, `/dev/nvme0n1`, etc.)
2. **Network interface names vary** - Check actual interface names per node hardware
3. **LACP requires switch support** - Ensure network switch supports 802.3ad
4. **SOPS encryption required** - Never commit unencrypted secrets
5. **talhelper version compatibility** - Use latest talhelper for Talos 1.12.0 support
6. **Cluster endpoint is VIP** - 10.25.11.10 should be the virtual IP, not a node IP

### Git Commit Message Format

```
feat(talos): create infra cluster machine configurations

- Add talconfig.yaml with 6 node definitions
- Configure MTU 9000 and LACP bonding
- Add node patches for Rook-Ceph and network tuning
- Encrypt secrets with SOPS/AGE
- Set Talos v1.12.0, Kubernetes v1.35.0
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

