# Story 4.4: Create Kubernetes Operational Taskfiles

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform operator,
I want unified taskfiles for common Kubernetes operations,
so that I can manage workloads efficiently across clusters.

## Acceptance Criteria

1. **AC1**: `.taskfiles/kubernetes/Taskfile.yaml` exists and is properly included in root `Taskfile.yaml`

2. **AC2**: `k8s:sync-secrets` task is implemented:
   - Forces External Secrets sync for a specific app or namespace
   - Accepts `APP` and `CLUSTER` variables
   - Uses `kubectl annotate externalsecret` to trigger refresh

3. **AC3**: `k8s:hr-restart` task is implemented:
   - Restarts a HelmRelease by suspending and resuming
   - Accepts `APP`, `NAMESPACE`, and `CLUSTER` variables
   - Verifies HelmRelease exists before operation

4. **AC4**: `k8s:cleanse-pods` task is implemented:
   - Deletes pods in failed, evicted, or error states
   - Accepts `CLUSTER` variable
   - Can target specific namespace via optional `NAMESPACE` variable

5. **AC5**: `k8s:browse-pvc` task is implemented:
   - Creates ephemeral pod to browse PVC contents
   - Accepts `PVC`, `NAMESPACE`, and `CLUSTER` variables
   - Uses alpine or busybox image for minimal footprint
   - Mounts PVC as read-only by default

6. **AC6**: `k8s:exec` task is implemented:
   - Execs into a pod interactively
   - Accepts `POD`, `NAMESPACE`, `CLUSTER`, and optional `CONTAINER` variables
   - Defaults to `/bin/sh` shell

7. **AC7**: `k8s:logs` task is implemented:
   - Streams pod logs with follow capability
   - Accepts `POD`, `NAMESPACE`, `CLUSTER`, and optional `CONTAINER` variables
   - Supports `--since` and `--tail` options

8. **AC8**: All tasks are cluster-aware and use proper kubeconfig contexts:
   - Tasks accept `CLUSTER` variable (default: `infra`)
   - Uses `--context ${CLUSTER}` for all kubectl commands
   - Validates cluster context exists before operations

9. **AC9**: `task k8s:hr-restart APP=gatus CLUSTER=infra` successfully restarts the Gatus HelmRelease

## Tasks / Subtasks

- [ ] Task 1: Create Taskfile structure (AC: #1)
  - [ ] Subtask 1.1: Create `.taskfiles/kubernetes/Taskfile.yaml` with proper header
  - [ ] Subtask 1.2: Add include reference in root `Taskfile.yaml`
  - [ ] Subtask 1.3: Define common variables (CLUSTER default, kubeconfig handling)

- [ ] Task 2: Implement k8s:sync-secrets task (AC: #2)
  - [ ] Subtask 2.1: Create task with APP and CLUSTER variables
  - [ ] Subtask 2.2: Use `kubectl annotate externalsecret --overwrite` pattern
  - [ ] Subtask 2.3: Add force refresh annotation `force-sync=timestamp`
  - [ ] Subtask 2.4: Support namespace-wide sync when APP not specified

- [ ] Task 3: Implement k8s:hr-restart task (AC: #3)
  - [ ] Subtask 3.1: Create task with APP, NAMESPACE, CLUSTER variables
  - [ ] Subtask 3.2: Verify HelmRelease exists before suspend/resume
  - [ ] Subtask 3.3: Use `flux suspend hr` then `flux resume hr` pattern
  - [ ] Subtask 3.4: Add status check after restart

- [ ] Task 4: Implement k8s:cleanse-pods task (AC: #4)
  - [ ] Subtask 4.1: Create task targeting Failed/Evicted/Error pods
  - [ ] Subtask 4.2: Use field-selector for pod status filtering
  - [ ] Subtask 4.3: Support optional NAMESPACE targeting
  - [ ] Subtask 4.4: Add dry-run mode for safety

- [ ] Task 5: Implement k8s:browse-pvc task (AC: #5)
  - [ ] Subtask 5.1: Create task with PVC, NAMESPACE, CLUSTER variables
  - [ ] Subtask 5.2: Generate ephemeral pod YAML with PVC mount
  - [ ] Subtask 5.3: Use alpine image with TTY and interactive shell
  - [ ] Subtask 5.4: Auto-cleanup pod on exit
  - [ ] Subtask 5.5: Support read-only or read-write mode via optional flag

- [ ] Task 6: Implement k8s:exec task (AC: #6)
  - [ ] Subtask 6.1: Create task with POD, NAMESPACE, CLUSTER variables
  - [ ] Subtask 6.2: Support optional CONTAINER for multi-container pods
  - [ ] Subtask 6.3: Use `kubectl exec -it` with proper TTY handling
  - [ ] Subtask 6.4: Default to /bin/sh shell

- [ ] Task 7: Implement k8s:logs task (AC: #7)
  - [ ] Subtask 7.1: Create task with POD, NAMESPACE, CLUSTER variables
  - [ ] Subtask 7.2: Support CONTAINER variable for multi-container pods
  - [ ] Subtask 7.3: Add FOLLOW variable (default: true)
  - [ ] Subtask 7.4: Add SINCE and TAIL variables with sensible defaults

- [ ] Task 8: Validate cluster-awareness (AC: #8, #9)
  - [ ] Subtask 8.1: Verify CLUSTER variable defaults to "infra"
  - [ ] Subtask 8.2: Test each task with explicit CLUSTER=apps
  - [ ] Subtask 8.3: Verify context validation before operations
  - [ ] Subtask 8.4: Test `task k8s:hr-restart APP=gatus CLUSTER=infra`

## Dev Notes

### Architecture Context

**Technology Stack:**
- Task (go-task) - https://taskfile.dev/
- kubectl CLI with kubeconfig contexts
- Flux CLI for HelmRelease operations
- External Secrets Operator v1.0.0

**Purpose of This Story:**
Create unified taskfiles that enable efficient Kubernetes operations across both clusters without memorizing complex kubectl commands. These tasks complement the existing:
- `.taskfiles/flux/Taskfile.yaml` - Flux-specific operations (Story 3.1)
- `.taskfiles/talos/Taskfile.yaml` - Talos node operations (Story 1.5)
- `.taskfiles/bootstrap/Taskfile.yaml` - Cluster bootstrap operations

### Previous Story Context (Stories 3.1, 1.5)

**Story 3.1 - Flux Taskfiles Learnings:**
- Pattern: Tasks accept `APP` and `CLUSTER` variables
- CLUSTER defaults to `infra`
- Uses `--context ${CLUSTER}` for kubectl commands
- Includes verification steps before destructive operations

**Story 1.5 - Talos Taskfiles Learnings:**
- Consistent variable naming: `CLUSTER`, `NODE`, `APP`
- Confirmation prompts for destructive operations
- Dry-run modes for safety
- Status checks after operations

### Implementation Patterns

**Taskfile Header Pattern (REQUIRED):**
```yaml
# yaml-language-server: $schema=https://taskfile.dev/schema.json
version: "3"

# Kubernetes operational tasks for workload management
# Usage: task k8s:<task> CLUSTER=<infra|apps> [other vars]

vars:
  CLUSTER: '{{.CLUSTER | default "infra"}}'
  KUBECONFIG: '{{.KUBECONFIG | default "~/.kube/config"}}'

tasks:
```

**Root Taskfile.yaml Include Pattern (REQUIRED):**
```yaml
includes:
  kubernetes:
    taskfile: .taskfiles/kubernetes/Taskfile.yaml
    aliases: ["k8s"]
```

**Cluster-Aware Task Pattern:**
```yaml
tasks:
  hr-restart:
    desc: Restart a HelmRelease by suspend/resume
    summary: |
      Restarts a HelmRelease by suspending and resuming reconciliation.
      Variables:
        APP: HelmRelease name (required)
        NAMESPACE: Target namespace (default: flux-system)
        CLUSTER: Target cluster (default: infra)
    vars:
      NAMESPACE: '{{.NAMESPACE | default "flux-system"}}'
    cmds:
      - flux --context {{.CLUSTER}} suspend hr {{.APP}} -n {{.NAMESPACE}}
      - flux --context {{.CLUSTER}} resume hr {{.APP}} -n {{.NAMESPACE}}
      - kubectl --context {{.CLUSTER}} get hr {{.APP}} -n {{.NAMESPACE}}
    requires:
      vars: [APP]
```

**ExternalSecret Sync Pattern:**
```yaml
  sync-secrets:
    desc: Force External Secrets sync
    vars:
      NAMESPACE: '{{.NAMESPACE | default "default"}}'
    cmds:
      - |
        kubectl --context {{.CLUSTER}} annotate externalsecret -n {{.NAMESPACE}} \
          {{if .APP}}{{.APP}}{{else}}-l app.kubernetes.io/managed-by=external-secrets{{end}} \
          force-sync=$(date +%s) --overwrite
```

**Pod Cleanup Pattern:**
```yaml
  cleanse-pods:
    desc: Delete failed/evicted pods
    vars:
      NAMESPACE: '{{.NAMESPACE | default ""}}'
    cmds:
      - |
        kubectl --context {{.CLUSTER}} delete pods \
          {{if .NAMESPACE}}-n {{.NAMESPACE}}{{else}}-A{{end}} \
          --field-selector=status.phase==Failed
      - |
        kubectl --context {{.CLUSTER}} delete pods \
          {{if .NAMESPACE}}-n {{.NAMESPACE}}{{else}}-A{{end}} \
          --field-selector=status.phase==Evicted 2>/dev/null || true
```

**PVC Browser Pattern:**
```yaml
  browse-pvc:
    desc: Browse PVC contents via ephemeral pod
    vars:
      READONLY: '{{.READONLY | default "true"}}'
    cmds:
      - |
        kubectl --context {{.CLUSTER}} run pvc-browser-{{.PVC}} \
          -n {{.NAMESPACE}} --rm -it --restart=Never \
          --image=alpine:latest \
          --overrides='
          {
            "spec": {
              "containers": [{
                "name": "pvc-browser",
                "image": "alpine:latest",
                "command": ["/bin/sh"],
                "stdin": true,
                "tty": true,
                "volumeMounts": [{
                  "name": "data",
                  "mountPath": "/data",
                  "readOnly": {{.READONLY}}
                }]
              }],
              "volumes": [{
                "name": "data",
                "persistentVolumeClaim": {"claimName": "{{.PVC}}"}
              }]
            }
          }'
    requires:
      vars: [PVC, NAMESPACE]
```

**Exec Into Pod Pattern:**
```yaml
  exec:
    desc: Exec into a pod
    vars:
      SHELL: '{{.SHELL | default "/bin/sh"}}'
    cmds:
      - |
        kubectl --context {{.CLUSTER}} exec -it -n {{.NAMESPACE}} {{.POD}} \
          {{if .CONTAINER}}-c {{.CONTAINER}}{{end}} -- {{.SHELL}}
    requires:
      vars: [POD, NAMESPACE]
```

**Logs Streaming Pattern:**
```yaml
  logs:
    desc: Stream pod logs
    vars:
      FOLLOW: '{{.FOLLOW | default "true"}}'
      TAIL: '{{.TAIL | default "100"}}'
      SINCE: '{{.SINCE | default "1h"}}'
    cmds:
      - |
        kubectl --context {{.CLUSTER}} logs -n {{.NAMESPACE}} {{.POD}} \
          {{if .CONTAINER}}-c {{.CONTAINER}}{{end}} \
          {{if eq .FOLLOW "true"}}-f{{end}} \
          --tail={{.TAIL}} --since={{.SINCE}}
    requires:
      vars: [POD, NAMESPACE]
```

### Critical Implementation Rules

**From project-context.md - Taskfile Operations:**
| Task Category | Key Operations |
|---------------|----------------|
| `bootstrap:*` | Talos bootstrap, K8s apps bootstrap |
| `talos:*` | apply-node, upgrade-node, upgrade-k8s |
| `kubernetes:*` | sync-secrets, hr-restart, cleanse-pods |
| `volsync:*` | snapshot, restore, unlock |
| `op:*` | push/pull kubeconfig to 1Password |

**From architecture.md - Taskfile Automation:**
| Task Category | Key Operations |
|---------------|----------------|
| `kubernetes:*` | sync-secrets, hr-restart, cleanse-pods, browse-pvc |

**Variable Naming Conventions:**
- `CLUSTER` - Target cluster (`infra` or `apps`)
- `APP` - Application/HelmRelease name
- `NAMESPACE` - Kubernetes namespace
- `POD` - Pod name
- `PVC` - PersistentVolumeClaim name
- `CONTAINER` - Container name (for multi-container pods)

**Context Handling:**
- Both clusters share kubeconfig with named contexts: `infra` and `apps`
- All kubectl/flux commands MUST include `--context {{.CLUSTER}}`
- Default CLUSTER is `infra`

### Project Structure Notes

- **Location**: `.taskfiles/kubernetes/Taskfile.yaml`
- **Alias**: `k8s` (so `task k8s:logs` works)
- **Integration**: Included in root `Taskfile.yaml`
- **Dependencies**: kubectl, flux CLI, kubeconfig with contexts

### Existing Taskfile Structure

```
.taskfiles/
├── bootstrap/Taskfile.yaml     # bootstrap:infra, bootstrap:apps
├── flux/Taskfile.yaml          # flux:reconcile, flux:suspend, flux:resume
├── talos/Taskfile.yaml         # talos:apply-node, talos:upgrade-node
├── volsync/Taskfile.yaml       # volsync:snapshot, volsync:restore
├── dr/Taskfile.yaml            # dr:verify-backups, dr:test-restore
├── op/Taskfile.yaml            # op:push, op:pull kubeconfig
└── kubernetes/Taskfile.yaml    # NEW: This story
```

### Multi-Cluster Context

| Cluster | Context Name | API Endpoint |
|---------|--------------|--------------|
| infra | `infra` | https://10.25.11.10:6443 |
| apps | `apps` | https://10.25.13.10:6443 |

All tasks should work with either cluster by passing `CLUSTER=infra` or `CLUSTER=apps`.

### Task Descriptions

Brief task descriptions for the help output:

| Task | Description |
|------|-------------|
| `k8s:sync-secrets` | Force External Secrets sync |
| `k8s:hr-restart` | Restart a HelmRelease |
| `k8s:cleanse-pods` | Delete failed/evicted pods |
| `k8s:browse-pvc` | Browse PVC contents via ephemeral pod |
| `k8s:exec` | Exec into a pod |
| `k8s:logs` | Stream pod logs |

### Safety Considerations

1. **No destructive defaults**: Tasks like `cleanse-pods` only delete non-running pods
2. **Confirmation prompts**: Consider adding for cluster-wide operations
3. **Dry-run modes**: Add `--dry-run=client` option where applicable
4. **Verification steps**: Include status checks after operations
5. **Error handling**: Use `|| true` for optional cleanup commands

### Testing Commands

```bash
# List all kubernetes tasks
task --list | grep k8s

# Test sync-secrets
task k8s:sync-secrets APP=gatus NAMESPACE=observability CLUSTER=infra

# Test hr-restart
task k8s:hr-restart APP=gatus NAMESPACE=observability CLUSTER=infra

# Test cleanse-pods (dry-run first if implemented)
task k8s:cleanse-pods CLUSTER=infra

# Test browse-pvc
task k8s:browse-pvc PVC=gatus-data NAMESPACE=observability CLUSTER=infra

# Test exec
task k8s:exec POD=gatus-xxx NAMESPACE=observability CLUSTER=infra

# Test logs
task k8s:logs POD=gatus-xxx NAMESPACE=observability CLUSTER=infra
```

### Anti-Patterns to Avoid

1. **DO NOT** hardcode cluster contexts - always use `--context {{.CLUSTER}}`
2. **DO NOT** use `kubectl config use-context` - use `--context` flag instead
3. **DO NOT** assume namespace - always require or default explicitly
4. **DO NOT** delete pods without status filtering
5. **DO NOT** skip verification after operations

### References

- [Source: docs/project-context.md#Taskfile Operations] - Task categories
- [Source: _bmad-output/planning-artifacts/architecture.md#Taskfile Automation] - Task requirements
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.4] - Original acceptance criteria
- [Source: _bmad-output/implementation-artifacts/3-1-create-flux-operational-taskfiles.md] - Flux task patterns
- [Source: _bmad-output/implementation-artifacts/1-5-create-operational-taskfiles-for-talos.md] - Talos task patterns
- [Source: _bmad-output/implementation-artifacts/4-3-create-reference-application-deployment.md] - Reference app for testing

### External Documentation

- [Taskfile Documentation](https://taskfile.dev/)
- [Taskfile Schema](https://taskfile.dev/schema.json)
- [kubectl Reference](https://kubernetes.io/docs/reference/kubectl/)
- [Flux CLI Reference](https://fluxcd.io/flux/cmd/)
- [External Secrets Operator](https://external-secrets.io/)

### Verification Commands

```bash
# Validate taskfile syntax
task --list-all

# Verify kubernetes tasks are available
task kubernetes:hr-restart --help 2>/dev/null || task k8s:hr-restart --help

# Test with actual workload
task k8s:hr-restart APP=gatus CLUSTER=infra

# Verify HR status after restart
kubectl --context infra get hr -n observability gatus
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
