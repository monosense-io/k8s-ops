# Story 2.1: Deploy Rook-Ceph Storage Cluster

Status: ready-for-dev

## Story

As a **platform operator**,
I want **Rook-Ceph providing block storage with 3-replica redundancy**,
So that **applications have reliable, persistent storage**.

## Acceptance Criteria

1. **Given** a running infra cluster with Flux operational
   **When** Rook-Ceph is deployed
   **Then** `infrastructure/base/rook-ceph/` contains:
   - Operator HelmRelease with Rook v1.18.8
   - CephCluster CR with 3 replicas, Ceph Squid 19.2.3
   - StorageClass `ceph-block` for RWO volumes

2. **And** Ceph cluster reaches `HEALTH_OK` status

3. **And** all OSDs are up and PGs are `active+clean`

4. **And** `kubectl get cephcluster -n rook-ceph` shows Ready state

5. **And** a test PVC using `ceph-block` StorageClass provisions successfully

## Tasks / Subtasks

- [ ] Task 1: Create Rook-Ceph Directory Structure (AC: #1)
  - [ ] Create `infrastructure/base/rook-ceph/` directory
  - [ ] Create `infrastructure/base/rook-ceph/app/` subdirectory for operator
  - [ ] Create `infrastructure/base/rook-ceph/cluster/` subdirectory for CephCluster
  - [ ] Create `infrastructure/base/rook-ceph/ks.yaml` Flux Kustomization entry point
  - [ ] Add namespace configuration with privileged PodSecurity label

- [ ] Task 2: Deploy Rook-Ceph Operator (AC: #1)
  - [ ] Create `infrastructure/base/rook-ceph/app/helmrelease.yaml` with Rook v1.18.8
  - [ ] Configure HelmRelease with proper remediation (retries: -1 for operator, rollback strategy)
  - [ ] Set `csi.rookUseCsiOperator: true` for CSI operator (new in v1.18)
  - [ ] Configure CSI driver settings for RBD and CephFS
  - [ ] Set resource limits for operator pods
  - [ ] Create `infrastructure/base/rook-ceph/app/kustomization.yaml`
  - [ ] Verify HelmRepository reference exists in `infrastructure/base/repositories/`

- [ ] Task 3: Deploy CSI Operator (AC: #1)
  - [ ] Create CSI operator configuration (automatically installed by helm with `csi.rookUseCsiOperator`)
  - [ ] Configure CSI driver for RBD volumes
  - [ ] Configure CSI driver for CephFS volumes (if needed)
  - [ ] Set CSI driver resource limits

- [ ] Task 4: Create CephCluster CR (AC: #1, #2, #3, #4)
  - [ ] Create `infrastructure/base/rook-ceph/cluster/cephcluster.yaml`
  - [ ] Configure Ceph Squid 19.2.3 image: `quay.io/ceph/ceph:v19.2.3`
  - [ ] Set 3 MON replicas on separate nodes
  - [ ] Configure OSD placement with anti-affinity
  - [ ] Set `useAllNodes: false` for explicit node control
  - [ ] Configure device selection for available disks
  - [ ] Set `dataDirHostPath: /var/lib/rook` (Talos compatible path)
  - [ ] Configure placement constraints for Talos nodes
  - [ ] Set resource requests (do NOT set limits for OSDs)
  - [ ] Create `infrastructure/base/rook-ceph/cluster/kustomization.yaml`

- [ ] Task 5: Create CephBlockPool and StorageClass (AC: #1, #5)
  - [ ] Create `infrastructure/base/rook-ceph/cluster/cephblockpool.yaml`
  - [ ] Configure pool with 3 replicas (`replicated.size: 3`)
  - [ ] Set failure domain to `host` for node-level redundancy
  - [ ] Create `infrastructure/base/rook-ceph/cluster/storageclass.yaml` for `ceph-block`
  - [ ] Configure StorageClass with `reclaimPolicy: Delete`
  - [ ] Set `allowVolumeExpansion: true`
  - [ ] Set `volumeBindingMode: Immediate`
  - [ ] Mark as non-default StorageClass (OpenEBS is default for CNPG)

- [ ] Task 6: Configure Talos-Specific Settings (AC: #2, #3)
  - [ ] Add privileged PodSecurity label to namespace: `pod-security.kubernetes.io/enforce: privileged`
  - [ ] Verify Talos nodes have dedicated disks for Ceph (not system disk)
  - [ ] Configure node selector for storage nodes (if using dedicated nodes)
  - [ ] Set tolerations if needed for dedicated storage nodes
  - [ ] Document disk requirements per node

- [ ] Task 7: Configure Flux Dependencies (AC: #1)
  - [ ] Update `infrastructure/base/rook-ceph/ks.yaml` with proper dependsOn
  - [ ] Ensure rook-ceph depends on cluster-infrastructure (Cilium CNI required)
  - [ ] Add operator → cluster dependency chain in ks.yaml
  - [ ] Add to `infrastructure/base/kustomization.yaml` resource list
  - [ ] Configure health checks for CephCluster readiness

- [ ] Task 8: Verify Cluster Health (AC: #2, #3, #4)
  - [ ] Deploy all Rook-Ceph resources via Flux reconciliation
  - [ ] Wait for operator pods to become ready
  - [ ] Monitor CephCluster status until Ready
  - [ ] Verify Ceph health: `kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph status`
  - [ ] Check all OSDs are up: `kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph osd tree`
  - [ ] Verify PGs are `active+clean`: `kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph pg stat`
  - [ ] Check MON quorum: `kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph mon stat`

- [ ] Task 9: Test PVC Provisioning (AC: #5)
  - [ ] Create test PVC using `ceph-block` StorageClass
  - [ ] Create test Pod mounting the PVC
  - [ ] Write and read data to verify functionality
  - [ ] Verify RBD volume created in Ceph
  - [ ] Clean up test resources after verification

- [ ] Task 10: Deploy Toolbox Pod (Optional but Recommended)
  - [ ] Create `infrastructure/base/rook-ceph/cluster/toolbox.yaml` deployment
  - [ ] Configure with Ceph tools for cluster management
  - [ ] Verify toolbox can access Ceph cluster

- [ ] Task 11: Document and Finalize
  - [ ] Update `docs/runbooks/rook-ceph.md` with operational procedures
  - [ ] Document disk layout per node
  - [ ] Document OSD recovery procedures
  - [ ] Document MON quorum recovery procedures

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
   | Rook-Ceph | v1.18.8 | Latest patch release |
   | Ceph | Squid 19.2.3 | Latest stable |
   | Kubernetes | v1.35.0 (in Talos 1.12.0) | Rook v1.18 supports k8s v1.29-v1.34+ |

3. **NFR Requirements:**
   - NFR17: Rook-Ceph availability 99.9% (Ceph cluster HEALTH_OK uptime)
   - NFR22: Storage redundancy 3 replicas (Rook-Ceph replication factor)
   - NFR33: Storage efficiency - Thin provisioning (Rook-Ceph uses only allocated space)

4. **Bootstrap Sequence Position:**
   ```
   Phase 2: Post-Flux (GitOps Reconciliation)
   external-secrets → Rook-Ceph → VictoriaMetrics → Applications
   ```
   Rook-Ceph is deployed AFTER external-secrets and BEFORE applications.

5. **App Location Rules:**
   - Rook-Ceph goes in `infrastructure/base/rook-ceph/` (shared infrastructure)
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

2. **Dependency Rules:**
   - Apps with Ceph storage MUST depend on `rook-ceph-cluster`

3. **HelmRelease Standards:**
   - Operators use `retries: -1` for install (infinite retry)
   - All HelmReleases MUST have remediation blocks

4. **Namespace Security:**
   - Rook-Ceph requires privileged namespace: `pod-security.kubernetes.io/enforce: privileged`

### Talos Linux Specific Requirements

**From Talos Documentation (talos.dev):**

1. **Disk Requirements:**
   - Talos reserves an entire disk for OS installation
   - Machines with multiple available disks are needed for Ceph
   - Block devices or partitions used by Ceph must have no partitions or formatted filesystems

2. **Namespace Label Required:**
   ```yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: rook-ceph
     labels:
       pod-security.kubernetes.io/enforce: privileged
       pod-security.kubernetes.io/enforce-version: latest
       pod-security.kubernetes.io/audit: privileged
       pod-security.kubernetes.io/audit-version: latest
       pod-security.kubernetes.io/warn: privileged
       pod-security.kubernetes.io/warn-version: latest
   ```

3. **Data Directory:**
   - Use `/var/lib/rook` as dataDirHostPath (Talos writable path)

4. **Maintenance Considerations:**
   - ALWAYS check Ceph health before Talos node upgrades
   - Wait for cluster to return to HEALTH_OK before proceeding to next node

### Directory Structure

```
infrastructure/base/rook-ceph/
├── app/                              # Rook Operator
│   ├── helmrelease.yaml
│   └── kustomization.yaml
├── cluster/                          # CephCluster and resources
│   ├── cephcluster.yaml
│   ├── cephblockpool.yaml
│   ├── storageclass.yaml
│   ├── toolbox.yaml                  # Optional debugging pod
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
  name: rook-ceph-operator
spec:
  interval: 1h
  chart:
    spec:
      chart: rook-ceph
      version: v1.18.8
      sourceRef:
        kind: HelmRepository
        name: rook-ceph
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
    crds:
      enabled: true
    csi:
      rookUseCsiOperator: true  # New in v1.18 - recommended
      enableRbdDriver: true
      enableCephfsDriver: false  # Enable if CephFS needed
      csiRBDPluginResource:
        requests:
          memory: 128Mi
          cpu: 100m
        limits:
          memory: 512Mi
          cpu: 500m
    monitoring:
      enabled: true
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
```

### CephCluster CR Template

```yaml
---
apiVersion: ceph.rook.io/v1
kind: CephCluster
metadata:
  name: rook-ceph
  namespace: rook-ceph
spec:
  cephVersion:
    image: quay.io/ceph/ceph:v19.2.3
    allowUnsupported: false
  dataDirHostPath: /var/lib/rook
  mon:
    count: 3
    allowMultiplePerNode: false
  mgr:
    count: 2
    allowMultiplePerNode: false
    modules:
      - name: pg_autoscaler
        enabled: true
  dashboard:
    enabled: true
    ssl: true
  network:
    provider: host  # Recommended for performance
  storage:
    useAllNodes: false
    useAllDevices: false
    config:
      osdsPerDevice: "1"
    nodes:
      - name: "node1"
        devices:
          - name: "/dev/sdb"  # Adjust to actual disk names
      - name: "node2"
        devices:
          - name: "/dev/sdb"
      - name: "node3"
        devices:
          - name: "/dev/sdb"
  placement:
    all:
      nodeAffinity:
        requiredDuringSchedulingIgnoredDuringExecution:
          nodeSelectorTerms:
            - matchExpressions:
                - key: node-role.kubernetes.io/control-plane
                  operator: DoesNotExist
      tolerations: []
    osd:
      podAntiAffinity:
        preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: rook-ceph-osd
              topologyKey: kubernetes.io/hostname
  resources:
    mgr:
      requests:
        cpu: 100m
        memory: 512Mi
    mon:
      requests:
        cpu: 100m
        memory: 512Mi
    osd:
      requests:
        cpu: 500m
        memory: 2Gi
      # NOTE: Do NOT set limits for OSDs - causes issues
    prepareosd:
      requests:
        cpu: 250m
        memory: 50Mi
```

### CephBlockPool Template

```yaml
---
apiVersion: ceph.rook.io/v1
kind: CephBlockPool
metadata:
  name: ceph-blockpool
  namespace: rook-ceph
spec:
  failureDomain: host
  replicated:
    size: 3
    requireSafeReplicaSize: true
  parameters:
    compression_mode: none  # Enable "aggressive" for better storage efficiency
```

### StorageClass Template

```yaml
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ceph-block
  annotations:
    storageclass.kubernetes.io/is-default-class: "false"  # OpenEBS is default for CNPG
provisioner: rook-ceph.rbd.csi.ceph.com
parameters:
  clusterID: rook-ceph
  pool: ceph-blockpool
  imageFormat: "2"
  imageFeatures: layering
  csi.storage.k8s.io/provisioner-secret-name: rook-csi-rbd-provisioner
  csi.storage.k8s.io/provisioner-secret-namespace: rook-ceph
  csi.storage.k8s.io/controller-expand-secret-name: rook-csi-rbd-provisioner
  csi.storage.k8s.io/controller-expand-secret-namespace: rook-ceph
  csi.storage.k8s.io/node-stage-secret-name: rook-csi-rbd-node
  csi.storage.k8s.io/node-stage-secret-namespace: rook-ceph
  csi.storage.k8s.io/fstype: ext4
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: Immediate
```

### Flux Kustomization Template

```yaml
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name rook-ceph
  namespace: flux-system
spec:
  targetNamespace: rook-ceph
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./infrastructure/base/rook-ceph
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: true
  interval: 1h
  retryInterval: 1m
  timeout: 15m
  dependsOn:
    - name: external-secrets-stores  # Must be after secrets are available
  healthCheckExprs:
    - apiVersion: ceph.rook.io/v1
      kind: CephCluster
      failed: status.phase != 'Ready' && status.phase != 'Progressing'
```

### Test PVC Template

```yaml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ceph-test-pvc
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: ceph-block
---
apiVersion: v1
kind: Pod
metadata:
  name: ceph-test-pod
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
        claimName: ceph-test-pvc
```

### Previous Story Intelligence

**From Epic 1 Stories (1.1-1.5):**
- Talos cluster is operational with Cilium CNI
- Flux is connected to k8s-ops repository
- External Secrets Operator is syncing from 1Password
- Node IPs: 10.25.11.11-16 for infra cluster
- Bootstrap sequence completed successfully

**Key Learnings:**
- Operators need `retries: -1` for install remediation
- Use `.yaml` extension consistently
- Flux Kustomization path uses relative format: `./infrastructure/base/...`
- Use `wait: true` for infrastructure components
- Add healthCheckExprs for status monitoring

### Latest Technical Information (December 2025)

**Rook v1.18.8 Key Changes:**

1. **CSI Operator (New Default):**
   - Ceph CSI operator is now the default and recommended component
   - Set `csi.rookUseCsiOperator: true` in helm values
   - CSI operator runs independently to manage Ceph-CSI driver
   - Rook automatically converts settings to CSI operator CRs during upgrade

2. **Kubernetes Compatibility:**
   - Minimum supported: Kubernetes v1.29
   - Maximum supported: Kubernetes v1.34
   - Talos v1.12.0 includes Kubernetes v1.35.0 (should work, verify)

3. **Ceph Squid 19.2.3:**
   - Latest stable Ceph version
   - Released July 2025
   - Image: `quay.io/ceph/ceph:v19.2.3`

4. **Best Practices (from rook.io documentation):**
   - Do NOT set resource limits for OSD pods (can cause issues during failures)
   - Set `useAllNodes: false` for production clusters
   - Use anti-affinity for OSD pods
   - MON count must be odd (3 or 5 recommended)
   - SSDs strongly recommended for MON metadata

5. **Performance Considerations:**
   - Use host networking for best performance
   - Separate MON disks from OSD disks if possible
   - PG autoscaler module recommended for automatic PG management
   - For homelab: expect ~15 CPU cores and 24GB RAM cluster-wide

### Verification Commands

```bash
# Check operator status
kubectl get pods -n rook-ceph -l app=rook-ceph-operator

# Check CephCluster status
kubectl get cephcluster -n rook-ceph

# Detailed cluster status
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph status

# Check OSD status
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph osd tree

# Check PG status
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph pg stat

# Check MON quorum
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph mon stat

# Check pool status
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph osd pool ls detail

# Check StorageClass
kubectl get sc ceph-block

# Test PVC provisioning
kubectl get pvc -A | grep ceph

# Check CSI driver pods
kubectl get pods -n rook-ceph -l app=csi-rbdplugin
```

### Critical Implementation Rules

1. **Namespace Security:**
   - MUST add `pod-security.kubernetes.io/enforce: privileged` label
   - Without this, Ceph pods will fail to start on Talos

2. **OSD Resources:**
   - Set requests but NEVER set limits for OSD pods
   - OSD limits can cause worse failures during outage scenarios

3. **Node Selection:**
   - Set `useAllNodes: false` in production
   - Explicitly define which nodes and disks to use
   - Avoid using Talos system disk

4. **MON Configuration:**
   - Always use odd number (3 or 5)
   - Never allow multiple per node in production

5. **Disk Preparation:**
   - Disks must have no partitions or filesystems
   - Wipe disks if previously used: `sgdisk --zap-all /dev/sdX`

6. **Health Checks:**
   - Always verify HEALTH_OK before node maintenance
   - Wait for all PGs to be `active+clean` before proceeding

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.1: Deploy Rook-Ceph Storage Cluster]
- [Source: _bmad-output/planning-artifacts/architecture.md#Storage Strategy]
- [Source: docs/project-context.md#Storage Class Selection]
- [Rook Documentation](https://rook.io/docs/rook/latest-release/)
- [Rook v1.18 Releases](https://github.com/rook/rook/releases)
- [Talos Ceph Configuration](https://www.talos.dev/v1.10/kubernetes-guides/configuration/ceph-with-rook/)
- [CephCluster CRD Reference](https://rook.io/docs/rook/latest/CRDs/Cluster/ceph-cluster-crd/)
- [Rook Best Practices](https://documentation.suse.com/sbp/storage/html/SBP-rook-ceph-kubernetes/index.html)

### Validation Checklist

Before marking complete, verify:
- [ ] `infrastructure/base/rook-ceph/` directory structure created
- [ ] Rook Operator HelmRelease v1.18.8 deployed
- [ ] CSI operator enabled with `rookUseCsiOperator: true`
- [ ] Namespace has privileged PodSecurity label
- [ ] CephCluster CR with 3 MONs, 3 replica storage
- [ ] Ceph image is `quay.io/ceph/ceph:v19.2.3`
- [ ] CephBlockPool with `replicated.size: 3`
- [ ] StorageClass `ceph-block` created (non-default)
- [ ] `kubectl get cephcluster -n rook-ceph` shows Ready
- [ ] `ceph status` shows HEALTH_OK
- [ ] All OSDs are up per `ceph osd tree`
- [ ] PGs are `active+clean` per `ceph pg stat`
- [ ] Test PVC provisions and binds successfully
- [ ] Toolbox pod deployed for cluster management
- [ ] Flux reconciliation successful
- [ ] Runbook documentation updated

### Git Commit Message Format

```
feat(rook-ceph): deploy Rook-Ceph v1.18.8 storage cluster

- Deploy Rook-Ceph operator v1.18.8 via HelmRelease
- Configure CSI operator (new in v1.18)
- Deploy CephCluster with Ceph Squid 19.2.3
- Configure 3 MONs, 2 MGRs, 3-replica storage
- Create CephBlockPool and ceph-block StorageClass
- Add Talos-compatible privileged namespace
- Verify HEALTH_OK and OSD status
- NFR17: 99.9% availability, NFR22: 3 replicas
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
