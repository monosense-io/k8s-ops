# Story 1.5: Create Operational Taskfiles for Talos

Status: ready-for-dev

## Story

As a **platform operator**,
I want **unified taskfiles for common Talos operations**,
So that **I can manage nodes consistently without remembering complex commands**.

## Acceptance Criteria

1. **Given** a running infra cluster from Story 1.3
   **When** Talos taskfiles are created
   **Then** `.taskfiles/talos/Taskfile.yaml` contains tasks:
   - `talos:apply-node` - Apply machine config to a node
   - `talos:upgrade-node` - Upgrade Talos on a node with rolling strategy
   - `talos:upgrade-k8s` - Upgrade Kubernetes version
   - `talos:reset-cluster` - Reset cluster (with confirmation prompt)
   - `talos:generate-iso` - Generate installer ISO

2. **And** `.taskfiles/op/Taskfile.yaml` contains:
   - `op:push` - Push kubeconfig to 1Password
   - `op:pull` - Pull kubeconfig from 1Password

3. **And** tasks are cluster-aware (accept CLUSTER variable)

4. **And** `task talos:apply-node CLUSTER=infra NODE=10.25.11.11` works correctly

## Tasks / Subtasks

- [ ] Task 1: Create Root Taskfile Structure (AC: #3)
  - [ ] Create `Taskfile.yaml` at repository root with includes for all task categories
  - [ ] Create `.taskfiles/` directory structure
  - [ ] Configure version: '3' schema
  - [ ] Set default shell and cross-platform settings
  - [ ] Add global variables for CLUSTER (default: infra)

- [ ] Task 2: Create Talos Taskfile (AC: #1, #3, #4)
  - [ ] Create `.taskfiles/talos/Taskfile.yaml`
  - [ ] Implement `talos:apply-node` task with NODE and CLUSTER variables
  - [ ] Implement `talos:upgrade-node` task with rolling upgrade logic
  - [ ] Implement `talos:upgrade-k8s` task for Kubernetes version upgrades
  - [ ] Implement `talos:reset-cluster` task with confirmation prompt
  - [ ] Implement `talos:generate-iso` task for installer ISO generation
  - [ ] Add `desc:` blocks for each task for documentation
  - [ ] Add error handling and validation for required variables

- [ ] Task 3: Create 1Password Taskfile (AC: #2)
  - [ ] Create `.taskfiles/op/Taskfile.yaml`
  - [ ] Implement `op:push` task to push kubeconfig to 1Password
  - [ ] Implement `op:pull` task to pull kubeconfig from 1Password
  - [ ] Configure vault and item naming conventions
  - [ ] Add cluster-aware variable handling

- [ ] Task 4: Add Additional Talos Utility Tasks (AC: #1)
  - [ ] Add `talos:health` task to check cluster health
  - [ ] Add `talos:dashboard` task to open interactive dashboard
  - [ ] Add `talos:kubeconfig` task to generate kubeconfig
  - [ ] Add `talos:logs` task to stream node logs
  - [ ] Add `talos:services` task to list services on node

- [ ] Task 5: Test and Validate All Tasks (AC: #1-#4)
  - [ ] Test `task talos:apply-node CLUSTER=infra NODE=10.25.11.11`
  - [ ] Test `task talos:health CLUSTER=infra`
  - [ ] Test `task op:push CLUSTER=infra`
  - [ ] Test `task op:pull CLUSTER=infra`
  - [ ] Verify `task --list` shows all tasks with descriptions
  - [ ] Document any issues or quirks discovered

- [ ] Task 6: Update Documentation
  - [ ] Add taskfile usage section to `docs/runbooks/talos.md`
  - [ ] Document required environment variables
  - [ ] Add troubleshooting section for common issues
  - [ ] Update README with available task commands

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document (architecture.md):**

1. **Taskfile Automation (Unified Operations):**
   | Task Category | Key Operations |
   |---------------|----------------|
   | `bootstrap:*` | Talos bootstrap, K8s apps bootstrap (cluster-aware) |
   | `talos:*` | apply-node, upgrade-node, upgrade-k8s, reset-cluster, generate-iso |
   | `kubernetes:*` | sync-secrets, hr-restart, cleanse-pods, browse-pvc |
   | `volsync:*` | snapshot, restore, unlock |
   | `op:*` | push/pull kubeconfig to 1Password (multi-cluster) |
   | `dr:*` | verify-backups, test-cnpg-restore |

2. **Technology Stack Versions (December 2025):**
   | Component | Version | Notes |
   |-----------|---------|-------|
   | Talos Linux | v1.12.0 | Immutable K8s OS, API-driven (no SSH) |
   | Kubernetes | v1.35.0 | Included with Talos 1.12.0 |
   | Task (go-task) | v3.x | YAML-based task runner |

3. **Cluster Identity Configuration:**
   | Cluster | Network | Endpoint | cluster.id |
   |---------|---------|----------|------------|
   | infra | 10.25.11.0/24 | 10.25.11.10 | 1 |
   | apps | 10.25.13.0/24 | 10.25.13.10 | 2 |

### Project Context Rules (Critical)

**From project-context.md:**

1. **Talos Version:**
   - Talos Linux v1.12.0 - Immutable K8s OS, API-driven (no SSH)

2. **Taskfile Operations:**
   | Task Category | Key Operations |
   |---------------|----------------|
   | `bootstrap:*` | Talos bootstrap, K8s apps bootstrap |
   | `talos:*` | apply-node, upgrade-node, upgrade-k8s |
   | `kubernetes:*` | sync-secrets, hr-restart, cleanse-pods |
   | `volsync:*` | snapshot, restore, unlock |
   | `op:*` | push/pull kubeconfig to 1Password |

3. **SOPS AGE Key:**
   - `age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek`

### Directory Structure

```
k8s-ops/
├── Taskfile.yaml                       # Root taskfile with includes
├── .taskfiles/
│   ├── talos/Taskfile.yaml             # Talos operations (this story)
│   ├── op/Taskfile.yaml                # 1Password operations (this story)
│   ├── bootstrap/Taskfile.yaml         # Bootstrap tasks (from Story 1.2)
│   ├── kubernetes/Taskfile.yaml        # K8s operations (future)
│   ├── flux/Taskfile.yaml              # Flux operations (future)
│   ├── volsync/Taskfile.yaml           # Backup operations (future)
│   └── dr/Taskfile.yaml                # DR operations (future)
└── clusters/
    ├── infra/talos/                    # Infra Talos configs
    │   ├── talconfig.yaml
    │   ├── talsecret.sops.yaml
    │   └── clusterconfig/
    │       ├── talosconfig
    │       └── *.yaml (machine configs)
    └── apps/talos/                     # Apps Talos configs
        ├── talconfig.yaml
        ├── talsecret.sops.yaml
        └── clusterconfig/
```

### Root Taskfile Template

```yaml
---
# yaml-language-server: $schema=https://taskfile.dev/schema.json
version: '3'

vars:
  # Default cluster for operations
  CLUSTER: '{{ .CLUSTER | default "infra" }}'
  # Project root detection
  PROJECT_ROOT:
    sh: git rev-parse --show-toplevel

includes:
  talos:
    taskfile: .taskfiles/talos/Taskfile.yaml
    aliases: [t]
  op:
    taskfile: .taskfiles/op/Taskfile.yaml
  bootstrap:
    taskfile: .taskfiles/bootstrap/Taskfile.yaml
    aliases: [bs]
  # Future includes
  # kubernetes:
  #   taskfile: .taskfiles/kubernetes/Taskfile.yaml
  #   aliases: [k8s]
  # flux:
  #   taskfile: .taskfiles/flux/Taskfile.yaml
  #   aliases: [f]

env:
  # Ensure color output
  FORCE_COLOR: 'true'

tasks:
  default:
    desc: List all available tasks
    cmds:
      - task --list
    silent: true
```

### Talos Taskfile Template

```yaml
---
# yaml-language-server: $schema=https://taskfile.dev/schema.json
version: '3'

vars:
  # Cluster configuration
  CLUSTER: '{{ .CLUSTER | default "infra" }}'
  # Node network mappings
  INFRA_ENDPOINT: '10.25.11.10'
  APPS_ENDPOINT: '10.25.13.10'
  INFRA_NODES: '10.25.11.11,10.25.11.12,10.25.11.13,10.25.11.14,10.25.11.15,10.25.11.16'
  APPS_NODES: '10.25.13.11,10.25.13.12,10.25.13.13,10.25.13.14,10.25.13.15,10.25.13.16'
  # Dynamic endpoint based on cluster
  ENDPOINT: '{{ if eq .CLUSTER "infra" }}{{ .INFRA_ENDPOINT }}{{ else }}{{ .APPS_ENDPOINT }}{{ end }}'
  # Talos config path
  TALOS_DIR: '{{ .PROJECT_ROOT }}/clusters/{{ .CLUSTER }}/talos'
  TALOSCONFIG: '{{ .TALOS_DIR }}/clusterconfig/talosconfig'
  # Talos version for upgrades
  TALOS_VERSION: 'v1.12.0'

tasks:
  apply-node:
    desc: Apply machine configuration to a node
    summary: |
      Apply Talos machine configuration to a specific node.

      Usage:
        task talos:apply-node CLUSTER=infra NODE=10.25.11.11
        task talos:apply-node CLUSTER=infra NODE=10.25.11.11 MODE=try

      Variables:
        CLUSTER: Target cluster (default: infra)
        NODE: Target node IP address (REQUIRED)
        MODE: Apply mode - 'auto' (default), 'try', 'staged', 'no-reboot'
    vars:
      NODE: '{{ .NODE }}'
      MODE: '{{ .MODE | default "auto" }}'
    requires:
      vars: [NODE]
    preconditions:
      - sh: test -f {{ .TALOSCONFIG }}
        msg: "Talos config not found at {{ .TALOSCONFIG }}"
      - sh: test -f {{ .TALOS_DIR }}/clusterconfig/{{ .CLUSTER }}-*.yaml
        msg: "No machine configs found in {{ .TALOS_DIR }}/clusterconfig/"
    cmds:
      - |
        echo "Applying configuration to node {{ .NODE }} in {{ .CLUSTER }} cluster..."
        talosctl apply-config \
          --talosconfig {{ .TALOSCONFIG }} \
          --nodes {{ .NODE }} \
          --mode {{ .MODE }} \
          --file {{ .TALOS_DIR }}/clusterconfig/{{ .CLUSTER }}-{{ .NODE }}.yaml
      - echo "✓ Configuration applied to {{ .NODE }}"

  upgrade-node:
    desc: Upgrade Talos on a specific node with rolling strategy
    summary: |
      Upgrade Talos Linux on a specific node.
      Uses --preserve flag for data retention and waits for node health.

      Usage:
        task talos:upgrade-node CLUSTER=infra NODE=10.25.11.11
        task talos:upgrade-node NODE=10.25.11.11 VERSION=v1.12.1

      Variables:
        CLUSTER: Target cluster (default: infra)
        NODE: Target node IP address (REQUIRED)
        VERSION: Talos version (default: v1.12.0)
    vars:
      NODE: '{{ .NODE }}'
      VERSION: '{{ .VERSION | default .TALOS_VERSION }}'
    requires:
      vars: [NODE]
    preconditions:
      - sh: test -f {{ .TALOSCONFIG }}
        msg: "Talos config not found at {{ .TALOSCONFIG }}"
    cmds:
      - |
        echo "Upgrading node {{ .NODE }} to Talos {{ .VERSION }}..."
        talosctl upgrade \
          --talosconfig {{ .TALOSCONFIG }} \
          --nodes {{ .NODE }} \
          --image ghcr.io/siderolabs/installer:{{ .VERSION }} \
          --preserve \
          --wait \
          --debug
      - task: health
        vars: { CLUSTER: "{{ .CLUSTER }}" }
      - echo "✓ Node {{ .NODE }} upgraded to {{ .VERSION }}"

  upgrade-k8s:
    desc: Upgrade Kubernetes version across the cluster
    summary: |
      Upgrade Kubernetes version on all cluster nodes.
      This upgrades control plane first, then workers.

      Usage:
        task talos:upgrade-k8s CLUSTER=infra K8S_VERSION=1.35.1

      Variables:
        CLUSTER: Target cluster (default: infra)
        K8S_VERSION: Target Kubernetes version (REQUIRED)
    vars:
      K8S_VERSION: '{{ .K8S_VERSION }}'
    requires:
      vars: [K8S_VERSION]
    preconditions:
      - sh: test -f {{ .TALOSCONFIG }}
        msg: "Talos config not found at {{ .TALOSCONFIG }}"
    cmds:
      - |
        echo "Upgrading {{ .CLUSTER }} cluster to Kubernetes v{{ .K8S_VERSION }}..."
        talosctl upgrade-k8s \
          --talosconfig {{ .TALOSCONFIG }} \
          --endpoints {{ .ENDPOINT }} \
          --to {{ .K8S_VERSION }}
      - echo "✓ Kubernetes upgraded to v{{ .K8S_VERSION }}"

  reset-cluster:
    desc: Reset cluster (DANGEROUS - with confirmation prompt)
    summary: |
      Reset the entire Talos cluster. This DESTROYS ALL DATA.
      Requires explicit confirmation.

      Usage:
        task talos:reset-cluster CLUSTER=infra

      Variables:
        CLUSTER: Target cluster (default: infra)
        CONFIRM: Must be 'yes-destroy-all-data' to proceed
    vars:
      CONFIRM: '{{ .CONFIRM }}'
    preconditions:
      - sh: test "{{ .CONFIRM }}" = "yes-destroy-all-data"
        msg: |

          ⚠️  WARNING: This will DESTROY ALL DATA on the {{ .CLUSTER }} cluster!

          To proceed, run:
            task talos:reset-cluster CLUSTER={{ .CLUSTER }} CONFIRM=yes-destroy-all-data

    cmds:
      - |
        echo "⚠️  RESETTING {{ .CLUSTER }} CLUSTER - ALL DATA WILL BE DESTROYED"
        NODES="{{ if eq .CLUSTER "infra" }}{{ .INFRA_NODES }}{{ else }}{{ .APPS_NODES }}{{ end }}"
        for NODE in $(echo $NODES | tr ',' ' '); do
          echo "Resetting node $NODE..."
          talosctl reset \
            --talosconfig {{ .TALOSCONFIG }} \
            --nodes $NODE \
            --graceful=false \
            --reboot=true || true
        done
      - echo "✓ Cluster {{ .CLUSTER }} reset initiated"

  generate-iso:
    desc: Generate Talos installer ISO with embedded configuration
    summary: |
      Generate a Talos installer ISO with machine configuration embedded.
      Useful for bare-metal deployments.

      Usage:
        task talos:generate-iso CLUSTER=infra ARCH=amd64

      Variables:
        CLUSTER: Target cluster (default: infra)
        ARCH: Architecture - amd64, arm64 (default: amd64)
        OUTPUT: Output directory (default: ./iso)
    vars:
      ARCH: '{{ .ARCH | default "amd64" }}'
      OUTPUT: '{{ .OUTPUT | default "./iso" }}'
    cmds:
      - mkdir -p {{ .OUTPUT }}
      - |
        echo "Generating Talos {{ .TALOS_VERSION }} ISO for {{ .CLUSTER }} cluster..."
        talosctl image default \
          --talosconfig {{ .TALOSCONFIG }} \
          --output {{ .OUTPUT }}/talos-{{ .CLUSTER }}-{{ .ARCH }}.iso \
          --arch {{ .ARCH }} \
          --installer-image ghcr.io/siderolabs/installer:{{ .TALOS_VERSION }}
      - echo "✓ ISO generated: {{ .OUTPUT }}/talos-{{ .CLUSTER }}-{{ .ARCH }}.iso"

  health:
    desc: Check Talos cluster health
    summary: |
      Check the health status of all nodes in the cluster.

      Usage:
        task talos:health CLUSTER=infra
        task talos:health CLUSTER=infra TIMEOUT=5m

      Variables:
        CLUSTER: Target cluster (default: infra)
        TIMEOUT: Health check timeout (default: 10m)
    vars:
      TIMEOUT: '{{ .TIMEOUT | default "10m" }}'
    preconditions:
      - sh: test -f {{ .TALOSCONFIG }}
        msg: "Talos config not found at {{ .TALOSCONFIG }}"
    cmds:
      - |
        echo "Checking health of {{ .CLUSTER }} cluster..."
        talosctl health \
          --talosconfig {{ .TALOSCONFIG }} \
          --wait-timeout {{ .TIMEOUT }}
      - echo "✓ Cluster {{ .CLUSTER }} is healthy"

  dashboard:
    desc: Open Talos interactive dashboard
    summary: |
      Open the interactive Talos dashboard for a node.

      Usage:
        task talos:dashboard CLUSTER=infra NODE=10.25.11.11

      Variables:
        CLUSTER: Target cluster (default: infra)
        NODE: Target node IP (optional - uses endpoint if not specified)
    vars:
      NODE: '{{ .NODE | default .ENDPOINT }}'
    preconditions:
      - sh: test -f {{ .TALOSCONFIG }}
        msg: "Talos config not found at {{ .TALOSCONFIG }}"
    cmds:
      - |
        talosctl dashboard \
          --talosconfig {{ .TALOSCONFIG }} \
          --nodes {{ .NODE }}

  kubeconfig:
    desc: Generate kubeconfig for the cluster
    summary: |
      Generate a kubeconfig file for kubectl access.

      Usage:
        task talos:kubeconfig CLUSTER=infra
        task talos:kubeconfig CLUSTER=infra OUTPUT=~/.kube/infra

      Variables:
        CLUSTER: Target cluster (default: infra)
        OUTPUT: Output path (default: ~/.kube/k8s-ops-{CLUSTER})
    vars:
      OUTPUT: '{{ .OUTPUT | default (printf "~/.kube/k8s-ops-%s" .CLUSTER) }}'
    preconditions:
      - sh: test -f {{ .TALOSCONFIG }}
        msg: "Talos config not found at {{ .TALOSCONFIG }}"
    cmds:
      - |
        echo "Generating kubeconfig for {{ .CLUSTER }} cluster..."
        talosctl kubeconfig \
          --talosconfig {{ .TALOSCONFIG }} \
          --nodes {{ .ENDPOINT }} \
          --force \
          -f {{ .OUTPUT }}
      - echo "✓ Kubeconfig saved to {{ .OUTPUT }}"

  logs:
    desc: Stream logs from a Talos node
    summary: |
      Stream logs from a specific service on a Talos node.

      Usage:
        task talos:logs CLUSTER=infra NODE=10.25.11.11
        task talos:logs NODE=10.25.11.11 SERVICE=etcd

      Variables:
        CLUSTER: Target cluster (default: infra)
        NODE: Target node IP address (REQUIRED)
        SERVICE: Service to tail logs (optional - all if not specified)
    vars:
      NODE: '{{ .NODE }}'
      SERVICE: '{{ .SERVICE }}'
    requires:
      vars: [NODE]
    preconditions:
      - sh: test -f {{ .TALOSCONFIG }}
        msg: "Talos config not found at {{ .TALOSCONFIG }}"
    cmds:
      - |
        talosctl logs \
          --talosconfig {{ .TALOSCONFIG }} \
          --nodes {{ .NODE }} \
          {{ if .SERVICE }}{{ .SERVICE }}{{ end }} \
          --follow

  services:
    desc: List services running on a Talos node
    summary: |
      List all services and their status on a Talos node.

      Usage:
        task talos:services CLUSTER=infra NODE=10.25.11.11

      Variables:
        CLUSTER: Target cluster (default: infra)
        NODE: Target node IP address (REQUIRED)
    vars:
      NODE: '{{ .NODE }}'
    requires:
      vars: [NODE]
    preconditions:
      - sh: test -f {{ .TALOSCONFIG }}
        msg: "Talos config not found at {{ .TALOSCONFIG }}"
    cmds:
      - |
        talosctl services \
          --talosconfig {{ .TALOSCONFIG }} \
          --nodes {{ .NODE }}
```

### 1Password Taskfile Template

```yaml
---
# yaml-language-server: $schema=https://taskfile.dev/schema.json
version: '3'

vars:
  CLUSTER: '{{ .CLUSTER | default "infra" }}'
  # 1Password vault for kubeconfig storage
  OP_VAULT: 'k8s-ops'
  # Item naming pattern
  OP_ITEM_PREFIX: 'kubeconfig-'
  # Kubeconfig paths
  KUBECONFIG_PATH: '{{ .HOME }}/.kube/k8s-ops-{{ .CLUSTER }}'

tasks:
  push:
    desc: Push kubeconfig to 1Password
    summary: |
      Push the cluster kubeconfig to 1Password for secure storage.

      Usage:
        task op:push CLUSTER=infra

      Variables:
        CLUSTER: Target cluster (default: infra)
    preconditions:
      - sh: command -v op
        msg: "1Password CLI (op) not found. Install from: https://1password.com/downloads/command-line/"
      - sh: op whoami
        msg: "Not signed in to 1Password. Run: eval $(op signin)"
      - sh: test -f {{ .KUBECONFIG_PATH }}
        msg: "Kubeconfig not found at {{ .KUBECONFIG_PATH }}"
    cmds:
      - |
        echo "Pushing kubeconfig for {{ .CLUSTER }} to 1Password..."

        ITEM_NAME="{{ .OP_ITEM_PREFIX }}{{ .CLUSTER }}"

        # Check if item exists
        if op item get "$ITEM_NAME" --vault="{{ .OP_VAULT }}" > /dev/null 2>&1; then
          echo "Updating existing item $ITEM_NAME..."
          op item edit "$ITEM_NAME" \
            --vault="{{ .OP_VAULT }}" \
            "kubeconfig[file]={{ .KUBECONFIG_PATH }}"
        else
          echo "Creating new item $ITEM_NAME..."
          op item create \
            --category=document \
            --vault="{{ .OP_VAULT }}" \
            --title="$ITEM_NAME" \
            "kubeconfig[file]={{ .KUBECONFIG_PATH }}"
        fi
      - echo "✓ Kubeconfig pushed to 1Password vault {{ .OP_VAULT }}"

  pull:
    desc: Pull kubeconfig from 1Password
    summary: |
      Pull the cluster kubeconfig from 1Password to local filesystem.

      Usage:
        task op:pull CLUSTER=infra
        task op:pull CLUSTER=infra OUTPUT=~/.kube/custom-path

      Variables:
        CLUSTER: Target cluster (default: infra)
        OUTPUT: Output path (default: ~/.kube/k8s-ops-{CLUSTER})
    vars:
      OUTPUT: '{{ .OUTPUT | default .KUBECONFIG_PATH }}'
    preconditions:
      - sh: command -v op
        msg: "1Password CLI (op) not found. Install from: https://1password.com/downloads/command-line/"
      - sh: op whoami
        msg: "Not signed in to 1Password. Run: eval $(op signin)"
    cmds:
      - |
        echo "Pulling kubeconfig for {{ .CLUSTER }} from 1Password..."

        ITEM_NAME="{{ .OP_ITEM_PREFIX }}{{ .CLUSTER }}"

        op document get "$ITEM_NAME" \
          --vault="{{ .OP_VAULT }}" \
          --out-file={{ .OUTPUT }}

        chmod 600 {{ .OUTPUT }}
      - echo "✓ Kubeconfig saved to {{ .OUTPUT }}"

  list:
    desc: List all kubeconfigs stored in 1Password
    summary: |
      List all kubeconfig items stored in the 1Password vault.

      Usage:
        task op:list
    preconditions:
      - sh: command -v op
        msg: "1Password CLI (op) not found"
      - sh: op whoami
        msg: "Not signed in to 1Password"
    cmds:
      - |
        echo "Kubeconfigs in {{ .OP_VAULT }} vault:"
        op item list \
          --vault="{{ .OP_VAULT }}" \
          --format=json | jq -r '.[] | select(.title | startswith("{{ .OP_ITEM_PREFIX }}")) | "  - \(.title)"'
```

### talosctl Commands Reference

**Essential commands for Talos management:**

```bash
# Configuration Management
talosctl gen config <cluster-name> https://<endpoint>:6443  # Generate configs
talosctl apply-config --insecure -n <node-ip> --file <config>.yaml  # Apply config
talosctl apply-config -n <node-ip> --mode try --file <config>.yaml  # Try mode (1min rollback)
talosctl apply-config -n <node-ip> --dry-run --file <config>.yaml  # Dry run

# Cluster Bootstrap
talosctl bootstrap --nodes <ip> --endpoints <ip>  # Bootstrap control plane
talosctl kubeconfig  # Generate kubeconfig

# Health & Monitoring
talosctl health --wait-timeout 10m  # Health check with timeout
talosctl dashboard  # Interactive dashboard
talosctl services  # List services
talosctl logs <service> --follow  # Stream logs
talosctl containers  # List containers

# Upgrades
talosctl upgrade -n <ip> --image ghcr.io/siderolabs/installer:v1.x.x --preserve --wait
talosctl upgrade-k8s --to <version>  # Upgrade Kubernetes

# Troubleshooting
talosctl dmesg  # Kernel messages
talosctl netstat  # Network connections
talosctl memory  # Memory stats
talosctl processes  # Running processes

# Reset (DANGEROUS)
talosctl reset --graceful=false --reboot=true  # Reset node
```

### Previous Story Intelligence

**From Story 1.3 (Bootstrap Infra Cluster):**
- Taskfile structure established in `.taskfiles/bootstrap/Taskfile.yaml`
- Bootstrap sequence: CRDs → Cilium → CoreDNS → Spegel → cert-manager → Flux
- talosctl commands tested and working for bootstrap
- Kubeconfig generation via `talosctl kubeconfig`

**From Story 1.4 (External Secrets Operator):**
- 1Password vault `k8s-ops` used for secrets
- `op inject` pattern used for secrets injection
- Token rotation procedure documented (90-day expiration)

**Key Learnings:**
- Always use `.yaml` extension consistently (not `.yml`)
- Add `desc:` blocks for task documentation (`task --list`)
- Use preconditions to validate requirements before execution
- Variable defaults with `{{ .VAR | default "value" }}`
- Cross-cluster support via CLUSTER variable
- Error handling with meaningful messages

### Latest Technical Information (December 2025)

**Talos Linux:**
- Current stable version: v1.12.0 (includes Kubernetes 1.35.0)
- Key talosctl features:
  - `apply-config --mode try` for safe config testing (auto-rollback in 1 min)
  - `apply-config --dry-run` to preview changes
  - `upgrade --preserve` to retain ephemeral data
  - New `image cache-serve` subcommand for OCI registry serving
- Endpoints vs Nodes: Endpoints are load balancers/control planes, nodes are targets
- No SSH access - all management via talosctl API

**Taskfile (go-task):**
- Version 3 schema recommended
- Best practices:
  - Add `desc:` blocks for all tasks
  - Use `requires.vars` for mandatory variables
  - Use `preconditions` for validation
  - Pin binary version in CI/CD
  - Use `dir:` attribute for subdirectory execution
  - Validate YAML before commit
- Cross-platform: Declare target shell, avoid shell-specific constructs
- Documentation: `task --list` shows all tasks with descriptions

### Critical Implementation Rules

1. **Cluster Variable Convention:**
   - Always accept CLUSTER variable (default: infra)
   - Map CLUSTER to correct endpoints and node ranges
   - Use consistent naming: k8s-ops-{CLUSTER}

2. **Talos Configuration:**
   - TALOSCONFIG path: `clusters/{CLUSTER}/talos/clusterconfig/talosconfig`
   - Machine configs: `clusters/{CLUSTER}/talos/clusterconfig/{CLUSTER}-{NODE}.yaml`
   - Always use --talosconfig flag

3. **1Password Integration:**
   - Vault: `k8s-ops`
   - Item naming: `kubeconfig-{CLUSTER}`
   - Require `op whoami` check before operations
   - Set proper permissions (chmod 600) on kubeconfig

4. **Safety Considerations:**
   - Reset operations MUST require explicit confirmation
   - Use `--preserve` flag for upgrades
   - Use `--mode try` for config testing
   - Add timeout to health checks

5. **Documentation:**
   - Every task MUST have a `desc:` field
   - Complex tasks should have `summary:` with usage examples
   - Document all variables in summary

### Environment Variables Required

```bash
# Talos configuration (set dynamically by tasks)
export TALOSCONFIG=clusters/{CLUSTER}/talos/clusterconfig/talosconfig

# Kubernetes configuration
export KUBECONFIG=~/.kube/k8s-ops-{CLUSTER}

# 1Password (must be signed in)
eval $(op signin)

# SOPS AGE key (for decrypting secrets)
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
```

### Troubleshooting Guide

**Issue: "Talos config not found"**
- Cause: TALOSCONFIG path incorrect or file missing
- Fix: Verify `clusters/{CLUSTER}/talos/clusterconfig/talosconfig` exists
- Command: `ls -la clusters/infra/talos/clusterconfig/`

**Issue: "Node unreachable"**
- Cause: Network connectivity or node powered off
- Fix: Verify node IP and network connectivity
- Command: `ping 10.25.11.11`

**Issue: "Not signed in to 1Password"**
- Cause: 1Password CLI session expired
- Fix: Sign in again
- Command: `eval $(op signin)`

**Issue: "Apply config fails with validation error"**
- Cause: Invalid machine configuration
- Fix: Use `--dry-run` first to identify issues
- Command: `talosctl apply-config --dry-run --file config.yaml`

**Issue: "Upgrade fails with timeout"**
- Cause: Slow network or resource constraints
- Fix: Increase timeout or check node resources
- Command: `talosctl health --wait-timeout 20m`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.5: Create Operational Taskfiles for Talos]
- [Source: _bmad-output/planning-artifacts/architecture.md#Taskfile Automation]
- [Source: docs/project-context.md#Technology Stack & Versions]
- [Talos CLI Reference](https://www.talos.dev/v1.12/learn-more/talosctl/)
- [Taskfile Documentation](https://taskfile.dev/usage/)
- [Taskfile Best Practices](https://taskfile.dev/docs/guide)
- [1Password CLI](https://developer.1password.com/docs/cli)

### Validation Checklist

Before marking complete, verify:
- [ ] `Taskfile.yaml` exists at repository root
- [ ] `.taskfiles/talos/Taskfile.yaml` created with all required tasks
- [ ] `.taskfiles/op/Taskfile.yaml` created with push/pull tasks
- [ ] `task --list` shows all tasks with descriptions
- [ ] `task talos:health CLUSTER=infra` executes successfully
- [ ] `task talos:apply-node NODE=10.25.11.11 CLUSTER=infra` executes correctly
- [ ] `task op:push CLUSTER=infra` pushes kubeconfig to 1Password
- [ ] `task op:pull CLUSTER=infra` pulls kubeconfig from 1Password
- [ ] All tasks support CLUSTER variable
- [ ] Reset task requires explicit confirmation
- [ ] Documentation updated in docs/runbooks/

### Git Commit Message Format

```
feat(taskfiles): create operational taskfiles for Talos and 1Password

- Add root Taskfile.yaml with includes for all task categories
- Create .taskfiles/talos/Taskfile.yaml with:
  - talos:apply-node, talos:upgrade-node, talos:upgrade-k8s
  - talos:reset-cluster (with confirmation), talos:generate-iso
  - talos:health, talos:dashboard, talos:kubeconfig, talos:logs, talos:services
- Create .taskfiles/op/Taskfile.yaml with:
  - op:push, op:pull, op:list for kubeconfig management
- All tasks are cluster-aware via CLUSTER variable
- Add comprehensive documentation and error handling
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
