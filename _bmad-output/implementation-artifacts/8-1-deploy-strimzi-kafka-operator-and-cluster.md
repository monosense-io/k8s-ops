# Story 8.1: Deploy Strimzi Kafka Operator and Cluster

Status: ready-for-dev

---

## Story

As a **developer**,
I want **a Kafka cluster managed via GitOps**,
So that **I can build event-driven applications without managing Kafka infrastructure**.

---

## Acceptance Criteria

1. **Given** infra cluster is operational with storage
   **When** Strimzi Kafka is deployed
   **Then** `clusters/infra/apps/platform/strimzi-kafka/` contains:
   - Strimzi Operator HelmRelease (latest stable - see Dev Notes for version)
   - Kafka cluster CR with KRaft mode (no ZooKeeper)
   - 3 controllers + 3 brokers configuration using KafkaNodePool resources
   - Storage using Rook-Ceph (`ceph-block` StorageClass)

2. **Given** Strimzi operator is deployed
   **When** Kafka cluster CR is applied
   **Then** Kafka cluster reaches Ready state

3. **Given** Kafka cluster is Ready
   **When** developers create KafkaTopic CRs
   **Then** topics are provisioned automatically

4. **Given** Kafka cluster is operational
   **When** querying topics
   **Then** `kubectl get kafkatopics -n arsipq-platform` lists created topics

5. **Given** Kafka cluster networking
   **When** applications connect
   **Then** internal bootstrap address is accessible: `arsipq-kafka-kafka-bootstrap.arsipq-platform:9092`

---

## Tasks / Subtasks

- [ ] **Task 1: Create Strimzi Operator HelmRelease** (AC: #1)
  - [ ] 1.1 Create directory structure `clusters/infra/apps/platform/strimzi-kafka/operator/`
  - [ ] 1.2 Create `helmrelease.yaml` for Strimzi Operator
  - [ ] 1.3 Create `kustomization.yaml` for operator directory
  - [ ] 1.4 Create `ks.yaml` Flux Kustomization entry point
  - [ ] 1.5 Verify operator deployment with `kubectl get deploy -n strimzi-kafka strimzi-cluster-operator`

- [ ] **Task 2: Deploy Kafka Cluster with KRaft Mode** (AC: #1, #2)
  - [ ] 2.1 Create directory `clusters/infra/apps/platform/strimzi-kafka/cluster/`
  - [ ] 2.2 Create `kafka.yaml` with KRaft-enabled Kafka CR
  - [ ] 2.3 Create `kafkanodepool-controllers.yaml` for 3 controller nodes
  - [ ] 2.4 Create `kafkanodepool-brokers.yaml` for 3 broker nodes
  - [ ] 2.5 Create `kustomization.yaml` for cluster directory
  - [ ] 2.6 Create `ks.yaml` for cluster Flux Kustomization with dependency on operator
  - [ ] 2.7 Verify cluster status with `kubectl get kafka -n arsipq-platform`

- [ ] **Task 3: Configure Network Policy** (AC: #5)
  - [ ] 3.1 Create `networkpolicy.yaml` with CiliumNetworkPolicy for Tier 2 isolation
  - [ ] 3.2 Allow ingress from `arsipq-platform` namespace applications
  - [ ] 3.3 Allow ingress from observability namespace for metrics scraping
  - [ ] 3.4 Test connectivity from within the namespace

- [ ] **Task 4: Validate Topic Creation** (AC: #3, #4)
  - [ ] 4.1 Create test KafkaTopic CR
  - [ ] 4.2 Verify topic appears in `kubectl get kafkatopics -n arsipq-platform`
  - [ ] 4.3 Delete test topic after validation

- [ ] **Task 5: Configure Monitoring Integration** (AC: related to Epic 6)
  - [ ] 5.1 Enable Kafka metrics exporter in cluster CR
  - [ ] 5.2 Create ServiceMonitor for VictoriaMetrics scraping
  - [ ] 5.3 Verify metrics appear in VictoriaMetrics

---

## Dev Notes

### Latest Version Information (December 2025)

Based on web research, the latest Strimzi version is **0.49.1**. The architecture document specifies **v0.47.0** - recommend updating to latest stable for:
- Full KRaft support with dynamic controller quorums
- Latest security patches
- Improved KafkaNodePool support

**IMPORTANT:** Confirm with user whether to use 0.47.0 (as per architecture) or upgrade to 0.49.1.

### KRaft Mode Configuration

Strimzi KRaft mode requires:
1. **Kafka CR annotations:**
   - `strimzi.io/kraft: enabled`
   - `strimzi.io/node-pools: enabled`

2. **KafkaNodePool resources** for controller and broker roles:
   - Controllers: Manage cluster metadata using Raft consensus
   - Brokers: Handle message streaming and storage
   - Can use dual-role nodes for smaller deployments (not recommended for production)

3. **Node configuration for production (3+3 pattern):**
   ```yaml
   # Controllers pool
   spec:
     replicas: 3
     roles:
       - controller
     storage:
       type: jbod
       volumes:
         - id: 0
           type: persistent-claim
           size: 10Gi
           class: ceph-block

   # Brokers pool
   spec:
     replicas: 3
     roles:
       - broker
     storage:
       type: jbod
       volumes:
         - id: 0
           type: persistent-claim
           size: 100Gi
           class: ceph-block
   ```

### Architecture Constraints

From `docs/project-context.md` and architecture document:

| Constraint | Value |
|------------|-------|
| Location | `clusters/infra/apps/platform/strimzi-kafka/` (infra cluster only) |
| Namespace | `arsipq-platform` |
| StorageClass | `ceph-block` (Rook-Ceph) |
| Bootstrap Endpoint | `arsipq-kafka-kafka-bootstrap.arsipq-platform:9092` |
| Operator Memory | < 500MB RAM (NFR32) |

### Required Dependencies

Add to `ks.yaml`:
```yaml
spec:
  dependsOn:
    - name: rook-ceph-cluster
      namespace: flux-system
```

For the cluster Kustomization, also depend on operator:
```yaml
spec:
  dependsOn:
    - name: strimzi-kafka-operator
      namespace: flux-system
```

### healthCheckExprs Pattern

From project-context.md:
```yaml
healthCheckExprs:
  - apiVersion: kafka.strimzi.io/v1beta2
    kind: Kafka
    failed: status.conditions.filter(e, e.type == 'Ready').all(e, e.status == 'False')
```

### Naming Conventions

Following project naming standards:
- HelmRelease name: `strimzi-kafka-operator`
- Kafka cluster name: `arsipq-kafka`
- Namespace: `arsipq-platform`
- NodePool names: `controllers`, `brokers`

### HelmRelease Template

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: strimzi-kafka-operator
spec:
  interval: 1h
  chartRef:
    kind: OCIRepository
    name: strimzi-kafka-operator
    namespace: flux-system
  install:
    crds: CreateReplace
    remediation:
      retries: -1  # Operators must succeed
  upgrade:
    crds: CreateReplace
    cleanupOnFail: true
    remediation:
      strategy: rollback
      retries: 3
  values:
    # Operator values
```

### Directory Structure

```
clusters/infra/apps/platform/strimzi-kafka/
├── operator/
│   ├── helmrelease.yaml      # Strimzi Operator
│   └── kustomization.yaml
├── cluster/
│   ├── kafka.yaml            # Kafka CR with KRaft annotations
│   ├── kafkanodepool-controllers.yaml
│   ├── kafkanodepool-brokers.yaml
│   ├── networkpolicy.yaml
│   └── kustomization.yaml
├── ks-operator.yaml          # Flux Kustomization for operator
└── ks-cluster.yaml           # Flux Kustomization for cluster
```

### Project Structure Notes

- **Alignment:** This app is infra-only, correctly placed in `clusters/infra/apps/platform/`
- **Namespace:** `arsipq-platform` - may need to be created via targetNamespace in Flux Kustomization
- **OCIRepository:** Need to add OCIRepository for Strimzi helm chart if not exists in `infrastructure/base/repositories/oci/`

### References

- [Source: _bmad-output/planning-artifacts/epics.md - Epic 8, Story 8.1]
- [Source: _bmad-output/planning-artifacts/architecture.md - Technology Stack, App Location Rules]
- [Source: docs/project-context.md - Flux HelmRelease Rules, healthCheckExprs Patterns]
- [Source: Strimzi Documentation](https://strimzi.io/docs/operators/latest/deploying)
- [Source: Strimzi KRaft Blog](https://strimzi.io/blog/2023/09/11/kafka-node-pools-supporting-kraft/)

---

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

---

## Story Completion Notes

Story created by BMAD create-story workflow on 2025-12-31. Ultimate context engine analysis completed - comprehensive developer guide created.
