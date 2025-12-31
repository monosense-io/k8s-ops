# Story 3.1: Create Flux Operational Taskfiles

Status: ready-for-dev

## Story

As a **platform operator**,
I want **taskfile commands for common Flux operations**,
So that **I can manage reconciliation without memorizing kubectl commands and have consistent, repeatable operations across both clusters**.

## Acceptance Criteria

1. **Given** a running cluster with Flux operational
   **When** Flux taskfiles are created
   **Then** `.taskfiles/flux/Taskfile.yaml` contains tasks:
   - `flux:reconcile` - Trigger reconciliation for a Kustomization or HelmRelease
   - `flux:suspend` - Suspend reconciliation for an app or namespace
   - `flux:resume` - Resume reconciliation for an app or namespace
   - `flux:logs` - Stream Flux controller logs
   - `flux:events` - Show recent Flux events
   - `flux:diff` - Preview changes before reconciliation

2. **And** tasks accept APP and CLUSTER variables

3. **And** `task flux:suspend APP=odoo CLUSTER=apps` correctly suspends the HelmRelease

4. **And** `task flux:reconcile APP=odoo CLUSTER=apps` triggers immediate reconciliation

## Tasks / Subtasks

- [ ] Task 1: Create Taskfile Directory Structure (AC: #1)
  - [ ] Create `.taskfiles/flux/` directory
  - [ ] Create root `Taskfile.yaml` if not exists (references `.taskfiles/`)
  - [ ] Ensure correct directory permissions

- [ ] Task 2: Create Flux Taskfile with Core Tasks (AC: #1, #2)
  - [ ] Create `.taskfiles/flux/Taskfile.yaml` with version 3
  - [ ] Define CLUSTER variable with default (infra)
  - [ ] Define APP variable (required for app-specific tasks)
  - [ ] Define NAMESPACE variable with fallback to APP
  - [ ] Implement `flux:reconcile` task
  - [ ] Implement `flux:suspend` task
  - [ ] Implement `flux:resume` task
  - [ ] Implement `flux:logs` task
  - [ ] Implement `flux:events` task
  - [ ] Implement `flux:diff` task

- [ ] Task 3: Implement Multi-Cluster Context Handling (AC: #2, #3, #4)
  - [ ] Use CLUSTER variable to set kubectl context
  - [ ] Validate CLUSTER is valid (infra or apps)
  - [ ] Use `--context=${CLUSTER}` for all kubectl/flux commands
  - [ ] Add helper task for context verification

- [ ] Task 4: Create Root Taskfile.yaml (AC: #1)
  - [ ] Create `Taskfile.yaml` at repository root
  - [ ] Include `.taskfiles/flux/Taskfile.yaml`
  - [ ] Define global variables (CLUSTER default)
  - [ ] Add includes for future taskfile directories

- [ ] Task 5: Add Advanced Flux Tasks
  - [ ] `flux:status` - Show status of all Flux resources
  - [ ] `flux:check` - Run flux check command
  - [ ] `flux:tree` - Show dependency tree for a Kustomization
  - [ ] `flux:alerts` - Show recent alerts
  - [ ] `flux:trace` - Trace a Flux resource to its source

- [ ] Task 6: Verify Taskfile Operations (AC: #3, #4)
  - [ ] Test `task flux:reconcile APP=gatus CLUSTER=infra`
  - [ ] Test `task flux:suspend APP=gatus CLUSTER=infra`
  - [ ] Test `task flux:resume APP=gatus CLUSTER=infra`
  - [ ] Test `task flux:logs CLUSTER=infra`
  - [ ] Test `task flux:events CLUSTER=infra`
  - [ ] Verify --help output for all tasks

- [ ] Task 7: Document and Finalize
  - [ ] Add usage examples in task descriptions
  - [ ] Document in runbook or README
  - [ ] Update project-context.md with taskfile patterns

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document (architecture.md):**

1. **FRs Covered (Epic 3: GitOps Operations):**
   - FR4: Operator can view Flux reconciliation status for all clusters
   - FR5: Operator can trigger manual reconciliation when needed
   - FR6: Operator can suspend and resume Flux reconciliation per application or cluster

2. **Taskfile Automation Patterns (from architecture.md):**
   | Task Category | Key Operations |
   |---------------|----------------|
   | `bootstrap:*` | Talos bootstrap, K8s apps bootstrap (cluster-aware) |
   | `talos:*` | apply-node, upgrade-node, upgrade-k8s, reset-cluster, generate-iso |
   | `kubernetes:*` | sync-secrets, hr-restart, cleanse-pods, browse-pvc |
   | `volsync:*` | snapshot, restore, unlock |
   | `op:*` | push/pull kubeconfig to 1Password (multi-cluster) |
   | `dr:*` | verify-backups, test-cnpg-restore (NEW) |
   | **`flux:*`** | **reconcile, suspend, resume, logs, events, diff** |

3. **Multi-Cluster Context:**
   - Infra cluster: `infra` context
   - Apps cluster: `apps` context
   - Tasks MUST support CLUSTER variable

4. **Technology Stack:**
   - Flux CD v2.7.5
   - Kubernetes 1.35.0 (via Talos 1.12.0)
   - Task (go-task/task) for automation

### Project Context Rules (Critical)

**From project-context.md:**

1. **File Naming Standards:**
   - Use `.yaml` extension (not `.yml`)
   - Taskfile entry point: `Taskfile.yaml`

2. **Directory Structure (from architecture.md):**
   ```
   .taskfiles/
   ├── bootstrap/Taskfile.yaml     # bootstrap:infra, bootstrap:apps
   ├── talos/Taskfile.yaml         # talos:apply, talos:upgrade
   ├── kubernetes/Taskfile.yaml    # k8s:sync-secrets, k8s:hr-restart
   ├── volsync/Taskfile.yaml       # volsync:snapshot, volsync:restore
   ├── flux/Taskfile.yaml          # flux:reconcile, flux:suspend
   ├── dr/Taskfile.yaml            # dr:verify-backups, dr:test-restore
   └── op/Taskfile.yaml            # op:push, op:pull kubeconfig
   ```

3. **Git Commit Message Format:**
   ```
   <type>(<scope>): <description>

   Types: feat, fix, refactor, chore, docs, ci
   Scopes: infra, apps, flux, talos, bootstrap, renovate
   ```

### Flux CD CLI Commands Reference

**From Flux CD v2.7.5 Documentation:**

1. **Reconcile Commands:**
   - `flux reconcile ks <name>` - Reconcile a Kustomization
   - `flux reconcile hr <name>` - Reconcile a HelmRelease
   - `flux reconcile source git <name>` - Reconcile a GitRepository

2. **Suspend Commands:**
   - `flux suspend ks <name>` - Suspend a Kustomization
   - `flux suspend hr <name>` - Suspend a HelmRelease
   - `flux suspend ks --all` - Suspend all Kustomizations

3. **Resume Commands:**
   - `flux resume ks <name>` - Resume a Kustomization
   - `flux resume hr <name>` - Resume a HelmRelease
   - `flux resume ks --all --wait` - Resume all and wait

4. **Other Commands:**
   - `flux logs` - Stream Flux controller logs
   - `flux events` - Show recent Flux events
   - `flux diff kustomization <name>` - Preview changes
   - `flux tree ks <name>` - Show dependency tree
   - `flux check` - Check Flux components health
   - `flux trace <name>` - Trace resource to source

### Taskfile Patterns (Established)

**Standard Taskfile v3 Structure:**

```yaml
version: "3"

vars:
  CLUSTER: '{{.CLUSTER | default "infra"}}'

tasks:
  task-name:
    desc: Short description
    summary: |
      Longer description with usage examples.

      Examples:
        task flux:reconcile APP=gatus CLUSTER=infra
    requires:
      vars: [APP]  # Required variables
    cmds:
      - flux reconcile ks {{.APP}} --context={{.CLUSTER}}
    preconditions:
      - sh: kubectl config get-contexts {{.CLUSTER}} &>/dev/null
        msg: "Cluster context '{{.CLUSTER}}' not found"
```

**Multi-Cluster Pattern:**

```yaml
vars:
  CLUSTER: '{{.CLUSTER | default "infra"}}'
  KUBECONFIG: '{{.KUBECONFIG | default "~/.kube/config"}}'

tasks:
  reconcile:
    cmds:
      - flux reconcile ks {{.APP}} --context={{.CLUSTER}}
```

### Directory Structure

```
k8s-ops/
├── Taskfile.yaml                    # Root entry point (includes .taskfiles/)
└── .taskfiles/
    └── flux/
        └── Taskfile.yaml            # Flux-specific tasks
```

### Taskfile Templates

**Root Taskfile.yaml:**

```yaml
---
version: "3"

vars:
  CLUSTER: '{{.CLUSTER | default "infra"}}'

includes:
  flux:
    taskfile: .taskfiles/flux/Taskfile.yaml
    aliases: ["f"]
```

**.taskfiles/flux/Taskfile.yaml:**

```yaml
---
version: "3"

vars:
  CLUSTER: '{{.CLUSTER | default "infra"}}'
  NAMESPACE: '{{.NAMESPACE | default "flux-system"}}'

tasks:
  reconcile:
    desc: Trigger Flux reconciliation for a Kustomization or HelmRelease
    summary: |
      Triggers immediate reconciliation of a Flux Kustomization.

      Variables:
        APP     - Required. Name of the Kustomization/HelmRelease.
        CLUSTER - Optional. Target cluster context (default: infra).
        TYPE    - Optional. Resource type: ks or hr (default: ks).

      Examples:
        task flux:reconcile APP=gatus
        task flux:reconcile APP=odoo CLUSTER=apps
        task flux:reconcile APP=odoo TYPE=hr CLUSTER=apps
    requires:
      vars: [APP]
    vars:
      TYPE: '{{.TYPE | default "ks"}}'
    cmds:
      - flux reconcile {{.TYPE}} {{.APP}} --context={{.CLUSTER}} -n flux-system
    preconditions:
      - sh: kubectl config get-contexts {{.CLUSTER}} &>/dev/null
        msg: "Cluster context '{{.CLUSTER}}' not found"
      - sh: which flux
        msg: "flux CLI not found in PATH"

  suspend:
    desc: Suspend Flux reconciliation for an app or namespace
    summary: |
      Suspends reconciliation of a Flux Kustomization or HelmRelease.
      The resource will not reconcile until resumed.

      Variables:
        APP     - Required. Name of the Kustomization/HelmRelease.
        CLUSTER - Optional. Target cluster context (default: infra).
        TYPE    - Optional. Resource type: ks or hr (default: ks).

      Examples:
        task flux:suspend APP=odoo CLUSTER=apps
        task flux:suspend APP=odoo TYPE=hr CLUSTER=apps
    requires:
      vars: [APP]
    vars:
      TYPE: '{{.TYPE | default "ks"}}'
    cmds:
      - flux suspend {{.TYPE}} {{.APP}} --context={{.CLUSTER}} -n flux-system
    preconditions:
      - sh: kubectl config get-contexts {{.CLUSTER}} &>/dev/null
        msg: "Cluster context '{{.CLUSTER}}' not found"

  resume:
    desc: Resume Flux reconciliation for an app
    summary: |
      Resumes a previously suspended Kustomization or HelmRelease.

      Variables:
        APP     - Required. Name of the Kustomization/HelmRelease.
        CLUSTER - Optional. Target cluster context (default: infra).
        TYPE    - Optional. Resource type: ks or hr (default: ks).
        WAIT    - Optional. Wait for reconciliation (default: false).

      Examples:
        task flux:resume APP=odoo CLUSTER=apps
        task flux:resume APP=odoo TYPE=hr WAIT=true
    requires:
      vars: [APP]
    vars:
      TYPE: '{{.TYPE | default "ks"}}'
      WAIT_FLAG: '{{if eq .WAIT "true"}}--wait{{end}}'
    cmds:
      - flux resume {{.TYPE}} {{.APP}} --context={{.CLUSTER}} -n flux-system {{.WAIT_FLAG}}
    preconditions:
      - sh: kubectl config get-contexts {{.CLUSTER}} &>/dev/null
        msg: "Cluster context '{{.CLUSTER}}' not found"

  logs:
    desc: Stream Flux controller logs
    summary: |
      Streams logs from Flux controllers (source, kustomize, helm, notification).

      Variables:
        CLUSTER    - Optional. Target cluster context (default: infra).
        CONTROLLER - Optional. Specific controller to filter (all by default).
        LEVEL      - Optional. Log level filter: info, debug, error.

      Examples:
        task flux:logs
        task flux:logs CLUSTER=apps
        task flux:logs CONTROLLER=kustomize-controller
        task flux:logs LEVEL=error
    vars:
      CONTROLLER_FLAG: '{{if .CONTROLLER}}--flux-namespace=flux-system {{.CONTROLLER}}{{end}}'
      LEVEL_FLAG: '{{if .LEVEL}}--level={{.LEVEL}}{{end}}'
    cmds:
      - flux logs --context={{.CLUSTER}} {{.LEVEL_FLAG}} --follow
    preconditions:
      - sh: kubectl config get-contexts {{.CLUSTER}} &>/dev/null
        msg: "Cluster context '{{.CLUSTER}}' not found"

  events:
    desc: Show recent Flux events
    summary: |
      Shows recent events for Flux resources, useful for troubleshooting.

      Variables:
        CLUSTER   - Optional. Target cluster context (default: infra).
        APP       - Optional. Filter events for specific app.
        NAMESPACE - Optional. Filter by namespace (default: all).

      Examples:
        task flux:events
        task flux:events CLUSTER=apps
        task flux:events APP=gatus
    vars:
      APP_FILTER: '{{if .APP}}| grep -i {{.APP}}{{end}}'
    cmds:
      - flux events --context={{.CLUSTER}} --for=all-namespaces {{.APP_FILTER}}
    preconditions:
      - sh: kubectl config get-contexts {{.CLUSTER}} &>/dev/null
        msg: "Cluster context '{{.CLUSTER}}' not found"

  diff:
    desc: Preview changes before reconciliation
    summary: |
      Shows what would change if the Kustomization were to reconcile.
      Uses server-side dry-run to show actual diff.

      Variables:
        APP     - Required. Name of the Kustomization.
        CLUSTER - Optional. Target cluster context (default: infra).

      Examples:
        task flux:diff APP=gatus
        task flux:diff APP=odoo CLUSTER=apps
    requires:
      vars: [APP]
    cmds:
      - flux diff kustomization {{.APP}} --context={{.CLUSTER}}
    preconditions:
      - sh: kubectl config get-contexts {{.CLUSTER}} &>/dev/null
        msg: "Cluster context '{{.CLUSTER}}' not found"

  status:
    desc: Show status of all Flux resources
    summary: |
      Displays the status of all Flux resources in the cluster.

      Variables:
        CLUSTER - Optional. Target cluster context (default: infra).
        TYPE    - Optional. Filter by type: ks, hr, source, all (default: all).

      Examples:
        task flux:status
        task flux:status CLUSTER=apps
        task flux:status TYPE=hr
    vars:
      TYPE: '{{.TYPE | default "all"}}'
    cmds:
      - |
        {{if eq .TYPE "all"}}
        echo "=== Kustomizations ===" && flux get ks --context={{.CLUSTER}} -A
        echo "" && echo "=== HelmReleases ===" && flux get hr --context={{.CLUSTER}} -A
        echo "" && echo "=== Sources ===" && flux get sources all --context={{.CLUSTER}} -A
        {{else if eq .TYPE "ks"}}
        flux get ks --context={{.CLUSTER}} -A
        {{else if eq .TYPE "hr"}}
        flux get hr --context={{.CLUSTER}} -A
        {{else if eq .TYPE "source"}}
        flux get sources all --context={{.CLUSTER}} -A
        {{end}}
    preconditions:
      - sh: kubectl config get-contexts {{.CLUSTER}} &>/dev/null
        msg: "Cluster context '{{.CLUSTER}}' not found"

  check:
    desc: Run Flux health check
    summary: |
      Validates Flux installation and checks component health.

      Variables:
        CLUSTER - Optional. Target cluster context (default: infra).

      Examples:
        task flux:check
        task flux:check CLUSTER=apps
    cmds:
      - flux check --context={{.CLUSTER}}
    preconditions:
      - sh: kubectl config get-contexts {{.CLUSTER}} &>/dev/null
        msg: "Cluster context '{{.CLUSTER}}' not found"

  tree:
    desc: Show dependency tree for a Kustomization
    summary: |
      Displays the dependency tree for a Kustomization, showing
      what resources depend on it and what it depends on.

      Variables:
        APP     - Required. Name of the Kustomization.
        CLUSTER - Optional. Target cluster context (default: infra).

      Examples:
        task flux:tree APP=cluster-apps
        task flux:tree APP=odoo CLUSTER=apps
    requires:
      vars: [APP]
    cmds:
      - flux tree ks {{.APP}} --context={{.CLUSTER}} -n flux-system
    preconditions:
      - sh: kubectl config get-contexts {{.CLUSTER}} &>/dev/null
        msg: "Cluster context '{{.CLUSTER}}' not found"

  trace:
    desc: Trace a Flux resource to its source
    summary: |
      Traces a Kubernetes resource back to its Flux source,
      showing the complete reconciliation path.

      Variables:
        RESOURCE  - Required. Resource in format type/name (e.g., deploy/gatus).
        NAMESPACE - Required. Namespace of the resource.
        CLUSTER   - Optional. Target cluster context (default: infra).

      Examples:
        task flux:trace RESOURCE=deploy/gatus NAMESPACE=observability
        task flux:trace RESOURCE=hr/odoo NAMESPACE=business CLUSTER=apps
    requires:
      vars: [RESOURCE, NAMESPACE]
    cmds:
      - flux trace {{.RESOURCE}} -n {{.NAMESPACE}} --context={{.CLUSTER}}
    preconditions:
      - sh: kubectl config get-contexts {{.CLUSTER}} &>/dev/null
        msg: "Cluster context '{{.CLUSTER}}' not found"

  suspend-all:
    desc: Suspend all Kustomizations (emergency stop)
    summary: |
      EMERGENCY: Suspends ALL Kustomizations in the cluster.
      This stops all Flux reconciliation. Use with caution.

      Variables:
        CLUSTER - Optional. Target cluster context (default: infra).

      Examples:
        task flux:suspend-all CLUSTER=apps
    prompt: This will suspend ALL Flux reconciliation. Are you sure?
    cmds:
      - flux suspend ks --all --context={{.CLUSTER}}
    preconditions:
      - sh: kubectl config get-contexts {{.CLUSTER}} &>/dev/null
        msg: "Cluster context '{{.CLUSTER}}' not found"

  resume-all:
    desc: Resume all Kustomizations
    summary: |
      Resumes all previously suspended Kustomizations.

      Variables:
        CLUSTER - Optional. Target cluster context (default: infra).
        WAIT    - Optional. Wait for reconciliation (default: false).

      Examples:
        task flux:resume-all CLUSTER=apps
        task flux:resume-all WAIT=true
    vars:
      WAIT_FLAG: '{{if eq .WAIT "true"}}--wait{{end}}'
    cmds:
      - flux resume ks --all --context={{.CLUSTER}} {{.WAIT_FLAG}}
    preconditions:
      - sh: kubectl config get-contexts {{.CLUSTER}} &>/dev/null
        msg: "Cluster context '{{.CLUSTER}}' not found"

  reconcile-source:
    desc: Reconcile GitRepository source
    summary: |
      Forces the GitRepository to fetch latest changes.
      Use this when you've pushed changes and want immediate reconciliation.

      Variables:
        SOURCE  - Optional. GitRepository name (default: k8s-ops).
        CLUSTER - Optional. Target cluster context (default: infra).

      Examples:
        task flux:reconcile-source
        task flux:reconcile-source CLUSTER=apps
    vars:
      SOURCE: '{{.SOURCE | default "k8s-ops"}}'
    cmds:
      - flux reconcile source git {{.SOURCE}} --context={{.CLUSTER}}
    preconditions:
      - sh: kubectl config get-contexts {{.CLUSTER}} &>/dev/null
        msg: "Cluster context '{{.CLUSTER}}' not found"
```

### Previous Story Intelligence

**From Story 2.6 (Configure Resource Management Policies):**
- Directory structure patterns established
- Flux Kustomization hierarchy understood
- Priority classes and resource management deployed

**From Epic 2 Stories:**
- Consistent use of `.yaml` extension
- Flux reconciliation patterns for infrastructure
- Multi-cluster awareness (infra vs apps)

**Key Learnings:**
- Use `.yaml` extension consistently
- Tasks should be cluster-aware with CLUSTER variable
- Include preconditions for validation
- Provide detailed summaries with examples

### Technology Stack Requirements

**Required CLI Tools:**
- `flux` CLI v2.7.5+ installed
- `kubectl` configured with both cluster contexts
- `task` (go-task/task) v3.x installed

**Kubernetes Context Requirements:**
- Context `infra` for infra cluster
- Context `apps` for apps cluster
- Both contexts must be configured in ~/.kube/config

### Verification Commands

```bash
# Verify task is installed
task --version

# List available tasks
task --list

# Test reconcile
task flux:reconcile APP=gatus CLUSTER=infra

# Test suspend
task flux:suspend APP=gatus CLUSTER=infra

# Test resume
task flux:resume APP=gatus CLUSTER=infra

# Test logs
task flux:logs CLUSTER=infra

# Test status
task flux:status CLUSTER=infra

# Verify Flux health
task flux:check CLUSTER=infra
task flux:check CLUSTER=apps
```

### Critical Implementation Rules

1. **Taskfile Version:**
   - Use version: "3" (current stable)
   - Follow go-task/task documentation

2. **Variable Handling:**
   - Use `{{.VAR}}` syntax for variables
   - Provide sensible defaults with `| default`
   - Use `requires.vars` for mandatory inputs

3. **Multi-Cluster Support:**
   - ALWAYS include CLUSTER variable
   - Default to `infra` cluster
   - Use `--context={{.CLUSTER}}` for all kubectl/flux commands

4. **Preconditions:**
   - Validate cluster context exists
   - Validate required CLI tools installed
   - Provide helpful error messages

5. **Documentation:**
   - Use `desc` for short one-liner
   - Use `summary` for detailed usage with examples
   - Include variable documentation in summary

### Project Structure Notes

- **Location:** `.taskfiles/flux/Taskfile.yaml`
- **Entry Point:** Root `Taskfile.yaml` includes all taskfiles
- **Namespacing:** Tasks prefixed with `flux:` (e.g., `flux:reconcile`)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.1: Create Flux Operational Taskfiles]
- [Source: _bmad-output/planning-artifacts/architecture.md#Taskfile Automation (Unified Operations)]
- [Source: docs/project-context.md#Taskfile Operations]
- [Flux CD CLI - flux reconcile](https://fluxcd.io/flux/cmd/flux_reconcile/)
- [Flux CD CLI - flux suspend](https://fluxcd.io/flux/cmd/flux_suspend/)
- [Flux CD CLI - flux resume](https://fluxcd.io/flux/cmd/flux_resume/)
- [go-task/task Documentation](https://taskfile.dev/)

### Validation Checklist

Before marking complete, verify:
- [ ] `.taskfiles/flux/Taskfile.yaml` created with all required tasks
- [ ] Root `Taskfile.yaml` includes flux taskfile
- [ ] `task flux:reconcile APP=test CLUSTER=infra` works
- [ ] `task flux:suspend APP=test CLUSTER=infra` works
- [ ] `task flux:resume APP=test CLUSTER=infra` works
- [ ] `task flux:logs CLUSTER=infra` streams logs
- [ ] `task flux:events CLUSTER=infra` shows events
- [ ] `task flux:diff APP=test CLUSTER=infra` works
- [ ] All tasks have desc and summary
- [ ] Preconditions validate context exists

### Git Commit Message Format

```
feat(flux): create operational taskfiles for Flux management

- Add .taskfiles/flux/Taskfile.yaml with core tasks
- Add flux:reconcile, suspend, resume, logs, events, diff tasks
- Add flux:status, check, tree, trace helper tasks
- Support CLUSTER and APP variables for multi-cluster ops
- FR4: View Flux reconciliation status
- FR5: Trigger manual reconciliation
- FR6: Suspend/resume reconciliation
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

