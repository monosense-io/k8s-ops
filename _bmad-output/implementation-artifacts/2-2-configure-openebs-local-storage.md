# Story 2.2: Configure OpenEBS Local Storage

Status: ready-for-dev

## Story

As a **platform operator**,
I want **OpenEBS providing local NVMe storage for databases**,
So that **CNPG PostgreSQL clusters get optimal I/O performance**.

## Acceptance Criteria

1. **Given** Rook-Ceph is operational from Story 2.1
   **When** OpenEBS is deployed
   **Then** `infrastructure/base/openebs/` contains:
   - Operator HelmRelease with OpenEBS v4.4
   - StorageClass `openebs-hostpath` for local volumes

2. **And** LocalPV provisioner is running on all nodes

3. **And** a test PVC using `openebs-hostpath` provisions on local NVMe

4. **And** operator uses < 500MB RAM (NFR32)

## Tasks / Subtasks

- [ ] Task 1: Update Talos Machine Configuration for OpenEBS (AC: #2)
  - [ ] Add kubelet extraMounts for `/var/openebs/local` in `clusters/infra/talos/talconfig.yaml`
  - [ ] Configure bind mount with options: `rbind`, `rshared`, `rw`
  - [ ] Apply configuration to all infra cluster nodes via `talosctl apply`
  - [ ] Verify mount exists on nodes after configuration

- [ ] Task 2: Create OpenEBS Directory Structure (AC: #1)
  - [ ] Create `infrastructure/base/openebs/` directory
  - [ ] Create `infrastructure/base/openebs/app/` subdirectory for operator
  - [ ] Create `infrastructure/base/openebs/namespace.yaml` with privileged PodSecurity labels
  - [ ] Create `infrastructure/base/openebs/ks.yaml` Flux Kustomization entry point

- [ ] Task 3: Deploy OpenEBS LocalPV Provisioner (AC: #1, #4)
  - [ ] Add OpenEBS HelmRepository to `infrastructure/base/repositories/helm/openebs.yaml`
  - [ ] Create `infrastructure/base/openebs/app/helmrelease.yaml` with OpenEBS v4.4.0
  - [ ] Configure HelmRelease with proper remediation (retries: -1 for operator)
  - [ ] Disable Replicated Storage (Mayastor): `engines.replicated.mayastor.enabled: false`
  - [ ] Configure LocalPV hostpath basePath: `/var/openebs/local`
  - [ ] Set resource limits for provisioner pod (< 500MB RAM per NFR32)
  - [ ] Create `infrastructure/base/openebs/app/kustomization.yaml`

- [ ] Task 4: Configure StorageClass (AC: #1, #3)
  - [ ] Verify default `openebs-hostpath` StorageClass is created by Helm chart
  - [ ] Confirm StorageClass configuration has correct basePath
  - [ ] Document that this is the PRIMARY StorageClass for CNPG PostgreSQL

- [ ] Task 5: Configure Flux Dependencies (AC: #1)
  - [ ] Update `infrastructure/base/openebs/ks.yaml` with proper dependsOn
  - [ ] Ensure openebs depends on cluster-infrastructure (after Cilium CNI)
  - [ ] Add to `infrastructure/base/kustomization.yaml` resource list
  - [ ] Configure health checks for provisioner readiness

- [ ] Task 6: Verify Provisioner Health (AC: #2)
  - [ ] Deploy all OpenEBS resources via Flux reconciliation
  - [ ] Wait for provisioner pods to become ready on all nodes
  - [ ] Verify DaemonSet is scheduled to all worker nodes
  - [ ] Check provisioner logs for any errors
  - [ ] Verify StorageClass is available: `kubectl get sc openebs-hostpath`

- [ ] Task 7: Test PVC Provisioning (AC: #3)
  - [ ] Create test PVC using `openebs-hostpath` StorageClass
  - [ ] Create test Pod mounting the PVC
  - [ ] Write and read data to verify functionality
  - [ ] Verify local volume created on node filesystem
  - [ ] Clean up test resources after verification

- [ ] Task 8: Document and Finalize
  - [ ] Add OpenEBS section to `docs/runbooks/storage.md`
  - [ ] Document Talos upgrade procedure with `--preserve` flag
  - [ ] Document basePath location and backup considerations
  - [ ] Add verification commands to runbook

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document (architecture.md):**

1. **Storage Strategy:**
   | Type | Technology | Use Case |
   |------|------------|----------|
   | Block (RWO) | Rook-Ceph (`ceph-block`) | Stateful apps, general persistent storage |
   | Shared (RWX) | NFS | Media, shared configs |
   | Local (hostPath) | OpenEBS LocalPath | CNPG PostgreSQL clusters (local NVMe performance) |
   | Object (S3) | MinIO (infra cluster only) | General S3 storage (backed by NFS) |

2. **Technology Stack Versions (December 2025):**
   | Component | Version | Notes |
   |-----------|---------|-------|
   | OpenEBS | v4.4 | LocalPV for CNPG |
   | Kubernetes | v1.35.0 (in Talos 1.12.0) | Fully compatible |

3. **NFR Requirements:**
   - NFR32: Operator footprint < 500 MB RAM each

4. **Bootstrap Sequence Position:**
   ```
   Phase 2: Post-Flux (GitOps Reconciliation)
   external-secrets → Rook-Ceph → OpenEBS → VictoriaMetrics → Applications
   ```
   OpenEBS is deployed AFTER Rook-Ceph but BEFORE CNPG and applications.

5. **App Location Rules:**
   - OpenEBS goes in `infrastructure/base/openebs/` (shared infrastructure)
   - Deployed to BOTH clusters via Flux reconciliation

### Project Context Rules (Critical)

**From project-context.md:**

1. **Storage Class Selection:**
   | Use Case | StorageClass | Notes |
   |----------|--------------|-------|
   | General stateful apps | `ceph-block` | Rook-Ceph RWO |
   | CNPG PostgreSQL | `openebs-hostpath` | Local NVMe performance |
   | Shared files (RWX) | NFS mount | Via csi-driver-nfs |
   | Backups | Cloudflare R2 | VolSync + CNPG Barman |

2. **HelmRelease Standards:**
   - Operators use `retries: -1` for install (infinite retry)
   - All HelmReleases MUST have remediation blocks

3. **Namespace Security:**
   - OpenEBS requires privileged namespace: `pod-security.kubernetes.io/enforce: privileged`

### Talos Linux Specific Requirements

**From OpenEBS Documentation and Talos Guides:**

1. **Kubelet ExtraMounts Required:**
   Talos requires explicit bind-mounts for hostPath volumes. Add to `talconfig.yaml`:
   ```yaml
   machine:
     kubelet:
       extraMounts:
         - destination: /var/openebs/local
           type: bind
           source: /var/openebs/local
           options:
             - rbind
             - rshared
             - rw
   ```

2. **Namespace Labels Required:**
   ```yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: openebs
     labels:
       pod-security.kubernetes.io/enforce: privileged
       pod-security.kubernetes.io/enforce-version: latest
       pod-security.kubernetes.io/audit: privileged
       pod-security.kubernetes.io/audit-version: latest
       pod-security.kubernetes.io/warn: privileged
       pod-security.kubernetes.io/warn-version: latest
   ```

3. **CRITICAL: Talos Upgrade Preservation:**
   - ALWAYS use `talosctl upgrade --preserve` when upgrading Talos nodes
   - Without `--preserve`, the `/var/openebs/local` directory will be wiped
   - This will result in DATA LOSS for all LocalPV volumes

4. **Data Directory:**
   - Use `/var/openebs/local` as basePath (Talos writable path)
   - This path persists across reboots but NOT across upgrades without `--preserve`

### Directory Structure

```
infrastructure/base/openebs/
├── app/                              # OpenEBS Operator
│   ├── helmrelease.yaml
│   └── kustomization.yaml
├── namespace.yaml                    # With privileged PodSecurity
└── ks.yaml                           # Flux Kustomization entry point
```

### HelmRelease Template (Operator)

```yaml
---
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: openebs
spec:
  interval: 1h
  chart:
    spec:
      chart: openebs
      version: 4.4.0
      sourceRef:
        kind: HelmRepository
        name: openebs
        namespace: flux-system
  install:
    crds: CreateReplace
    remediation:
      retries: -1  # Operator must succeed
  upgrade:
    cleanupOnFail: true
    crds: CreateReplace
    remediation:
      strategy: rollback
      retries: 3
  values:
    # Disable Replicated Storage (Mayastor) - we only need LocalPV
    engines:
      replicated:
        mayastor:
          enabled: false
    # LocalPV Hostpath Configuration
    localpv-provisioner:
      hostpathClass:
        enabled: true
        name: openebs-hostpath
        isDefaultClass: false  # Rook-Ceph is for general use
        basePath: /var/openebs/local
        reclaimPolicy: Delete
        # Resource configuration for provisioner
      resources:
        requests:
          cpu: 50m
          memory: 64Mi
        limits:
          cpu: 200m
          memory: 256Mi
    # Disable LVM and ZFS - not needed
    lvm-localpv:
      enabled: false
    zfs-localpv:
      enabled: false
    # Disable OpenEBS CRDs for volume snapshots if already installed
    openebs-crds:
      csi:
        volumeSnapshots:
          enabled: false  # Already installed by Rook-Ceph
```

### Namespace Template

```yaml
---
apiVersion: v1
kind: Namespace
metadata:
  name: openebs
  labels:
    pod-security.kubernetes.io/enforce: privileged
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: privileged
    pod-security.kubernetes.io/audit-version: latest
    pod-security.kubernetes.io/warn: privileged
    pod-security.kubernetes.io/warn-version: latest
```

### HelmRepository Template

```yaml
---
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: openebs
  namespace: flux-system
spec:
  interval: 1h
  url: https://openebs.github.io/openebs
```

### Flux Kustomization Template

```yaml
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name openebs
  namespace: flux-system
spec:
  targetNamespace: openebs
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./infrastructure/base/openebs
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: true
  interval: 1h
  retryInterval: 1m
  timeout: 10m
  dependsOn:
    - name: rook-ceph  # Must be after Rook-Ceph is deployed
```

### Talos Machine Config Patch (talconfig.yaml)

```yaml
# Add to machine.kubelet section in talconfig.yaml
machine:
  kubelet:
    extraMounts:
      - destination: /var/openebs/local
        type: bind
        source: /var/openebs/local
        options:
          - rbind
          - rshared
          - rw
```

### Test PVC Template

```yaml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: openebs-test-pvc
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: openebs-hostpath
---
apiVersion: v1
kind: Pod
metadata:
  name: openebs-test-pod
  namespace: default
spec:
  containers:
    - name: test
      image: busybox
      command: ["sleep", "infinity"]
      volumeMounts:
        - name: test-volume
          mountPath: /mnt/test
  volumes:
    - name: test-volume
      persistentVolumeClaim:
        claimName: openebs-test-pvc
```

### Previous Story Intelligence

**From Story 2.1 (Deploy Rook-Ceph Storage Cluster):**
- Rook-Ceph v1.18.8 is operational with Ceph Squid 19.2.3
- StorageClass `ceph-block` is available for general stateful apps
- Privileged namespace pattern established for storage operators
- Flux Kustomization dependency chain pattern demonstrated
- HelmRelease remediation pattern: `retries: -1` for operators

**Key Learnings from Story 2.1:**
- Operators need `retries: -1` for install remediation
- Use `.yaml` extension consistently
- Flux Kustomization path uses relative format: `./infrastructure/base/...`
- Use `wait: true` for infrastructure components
- Privileged namespace labels are REQUIRED for storage operators

### Latest Technical Information (December 2025)

**OpenEBS v4.4.0 Key Information:**

1. **New Helm Registry:**
   - Chart location changed to: `https://openebs.github.io/openebs`
   - Old registry `https://openebs.github.io/charts` is deprecated

2. **Installation Components:**
   - Default installation includes: LocalPV Hostpath, LocalPV LVM, LocalPV ZFS, and Replicated Storage
   - For CNPG use case, disable everything except LocalPV Hostpath
   - Set `engines.replicated.mayastor.enabled: false` to disable Mayastor

3. **StorageClass Created:**
   - Default StorageClass: `openebs-hostpath`
   - BasePath: `/var/openebs/local`
   - Provisioner: `openebs.io/local`

4. **Resource Requirements:**
   - LocalPV provisioner is lightweight
   - Provisioner pod typically uses ~50Mi RAM
   - Well within NFR32 requirement (< 500MB)

5. **Kubernetes Compatibility:**
   - Minimum: Kubernetes v1.23
   - Tested with: Kubernetes v1.35.0 (in Talos 1.12.0)

6. **Important Helm Values:**
   ```yaml
   engines.replicated.mayastor.enabled: false  # Disable Mayastor
   lvm-localpv.enabled: false                   # Disable LVM
   zfs-localpv.enabled: false                   # Disable ZFS
   localpv-provisioner.hostpathClass.basePath: /var/openebs/local
   ```

### Verification Commands

```bash
# Check HelmRepository
kubectl get helmrepository openebs -n flux-system

# Check HelmRelease status
kubectl get helmrelease openebs -n flux-system

# Check OpenEBS pods
kubectl get pods -n openebs -l openebs.io/component-name=openebs-localpv-provisioner

# Check provisioner is running on all nodes
kubectl get pods -n openebs -o wide

# Check StorageClass
kubectl get sc openebs-hostpath

# Describe StorageClass for details
kubectl describe sc openebs-hostpath

# Test PVC provisioning
kubectl get pvc -A | grep openebs

# Check PV was created
kubectl get pv | grep openebs

# Verify hostpath on node
kubectl exec -it <provisioner-pod> -n openebs -- ls -la /var/openebs/local/

# Check Flux reconciliation status
flux get kustomization openebs
```

### Critical Implementation Rules

1. **Talos ExtraMounts:**
   - MUST configure kubelet extraMounts BEFORE deploying OpenEBS
   - Without this, LocalPV provisioner will fail to create volumes

2. **Namespace Security:**
   - MUST add `pod-security.kubernetes.io/enforce: privileged` label
   - Without this, provisioner pods will fail to start

3. **Disable Unused Components:**
   - MUST disable Mayastor, LVM, and ZFS to reduce resource usage
   - Only LocalPV Hostpath is needed for CNPG use case

4. **StorageClass Priority:**
   - `openebs-hostpath` is specifically for CNPG PostgreSQL
   - General applications should use `ceph-block` (Rook-Ceph)
   - Do NOT set `openebs-hostpath` as default

5. **Upgrade Safety:**
   - ALWAYS use `talosctl upgrade --preserve` for Talos upgrades
   - Document this in runbooks and taskfiles
   - Failure to use `--preserve` will result in DATA LOSS

6. **Dependency Order:**
   - OpenEBS depends on Rook-Ceph (for CSI volume snapshot CRDs)
   - CNPG depends on OpenEBS (for storage provisioning)

### Project Structure Notes

- **Alignment:** OpenEBS follows same structure as Rook-Ceph in Story 2.1
- **Path:** `infrastructure/base/openebs/` for shared infrastructure
- **Deployed to:** BOTH clusters (infra and apps)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.2: Configure OpenEBS Local Storage]
- [Source: _bmad-output/planning-artifacts/architecture.md#Storage Strategy]
- [Source: docs/project-context.md#Storage Class Selection]
- [OpenEBS Documentation](https://openebs.io/docs/quickstart-guide/installation)
- [OpenEBS LocalPV Hostpath Guide](https://openebs.io/docs/user-guides/local-storage-user-guide/local-pv-hostpath/hostpath-overview)
- [OpenEBS Talos Installation](https://github.com/openebs/dynamic-localpv-provisioner/blob/develop/docs/installation/platforms/talos.md)
- [Talos Local Storage Documentation](https://www.talos.dev/v1.10/kubernetes-guides/configuration/replicated-local-storage-with-openebs-jiva/)

### Validation Checklist

Before marking complete, verify:
- [ ] Talos machine config updated with kubelet extraMounts for `/var/openebs/local`
- [ ] Talos config applied to all nodes
- [ ] `infrastructure/base/openebs/` directory structure created
- [ ] OpenEBS HelmRepository added to `infrastructure/base/repositories/`
- [ ] OpenEBS HelmRelease v4.4.0 deployed
- [ ] Mayastor, LVM, ZFS disabled in HelmRelease values
- [ ] Namespace has privileged PodSecurity labels
- [ ] LocalPV provisioner pods running on all nodes
- [ ] StorageClass `openebs-hostpath` available
- [ ] Test PVC provisions and binds successfully
- [ ] Test Pod can write and read from volume
- [ ] Flux reconciliation successful
- [ ] Runbook documentation updated with Talos upgrade warning
- [ ] Resource usage < 500MB (NFR32)

### Git Commit Message Format

```
feat(openebs): deploy OpenEBS v4.4.0 LocalPV provisioner

- Deploy OpenEBS LocalPV provisioner v4.4.0 via HelmRelease
- Configure Talos kubelet extraMounts for /var/openebs/local
- Disable Mayastor, LVM, ZFS - LocalPV only
- Create openebs-hostpath StorageClass for CNPG use
- Add Talos-compatible privileged namespace
- Verify provisioner running on all nodes
- NFR32: < 500MB RAM footprint
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
