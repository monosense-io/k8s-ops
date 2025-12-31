# Story 4.5: Create Runbooks for Major Components

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform operator,
I want runbooks documenting operational procedures,
so that I can troubleshoot and recover from issues efficiently.

## Acceptance Criteria

1. **AC1**: `docs/runbooks/bootstrap.md` exists with full cluster bootstrap procedure:
   - Prerequisites checklist (1Password, R2, SOPS, Talos nodes)
   - Step-by-step `task bootstrap:infra` and `task bootstrap:apps` execution
   - Verification commands after each phase
   - Troubleshooting common bootstrap failures

2. **AC2**: `docs/runbooks/disaster-recovery.md` exists with DR procedures:
   - Full cluster rebuild from Git + VolSync + 1Password
   - CNPG point-in-time recovery procedure
   - VolSync PVC restore procedure
   - Estimated recovery times per data size
   - Recovery verification steps

3. **AC3**: `docs/runbooks/cnpg-restore.md` exists with CNPG backup/restore:
   - On-demand backup creation (`kubectl cnpg backup`)
   - Point-in-time recovery (PITR) procedure
   - Full cluster recovery from Barman
   - Database connection string patterns
   - Backup verification commands

4. **AC4**: `docs/runbooks/cluster-upgrade.md` exists with upgrade procedures:
   - Talos node upgrade with rolling strategy
   - Kubernetes version upgrade
   - Pre-upgrade checklist and verification
   - Rollback procedures

5. **AC5**: `docs/runbooks/rook-ceph.md` exists with Ceph operations:
   - Ceph health check commands
   - OSD troubleshooting
   - Pool expansion procedure
   - PG recovery and maintenance
   - Common Ceph issues and resolutions

6. **AC6**: `docs/runbooks/cilium.md` exists with network operations:
   - Network policy debugging
   - Connectivity test execution and interpretation
   - BGP session verification
   - Hubble usage for traffic analysis
   - Policy bypass for debugging

7. **AC7**: `docs/runbooks/flux.md` exists with GitOps operations:
   - Reconciliation troubleshooting
   - HelmRelease debugging
   - Kustomization debugging
   - Suspend/resume procedures
   - Force reconciliation

8. **AC8**: Each runbook includes:
   - Symptoms section (when to use this runbook)
   - Diagnosis steps with specific commands
   - Resolution procedures with verification
   - References to related taskfile commands

9. **AC9**: `docs/index.md` includes links to all runbooks with brief descriptions

## Tasks / Subtasks

- [ ] Task 1: Create runbook directory and index (AC: #9)
  - [ ] Subtask 1.1: Create `docs/runbooks/` directory if not exists
  - [ ] Subtask 1.2: Update `docs/index.md` with runbooks section and links

- [ ] Task 2: Create bootstrap.md runbook (AC: #1, #8)
  - [ ] Subtask 2.1: Document prerequisites (1Password vault, R2 buckets, AGE key, Talos nodes)
  - [ ] Subtask 2.2: Document `task bootstrap:infra` step-by-step with verification
  - [ ] Subtask 2.3: Document `task bootstrap:apps` step-by-step with verification
  - [ ] Subtask 2.4: Add troubleshooting section for common failures
  - [ ] Subtask 2.5: Include taskfile command references

- [ ] Task 3: Create disaster-recovery.md runbook (AC: #2, #8)
  - [ ] Subtask 3.1: Document full cluster rebuild from Git + VolSync + 1Password
  - [ ] Subtask 3.2: Document CNPG PITR procedure with timeline selection
  - [ ] Subtask 3.3: Document VolSync PVC restore with snapshot selection
  - [ ] Subtask 3.4: Include estimated recovery times (RTOs)
  - [ ] Subtask 3.5: Add verification steps for data integrity

- [ ] Task 4: Create cnpg-restore.md runbook (AC: #3, #8)
  - [ ] Subtask 4.1: Document on-demand backup creation
  - [ ] Subtask 4.2: Document PITR to test namespace
  - [ ] Subtask 4.3: Document full cluster recovery from Barman/R2
  - [ ] Subtask 4.4: Include database connection patterns (`${APP}-pguser-secret`)
  - [ ] Subtask 4.5: Add backup verification commands

- [ ] Task 5: Create cluster-upgrade.md runbook (AC: #4, #8)
  - [ ] Subtask 5.1: Document Talos node upgrade with `task talos:upgrade-node`
  - [ ] Subtask 5.2: Document Kubernetes version upgrade with `task talos:upgrade-k8s`
  - [ ] Subtask 5.3: Include pre-upgrade checklist (backups, node health)
  - [ ] Subtask 5.4: Document rollback procedures
  - [ ] Subtask 5.5: Add verification steps between node upgrades

- [ ] Task 6: Create rook-ceph.md runbook (AC: #5, #8)
  - [ ] Subtask 6.1: Document Ceph health check commands (`ceph status`, `ceph health detail`)
  - [ ] Subtask 6.2: Document OSD troubleshooting procedures
  - [ ] Subtask 6.3: Document pool capacity expansion
  - [ ] Subtask 6.4: Document PG recovery and maintenance
  - [ ] Subtask 6.5: Add common issues and resolutions matrix

- [ ] Task 7: Create cilium.md runbook (AC: #6, #8)
  - [ ] Subtask 7.1: Document network policy debugging with `cilium policy`
  - [ ] Subtask 7.2: Document connectivity test execution and result interpretation
  - [ ] Subtask 7.3: Document BGP session verification with `cilium bgp peers`
  - [ ] Subtask 7.4: Document Hubble usage for traffic analysis
  - [ ] Subtask 7.5: Document policy bypass annotation for debugging

- [ ] Task 8: Create flux.md runbook (AC: #7, #8)
  - [ ] Subtask 8.1: Document reconciliation troubleshooting with `flux logs`
  - [ ] Subtask 8.2: Document HelmRelease debugging with `flux get hr` and events
  - [ ] Subtask 8.3: Document Kustomization debugging with `flux get ks`
  - [ ] Subtask 8.4: Document suspend/resume procedures with `task flux:suspend/resume`
  - [ ] Subtask 8.5: Document force reconciliation with `task flux:reconcile`

## Dev Notes

### Architecture Context

**Purpose of This Story:**
Create comprehensive operational runbooks that enable efficient troubleshooting and recovery across the k8s-ops platform. These runbooks complement the taskfile automation from previous stories by providing:
- Contextual understanding of **when** to use each procedure
- Detailed **diagnosis** steps to identify root causes
- Step-by-step **resolution** procedures with verification
- Cross-references to **taskfile commands** where applicable

**Technology Stack for Runbooks:**
| Component | Version | Documentation Source |
|-----------|---------|---------------------|
| Talos Linux | v1.12.0 | https://talos.dev/latest/ |
| Cilium | v1.18.5 | https://docs.cilium.io/en/v1.18/ |
| Flux CD | v2.7.5 | https://fluxcd.io/flux/cmd/ |
| Rook-Ceph | v1.18.8 | https://rook.io/docs/rook/latest/ |
| CloudNative-PG | Latest | https://cloudnative-pg.io/documentation/ |
| VictoriaMetrics | v1.131.0 | https://docs.victoriametrics.com/ |

### Previous Story Context (Story 4.4)

**Kubernetes Taskfiles Learnings:**
- Taskfile patterns established for cluster-aware operations
- CLUSTER variable defaults to `infra`, accepts `apps`
- All commands use `--context {{.CLUSTER}}` pattern
- Tasks include verification steps after operations

**Taskfile Categories Available for Reference:**
| Category | Key Tasks |
|----------|-----------|
| `bootstrap:*` | bootstrap:infra, bootstrap:apps |
| `talos:*` | apply-node, upgrade-node, upgrade-k8s, reset-cluster |
| `kubernetes:*` | sync-secrets, hr-restart, cleanse-pods, browse-pvc |
| `flux:*` | reconcile, suspend, resume, logs, events, diff |
| `volsync:*` | snapshot, restore, unlock, list, status |
| `dr:*` | verify-backups, test-cnpg-restore |
| `op:*` | push, pull kubeconfig |

### Runbook Structure Pattern (REQUIRED)

Each runbook MUST follow this structure:

```markdown
# [Component] Operations Runbook

## Overview

Brief description of the component and when to use this runbook.

## Quick Reference

| Command | Description |
|---------|-------------|
| `task <category>:<task>` | Brief description |
| `kubectl <command>` | Brief description |

## Symptoms

### Symptom: [Problem Description]

**Indicators:**
- Observable indicator 1
- Observable indicator 2

**Related Alerts:**
- Alert name if applicable

---

## Diagnosis

### Step 1: [Diagnosis Step]

```bash
# Command to run
command --flags
```

**Expected Output:**
- What to look for in output

**If Abnormal:**
- What it means if output is unexpected

---

## Resolution Procedures

### Procedure: [Resolution Name]

**When to Use:**
- Condition that requires this procedure

**Prerequisites:**
- Required state before starting

**Steps:**

1. **Step Name**
   ```bash
   command
   ```
   **Verify:** Verification command or expected result

2. **Step Name**
   ```bash
   command
   ```
   **Verify:** Verification command or expected result

**Rollback:**
- How to undo if something goes wrong

---

## Common Issues

| Issue | Cause | Resolution |
|-------|-------|------------|
| Issue description | Root cause | Quick fix |

## Related Runbooks

- [Related Runbook](./related.md) - When to use
```

### Critical Technical Details

**Cluster Configuration:**
| Cluster | Context | API Endpoint | Domain |
|---------|---------|--------------|--------|
| infra | `infra` | https://10.25.11.10:6443 | monosense.dev |
| apps | `apps` | https://10.25.13.10:6443 | monosense.io |

**CNPG Shared Cluster Pattern:**
- Cluster name: `postgres` in `databases` namespace
- Host: `postgres-rw.databases.svc.cluster.local`
- Credentials: `${APP}-pguser-secret`
- Backups: Cloudflare R2 via Barman (30-day retention)

**Backup Destinations:**
- **CNPG Barman**: `s3://cnpg-{env}/` on Cloudflare R2
- **VolSync Restic**: `s3://{VOLSYNC_R2}/{APP}` on Cloudflare R2
- R2 Endpoint: `eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com`

**Storage Classes:**
| StorageClass | Technology | Use Case |
|--------------|------------|----------|
| `ceph-block` | Rook-Ceph | General stateful apps (RWO) |
| `openebs-hostpath` | OpenEBS | CNPG PostgreSQL (local NVMe) |
| NFS mount | csi-driver-nfs | Shared files (RWX) |

**Network Policy Tiers:**
| Tier | Namespaces | Default |
|------|------------|---------|
| Tier 0 | kube-system, flux-system | Always Allow |
| Tier 1 | observability, cert-manager, external-secrets | Controlled Access |
| Tier 2 | All application namespaces | Default Deny |

### Bootstrap Sequence Reference

**Phase 1: Pre-Flux (Helmfile)**
```
CRDs → Cilium → CoreDNS → Spegel → cert-manager → Flux
```

**Phase 2: Post-Flux (GitOps)**
```
external-secrets → Rook-Ceph → VictoriaMetrics → Applications
```

**Bootstrap Prerequisites:**
| Prerequisite | Verification Command |
|--------------|---------------------|
| GitHub repo | `gh repo view monosense/k8s-ops` |
| 1Password vault | `op item list --vault k8s-ops` |
| Cloudflare R2 | `terraform -chdir=terraform/cloudflare plan` |
| SOPS AGE key | `sops -d test.sops.yaml` succeeds |
| Talos nodes | `talosctl -n 10.25.11.10 version` |

### DR Testing Cadence Reference

| Test Type | Frequency | Scope | RTO Target |
|-----------|-----------|-------|------------|
| CNPG PITR | Monthly | Restore to test namespace | <30min |
| CNPG Full Recovery | Quarterly | Restore to separate cluster | <2h |
| VolSync PVC Restore | Monthly | Restore single app | <30min |
| Full DR Simulation | Bi-annually | Simulate infra cluster failure | <4h |
| Backup Verification | Weekly (automated) | Verify R2 accessibility | N/A |

### Cilium Operations Reference

**Connectivity Test:**
```bash
cilium --context ${CLUSTER} connectivity test
```

**BGP Verification:**
```bash
cilium --context ${CLUSTER} bgp peers
```

**Policy Debug Bypass:**
```yaml
# Add to pod annotations for debugging
policy.cilium.io/enforce: "false"
```

**Hubble Usage:**
```bash
# Enable Hubble CLI
cilium hubble port-forward &

# Observe traffic
hubble observe --namespace ${NAMESPACE}

# Check policy decisions
hubble observe --verdict DROPPED
```

### Flux Operations Reference

**Check Status:**
```bash
flux --context ${CLUSTER} check
flux --context ${CLUSTER} get all -A
```

**Troubleshoot Reconciliation:**
```bash
flux --context ${CLUSTER} logs --all-namespaces
flux --context ${CLUSTER} events
```

**Force Reconciliation:**
```bash
task flux:reconcile APP=${APP} CLUSTER=${CLUSTER}
# OR directly:
flux --context ${CLUSTER} reconcile ks ${APP} --with-source
```

**Suspend/Resume:**
```bash
task flux:suspend APP=${APP} CLUSTER=${CLUSTER}
task flux:resume APP=${APP} CLUSTER=${CLUSTER}
```

### Rook-Ceph Operations Reference

**Health Checks:**
```bash
# Enter Ceph toolbox
kubectl --context ${CLUSTER} -n rook-ceph exec -it deploy/rook-ceph-tools -- bash

# Inside toolbox:
ceph status
ceph health detail
ceph osd status
ceph osd df
ceph pg stat
```

**Common Ceph Commands:**
| Command | Purpose |
|---------|---------|
| `ceph status` | Overall cluster status |
| `ceph health detail` | Detailed health with warnings |
| `ceph osd tree` | OSD topology |
| `ceph osd df` | OSD disk usage |
| `ceph pg dump` | PG status dump |
| `ceph df` | Storage usage |

### CNPG Operations Reference

**Status Check:**
```bash
kubectl cnpg --context ${CLUSTER} status postgres -n databases
```

**On-Demand Backup:**
```bash
kubectl cnpg --context ${CLUSTER} backup postgres -n databases
```

**List Backups:**
```bash
kubectl --context ${CLUSTER} get backups -n databases
```

**PITR Restore (to test namespace):**
```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-pitr-test
  namespace: test-restore
spec:
  instances: 1
  storage:
    size: 10Gi
    storageClass: openebs-hostpath
  bootstrap:
    recovery:
      source: postgres
      recoveryTarget:
        targetTime: "2025-01-15T12:00:00Z"  # Point in time
  externalClusters:
    - name: postgres
      barmanObjectStore:
        destinationPath: s3://cnpg-infra/
        endpointURL: https://eca0833f608b5745af030307a99bdbb4.r2.cloudflarestorage.com
        s3Credentials:
          accessKeyId:
            name: cnpg-r2-credentials
            key: ACCESS_KEY_ID
          secretAccessKey:
            name: cnpg-r2-credentials
            key: SECRET_ACCESS_KEY
```

### Talos Upgrade Reference

**Pre-Upgrade Checklist:**
1. Verify all nodes healthy: `talosctl --nodes ${NODE} health`
2. Backup etcd: `talosctl --nodes ${CONTROL_PLANE} etcd snapshot /tmp/etcd.snapshot`
3. Verify Ceph health: `ceph status` shows HEALTH_OK
4. Verify all HelmReleases ready: `flux get hr -A | grep -v True`

**Rolling Node Upgrade:**
```bash
task talos:upgrade-node CLUSTER=${CLUSTER} NODE=${NODE}
```

**Kubernetes Upgrade:**
```bash
task talos:upgrade-k8s CLUSTER=${CLUSTER}
```

### Project Structure Notes

- **Runbook Location**: `docs/runbooks/`
- **Index Location**: `docs/index.md`
- **Related Taskfiles**: `.taskfiles/`
- **Architecture Reference**: `_bmad-output/planning-artifacts/architecture.md`

### Markdown Formatting Requirements

- Use GitHub-Flavored Markdown
- Code blocks with appropriate language tags (`bash`, `yaml`, `json`)
- Tables for quick reference sections
- Clear hierarchical headings (##, ###, ####)
- Use `> **Note:**` for important callouts
- Use `> **Warning:**` for dangerous operations
- Link between related runbooks

### Anti-Patterns to Avoid

1. **DO NOT** include cluster-specific values (use `${CLUSTER}` variables)
2. **DO NOT** hardcode node IPs (reference the cluster table)
3. **DO NOT** skip verification steps after procedures
4. **DO NOT** omit rollback procedures for destructive operations
5. **DO NOT** forget to reference taskfile commands where applicable
6. **DO NOT** create runbooks without the standard structure

### References

- [Source: docs/project-context.md#Taskfile Operations] - Taskfile categories
- [Source: _bmad-output/planning-artifacts/architecture.md#DR Testing Cadence] - DR procedures
- [Source: _bmad-output/planning-artifacts/architecture.md#Bootstrap Sequence] - Bootstrap order
- [Source: _bmad-output/planning-artifacts/architecture.md#Technology Stack] - Component versions
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.5] - Original acceptance criteria
- [Source: _bmad-output/implementation-artifacts/4-4-create-kubernetes-operational-taskfiles.md] - Taskfile patterns

### External Documentation

- [Talos Linux Documentation](https://talos.dev/latest/)
- [Cilium Documentation](https://docs.cilium.io/en/v1.18/)
- [Flux CD Documentation](https://fluxcd.io/flux/)
- [Rook-Ceph Documentation](https://rook.io/docs/rook/latest/)
- [CloudNative-PG Documentation](https://cloudnative-pg.io/documentation/)
- [VictoriaMetrics Documentation](https://docs.victoriametrics.com/)

### Verification Commands

```bash
# Verify runbook files exist
ls -la docs/runbooks/

# Verify index.md updated
grep -l "runbooks" docs/index.md

# Validate markdown syntax (if markdownlint available)
markdownlint docs/runbooks/*.md

# Check for broken links (if markdown-link-check available)
markdown-link-check docs/runbooks/*.md
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
