# Story 7.3: Create VolSync Operational Taskfiles

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **platform operator**,
I want **taskfile commands for backup and restore operations**,
So that **I can manage VolSync backups efficiently without complex kubectl commands**.

## Acceptance Criteria

1. **Given** VolSync is operational with backups running
   **When** `.taskfiles/volsync/Taskfile.yaml` is created
   **Then** the file contains all required task definitions with proper structure

2. **Given** taskfile exists
   **When** `task volsync:snapshot APP=<app> CLUSTER=<cluster>` is executed
   **Then** an immediate backup is triggered for the specified app's ReplicationSource

3. **Given** backups exist in R2
   **When** `task volsync:restore APP=<app> CLUSTER=<cluster>` is executed
   **Then** a ReplicationDestination is created to restore the PVC from the latest snapshot

4. **Given** backups exist in R2
   **When** `task volsync:restore APP=<app> CLUSTER=<cluster> SNAPSHOT=<id>` is executed
   **Then** a ReplicationDestination is created to restore from the specific snapshot

5. **Given** a Restic repository is locked (stale lock)
   **When** `task volsync:unlock APP=<app> CLUSTER=<cluster>` is executed
   **Then** the ReplicationSource unlock field is updated to trigger `restic unlock`

6. **Given** backups exist
   **When** `task volsync:list APP=<app> CLUSTER=<cluster>` is executed
   **Then** available snapshots are listed with timestamps using an ephemeral debug pod

7. **Given** ReplicationSources exist
   **When** `task volsync:status CLUSTER=<cluster>` is executed
   **Then** status of all ReplicationSources in the cluster is displayed

8. **Given** all tasks are defined
   **When** root `Taskfile.yaml` is updated
   **Then** volsync tasks are included and accessible via `task --list`

## Tasks / Subtasks

- [ ] Task 1: Create VolSync Taskfile Structure (AC: #1, #8)
  - [ ] 1.1 Create `.taskfiles/volsync/Taskfile.yaml` with proper header and variables
  - [ ] 1.2 Define required variables: APP, CLUSTER, NAMESPACE, SNAPSHOT (optional)
  - [ ] 1.3 Set default CLUSTER to `infra` if not specified
  - [ ] 1.4 Create root `Taskfile.yaml` if not exists, including volsync tasks

- [ ] Task 2: Implement volsync:snapshot Task (AC: #2)
  - [ ] 2.1 Create task that patches ReplicationSource to trigger immediate backup
  - [ ] 2.2 Use `kubectl patch` with annotation change to force reconciliation
  - [ ] 2.3 Wait for sync to start and report status
  - [ ] 2.4 Add description and required variables

- [ ] Task 3: Implement volsync:restore Task (AC: #3, #4)
  - [ ] 3.1 Create task that generates ReplicationDestination manifest
  - [ ] 3.2 Support optional SNAPSHOT variable for specific snapshot restore
  - [ ] 3.3 Use `previous` field when SNAPSHOT is an integer offset
  - [ ] 3.4 Apply ReplicationDestination and wait for completion
  - [ ] 3.5 Clean up ReplicationDestination after restore

- [ ] Task 4: Implement volsync:unlock Task (AC: #5)
  - [ ] 4.1 Create task that patches ReplicationSource with unlock trigger
  - [ ] 4.2 Set `spec.restic.unlock` to unique timestamp string
  - [ ] 4.3 Wait for unlock to complete (check status.restic.lastUnlocked)
  - [ ] 4.4 Report unlock success or failure

- [ ] Task 5: Implement volsync:list Task (AC: #6)
  - [ ] 5.1 Create task that spawns ephemeral debug pod with restic CLI
  - [ ] 5.2 Mount volsync-r2-secret into the pod for credentials
  - [ ] 5.3 Run `restic snapshots` to list available backups
  - [ ] 5.4 Parse and display snapshot list with timestamps
  - [ ] 5.5 Clean up debug pod after execution

- [ ] Task 6: Implement volsync:status Task (AC: #7)
  - [ ] 6.1 Create task that lists all ReplicationSources with status
  - [ ] 6.2 Display last sync time, next scheduled sync, and latest snapshot
  - [ ] 6.3 Highlight any ReplicationSources in error state
  - [ ] 6.4 Support namespace filtering with NAMESPACE variable

- [ ] Task 7: Integration and Testing (AC: #8)
  - [ ] 7.1 Verify `task --list` shows all volsync tasks
  - [ ] 7.2 Test each task with a sample application
  - [ ] 7.3 Document usage examples in taskfile comments
  - [ ] 7.4 Update docs/runbooks with taskfile references

## Dev Notes

### Architecture Compliance Requirements

**App Location:**
- Taskfile: `.taskfiles/volsync/Taskfile.yaml`
- Root include: `Taskfile.yaml` (at repository root)

**Directory Structure:**
```
k8s-ops/
├── Taskfile.yaml                    # Root taskfile with includes
└── .taskfiles/
    └── volsync/
        └── Taskfile.yaml            # VolSync-specific tasks
```

### Taskfile Variables Pattern

```yaml
version: '3'

vars:
  CLUSTER: '{{.CLUSTER | default "infra"}}'
  NAMESPACE: '{{.NAMESPACE | default ""}}'
  APP: '{{.APP}}'
  KUBECONFIG: '{{.ROOT_DIR}}/kubeconfig-{{.CLUSTER}}'

env:
  KUBECONFIG: '{{.KUBECONFIG}}'
```

### Task Implementation Patterns

**volsync:snapshot Task:**
```yaml
volsync:snapshot:
  desc: Trigger immediate VolSync backup for an application
  summary: |
    Triggers an immediate backup by updating the ReplicationSource annotation.
    Usage: task volsync:snapshot APP=odoo CLUSTER=apps
  requires:
    vars: [APP]
  cmds:
    - |
      NS=$(kubectl get replicationsource -A -o jsonpath='{range .items[?(@.metadata.name=="{{.APP}}-backup")]}{.metadata.namespace}{end}')
      if [ -z "$NS" ]; then
        echo "Error: ReplicationSource {{.APP}}-backup not found"
        exit 1
      fi
      kubectl patch replicationsource {{.APP}}-backup -n "$NS" \
        --type merge \
        -p '{"spec":{"trigger":{"manual":"snapshot-{{.TIMESTAMP}}"}}}'
      echo "Triggered snapshot for {{.APP}}-backup in namespace $NS"
```

**volsync:restore Task:**
```yaml
volsync:restore:
  desc: Restore PVC from VolSync backup
  summary: |
    Creates a ReplicationDestination to restore data from R2.
    Optionally specify SNAPSHOT for specific version (integer offset).
    Usage: task volsync:restore APP=odoo CLUSTER=apps [SNAPSHOT=2]
  requires:
    vars: [APP]
  vars:
    TIMESTAMP:
      sh: date +%Y%m%d%H%M%S
    PREVIOUS: '{{if .SNAPSHOT}}{{.SNAPSHOT}}{{else}}0{{end}}'
  cmds:
    - |
      NS=$(kubectl get replicationsource -A -o jsonpath='{range .items[?(@.metadata.name=="{{.APP}}-backup")]}{.metadata.namespace}{end}')
      cat <<EOF | kubectl apply -f -
      apiVersion: volsync.backube/v1alpha1
      kind: ReplicationDestination
      metadata:
        name: {{.APP}}-restore-{{.TIMESTAMP}}
        namespace: $NS
      spec:
        trigger:
          manual: restore-{{.TIMESTAMP}}
        restic:
          repository: volsync-r2-secret
          destinationPVC: {{.APP}}-data
          copyMethod: Direct
          previous: {{.PREVIOUS}}
      EOF
    - kubectl wait --for=condition=available replicationdestination/{{.APP}}-restore-{{.TIMESTAMP}} -n "$NS" --timeout=30m
    - echo "Restore completed for {{.APP}}"
```

**volsync:unlock Task:**
```yaml
volsync:unlock:
  desc: Unlock stuck Restic repository
  summary: |
    Clears stale repository locks by triggering restic unlock.
    Usage: task volsync:unlock APP=odoo CLUSTER=apps
  requires:
    vars: [APP]
  vars:
    TIMESTAMP:
      sh: date +%Y%m%d%H%M%S
  cmds:
    - |
      NS=$(kubectl get replicationsource -A -o jsonpath='{range .items[?(@.metadata.name=="{{.APP}}-backup")]}{.metadata.namespace}{end}')
      kubectl patch replicationsource {{.APP}}-backup -n "$NS" \
        --type merge \
        -p '{"spec":{"restic":{"unlock":"unlock-{{.TIMESTAMP}}"}}}'
      echo "Triggered unlock for {{.APP}}-backup"
      echo "Check status.restic.lastUnlocked for completion"
```

**volsync:list Task:**
```yaml
volsync:list:
  desc: List available VolSync snapshots for an application
  summary: |
    Spawns an ephemeral pod to run restic snapshots against the repository.
    Usage: task volsync:list APP=odoo CLUSTER=apps
  requires:
    vars: [APP]
  cmds:
    - |
      NS=$(kubectl get replicationsource -A -o jsonpath='{range .items[?(@.metadata.name=="{{.APP}}-backup")]}{.metadata.namespace}{end}')
      kubectl run volsync-list-{{.APP}}-$(date +%s) \
        --rm -it --restart=Never \
        --namespace="$NS" \
        --image=restic/restic:latest \
        --overrides='{
          "spec": {
            "containers": [{
              "name": "restic",
              "image": "restic/restic:latest",
              "command": ["restic", "snapshots", "--json"],
              "envFrom": [{"secretRef": {"name": "volsync-r2-secret"}}],
              "env": [
                {"name": "RESTIC_REPOSITORY", "value": "s3:https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com/${VOLSYNC_R2_BUCKET}/{{.APP}}"}
              ]
            }]
          }
        }' -- /bin/sh -c "restic snapshots"
```

**volsync:status Task:**
```yaml
volsync:status:
  desc: Show status of all VolSync ReplicationSources
  summary: |
    Lists all ReplicationSources with their sync status.
    Usage: task volsync:status CLUSTER=apps [NAMESPACE=business]
  cmds:
    - |
      if [ -n "{{.NAMESPACE}}" ]; then
        kubectl get replicationsource -n {{.NAMESPACE}} -o wide
      else
        kubectl get replicationsource -A -o wide
      fi
    - echo ""
    - echo "Last sync times:"
    - |
      kubectl get replicationsource {{if .NAMESPACE}}-n {{.NAMESPACE}}{{else}}-A{{end}} \
        -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name}: {.status.lastSyncTime}{"\n"}{end}'
```

### Root Taskfile Integration

```yaml
# Taskfile.yaml (root)
version: '3'

vars:
  ROOT_DIR:
    sh: git rev-parse --show-toplevel

includes:
  volsync:
    taskfile: .taskfiles/volsync/Taskfile.yaml
    dir: '{{.ROOT_DIR}}'
  # Future taskfiles:
  # talos:
  #   taskfile: .taskfiles/talos/Taskfile.yaml
  # kubernetes:
  #   taskfile: .taskfiles/kubernetes/Taskfile.yaml
  # flux:
  #   taskfile: .taskfiles/flux/Taskfile.yaml
```

### Restic Repository Access Pattern

For `volsync:list`, the ephemeral pod needs:

1. **Secret Reference:** `volsync-r2-secret` containing:
   - `RESTIC_REPOSITORY`: S3 URL to R2 bucket
   - `RESTIC_PASSWORD`: Repository encryption key
   - `AWS_ACCESS_KEY_ID`: R2 access key
   - `AWS_SECRET_ACCESS_KEY`: R2 secret key

2. **Restic Image:** `restic/restic:latest` (official image)

3. **Commands:**
   - `restic snapshots` - List all snapshots
   - `restic snapshots --json` - JSON output for parsing
   - `restic stats` - Repository statistics
   - `restic unlock` - Clear stale locks

### Cloudflare R2 Configuration

**R2 Endpoint:** `https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`
**Repository Path:** `s3:https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com/${VOLSYNC_R2_BUCKET}/${APP}`

### Dependencies

- **Hard Dependencies:**
  - Story 7.1 (VolSync deployment) - VolSync operator and credentials must exist
  - `kubectl` - Kubernetes CLI
  - `go-task` - Taskfile runner (https://taskfile.dev)

- **Soft Dependencies:**
  - Story 7.2 (CNPG Barman) - Not required but recommended for complete backup story

### Previous Story Intelligence (7.2 - CNPG Barman Backups)

From Story 7.2 implementation patterns:
- R2 endpoint configuration verified
- ExternalSecret pattern for credentials (`external-secrets.io/v1`)
- Same Cloudflare R2 bucket infrastructure
- Similar taskfile command patterns for operators

**Key Learnings to Apply:**
- Use consistent variable naming (APP, CLUSTER, NAMESPACE)
- Provide clear task descriptions with usage examples
- Handle namespace discovery dynamically when possible
- Include error handling for missing resources

### Previous Story Intelligence (7.1 - VolSync Deployment)

From Story 7.1:
- ReplicationSource template uses `${APP}-backup` naming
- Secret name: `volsync-r2-secret`
- PVC naming: `${APP}-data`
- Schedule: `0 */8 * * *`
- Retain: hourly: 24, daily: 7
- Component path: `kubernetes/components/volsync/r2/`

### Project Structure Notes

- Alignment with unified project structure: Taskfiles in `.taskfiles/` directory
- Follow existing Taskfile patterns from architecture document
- Cluster-aware commands with CLUSTER variable
- Consistent with other operational taskfiles (talos, kubernetes, flux)

### Security Considerations

- Taskfiles only use existing secrets (no credential handling)
- Ephemeral pods for restic commands auto-clean
- No credentials stored in taskfile definitions
- All sensitive operations via kubectl with RBAC

### Testing Considerations

**Manual Test Procedure:**
1. Run `task --list` to verify all tasks appear
2. Test `task volsync:status CLUSTER=infra` - should list ReplicationSources
3. Test `task volsync:list APP=<test-app>` - should list snapshots
4. Test `task volsync:snapshot APP=<test-app>` - should trigger backup
5. Test `task volsync:restore APP=<test-app>` - should create ReplicationDestination
6. Test `task volsync:unlock APP=<test-app>` - should clear locks (if any)

**Integration with Story 7.4:**
- DR runbook (Story 7.4) will reference these taskfile commands
- `tests/smoke/dr-volsync-restore.sh` will use `task volsync:restore`

### NFR Compliance

| NFR | Requirement | Implementation |
|-----|-------------|----------------|
| NFR29 | Taskfile coverage | Common operations available via unified .taskfiles |
| NFR20 | Cluster recovery < 2 hours | Taskfiles enable quick restore operations |
| NFR23 | Pattern consistency | Follows established taskfile conventions |

### Error Handling Patterns

```yaml
# Check for missing ReplicationSource
cmds:
  - |
    NS=$(kubectl get replicationsource -A -o jsonpath='{range .items[?(@.metadata.name=="{{.APP}}-backup")]}{.metadata.namespace}{end}')
    if [ -z "$NS" ]; then
      echo "Error: ReplicationSource {{.APP}}-backup not found in any namespace"
      echo "Available ReplicationSources:"
      kubectl get replicationsource -A
      exit 1
    fi
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 7.3] - Epic and story requirements
- [Source: _bmad-output/planning-artifacts/architecture.md#Taskfile Automation] - Taskfile automation patterns
- [Source: docs/project-context.md#Taskfile Operations] - Taskfile operation categories
- [Source: _bmad-output/implementation-artifacts/7-1-deploy-volsync-for-pvc-backups.md] - VolSync patterns from Story 7.1
- [Source: _bmad-output/implementation-artifacts/7-2-configure-cnpg-barman-backups-to-r2.md] - R2 configuration patterns
- [VolSync Documentation](https://volsync.readthedocs.io/en/stable/usage/restic/index.html) - Restic backup configuration
- [Restic Repository Operations](https://restic.readthedocs.io/en/latest/045_working_with_repos.html) - Restic CLI reference
- [Taskfile Documentation](https://taskfile.dev/) - go-task reference

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

