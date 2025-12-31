# Story 2.6: Configure Resource Management Policies

Status: ready-for-dev

## Story

As a **platform operator**,
I want **namespace quotas, limit ranges, and priority classes configured for workload management**,
So that **workloads don't starve resources, critical services are prioritized during resource contention, and the home lab runs efficiently within its resource constraints**.

## Acceptance Criteria

1. **Given** a running cluster with storage and networking
   **When** resource management is configured
   **Then** `kubernetes/apps/` contains resource policies:
   - PriorityClass definitions: `system-critical`, `cluster-services`, `application` (default)
   - LimitRange template for namespaces without explicit resource settings
   - ResourceQuota template for namespace resource limits

2. **And** kube-system pods use `system-critical` priority

3. **And** infrastructure operators use `cluster-services` priority

4. **And** application pods default to `application` priority

5. **And** pods without resource requests get defaults from LimitRange

## Tasks / Subtasks

- [ ] Task 1: Create PriorityClass Definitions (AC: #1, #2, #3, #4)
  - [ ] Create `kubernetes/apps/kube-system/priority-classes/` directory
  - [ ] Create `kubernetes/apps/kube-system/priority-classes/app/priorityclass.yaml` with three classes:
    - `system-critical`: value 1000000000, globalDefault: false, preemptionPolicy: PreemptLowerPriority
    - `cluster-services`: value 100000000, globalDefault: false
    - `application`: value 0, globalDefault: true (default for all pods)
  - [ ] Create `kubernetes/apps/kube-system/priority-classes/app/kustomization.yaml`
  - [ ] Create `kubernetes/apps/kube-system/priority-classes/ks.yaml` Flux Kustomization

- [ ] Task 2: Create LimitRange Template (AC: #1, #5)
  - [ ] Create `kubernetes/apps/kube-system/resource-defaults/` directory
  - [ ] Create `kubernetes/apps/kube-system/resource-defaults/app/limitrange.yaml` with:
    - Default CPU request: 10m
    - Default CPU limit: 1000m
    - Default memory request: 64Mi
    - Default memory limit: 512Mi
    - Type: Container
  - [ ] Create `kubernetes/apps/kube-system/resource-defaults/app/kustomization.yaml`
  - [ ] Create `kubernetes/apps/kube-system/resource-defaults/ks.yaml` Flux Kustomization
  - [ ] Note: LimitRange is namespace-scoped; apply to key namespaces requiring defaults

- [ ] Task 3: Create ResourceQuota Template (AC: #1)
  - [ ] Create `kubernetes/apps/kube-system/resource-quotas/` directory
  - [ ] Create template `kubernetes/apps/kube-system/resource-quotas/app/resourcequota-template.yaml`:
    - Define CPU/Memory limits per namespace category
    - Define pod count limits
    - Define PVC count and size limits
  - [ ] Create namespace-specific quotas for high-usage namespaces (optional)
  - [ ] Create `kubernetes/apps/kube-system/resource-quotas/app/kustomization.yaml`
  - [ ] Create `kubernetes/apps/kube-system/resource-quotas/ks.yaml` Flux Kustomization

- [ ] Task 4: Configure Priority Classes for Existing Workloads (AC: #2, #3)
  - [ ] Document which namespaces/workloads use which priority class:
    - kube-system: system-critical (built-in, already configured)
    - flux-system: cluster-services
    - rook-ceph: cluster-services
    - observability: cluster-services
    - databases: cluster-services
    - All other namespaces: application (default)
  - [ ] Update HelmReleases to specify priorityClassName where needed
  - [ ] For Flux-managed apps, use postBuild substitution or values override

- [ ] Task 5: Apply LimitRange to Key Namespaces (AC: #5)
  - [ ] Determine which namespaces need LimitRange (those with ad-hoc pods)
  - [ ] Create namespace-specific LimitRange resources if different defaults needed
  - [ ] Configure via Flux Kustomization with targetNamespace

- [ ] Task 6: Update Flux Kustomization Hierarchy (AC: #1)
  - [ ] Add priority-classes to `kubernetes/apps/kustomization.yaml`
  - [ ] Add resource-defaults to `kubernetes/apps/kustomization.yaml`
  - [ ] Add resource-quotas to `kubernetes/apps/kustomization.yaml` (if implemented)
  - [ ] Ensure correct dependency ordering (priority classes before other apps)

- [ ] Task 7: Verify Resource Management
  - [ ] Deploy priority classes and verify creation
  - [ ] Verify kube-system pods have correct priority (may be pre-existing)
  - [ ] Deploy test pod without resource requests, verify LimitRange defaults apply
  - [ ] Verify application pods use `application` priority by default
  - [ ] Check operator pods (rook-ceph, CNPG, etc.) can be configured for cluster-services

- [ ] Task 8: Document and Finalize
  - [ ] Document priority class usage in runbook
  - [ ] Document LimitRange defaults and when to override
  - [ ] Update project-context.md if new patterns established

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document (architecture.md):**

1. **FRs Covered:**
   - FR30: Operator can configure namespace resource quotas and limit ranges
   - FR31: Operator can assign workloads to priority classes (system-critical, cluster-services, application)

2. **NFRs Relevant:**
   - NFR30: Control plane overhead < 2 GB RAM per controller (home lab resource constraints)
   - NFR31: Observability overhead < 4 GB RAM total (VictoriaMetrics lighter than Prometheus)
   - NFR32: Operator footprint < 500 MB RAM each (CNPG, Strimzi, etc.)

3. **Resource Efficiency Context:**
   - Home lab environment with limited resources
   - Multiple operators running (Rook-Ceph, CNPG, Strimzi, ESO, etc.)
   - Two clusters sharing infrastructure: infra (platform services) and apps (business apps)

4. **Priority Class Strategy:**
   | Priority Class | Value | Use Case | Example Workloads |
   |---------------|-------|----------|-------------------|
   | system-critical | 1000000000 | Critical system components | CoreDNS, Cilium, kube-proxy |
   | cluster-services | 100000000 | Platform operators and shared services | Rook-Ceph, CNPG, Flux, VictoriaMetrics |
   | application | 0 (default) | User applications | Odoo, n8n, custom apps |

### Project Context Rules (Critical)

**From project-context.md:**

1. **App Location Rules:**
   - Priority classes are cluster-wide resources → `kubernetes/apps/kube-system/`
   - Deployed to BOTH clusters via Flux reconciliation

2. **File Naming Standards:**
   - Use `.yaml` extension (not `.yml`)
   - Use `kustomization.yaml` for Kustomize files
   - Use `ks.yaml` for Flux Kustomization entry points

3. **Flux Kustomization Standards:**
   ```yaml
   apiVersion: kustomize.toolkit.fluxcd.io/v1
   kind: Kustomization
   metadata:
     name: &name priority-classes
     namespace: flux-system
   spec:
     targetNamespace: kube-system
     commonMetadata:
       labels:
         app.kubernetes.io/name: *name
     path: ./kubernetes/apps/kube-system/priority-classes/app
     prune: true
     sourceRef:
       kind: GitRepository
       name: k8s-ops
     wait: false
     interval: 30m
     retryInterval: 1m
     timeout: 5m
   ```

4. **Variable Substitution:**
   - Use `${VARIABLE_NAME}` syntax for cluster-specific values
   - Reference `cluster-vars` ConfigMap via `postBuild.substituteFrom`

### Resource Management Kubernetes Concepts

**PriorityClass:**
- Cluster-scoped resource (no namespace)
- Value determines scheduling priority and preemption order
- Higher value = higher priority = scheduled first, preempts lower
- `globalDefault: true` sets default for pods without explicit priorityClassName
- `preemptionPolicy: PreemptLowerPriority` allows preempting lower-priority pods

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: cluster-services
value: 100000000
globalDefault: false
preemptionPolicy: PreemptLowerPriority
description: "Priority for cluster infrastructure services like operators"
```

**LimitRange:**
- Namespace-scoped resource
- Sets default requests/limits for containers without explicit settings
- Enforces min/max constraints on resource requests
- Applied per-container, not per-pod

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: business
spec:
  limits:
    - default:
        cpu: "1000m"
        memory: "512Mi"
      defaultRequest:
        cpu: "10m"
        memory: "64Mi"
      type: Container
```

**ResourceQuota:**
- Namespace-scoped resource
- Limits aggregate resource usage within namespace
- Can limit: CPU, memory, pod count, PVC count, service count
- Prevents runaway resource consumption

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: business
spec:
  hard:
    requests.cpu: "4"
    requests.memory: "8Gi"
    limits.cpu: "8"
    limits.memory: "16Gi"
    pods: "20"
    persistentvolumeclaims: "10"
```

### Directory Structure

```
kubernetes/apps/kube-system/
├── priority-classes/
│   ├── app/
│   │   ├── priorityclass.yaml      # All 3 priority classes
│   │   └── kustomization.yaml
│   └── ks.yaml
├── resource-defaults/
│   ├── app/
│   │   ├── limitrange.yaml         # Default LimitRange
│   │   └── kustomization.yaml
│   └── ks.yaml
└── resource-quotas/                  # Optional - if implementing quotas
    ├── app/
    │   ├── resourcequota-template.yaml
    │   └── kustomization.yaml
    └── ks.yaml
```

### Resource Templates

**priority-classes/app/priorityclass.yaml:**
```yaml
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: system-critical
value: 1000000000
globalDefault: false
preemptionPolicy: PreemptLowerPriority
description: "Critical system components - CoreDNS, Cilium, CNI"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: cluster-services
value: 100000000
globalDefault: false
preemptionPolicy: PreemptLowerPriority
description: "Platform operators and shared infrastructure services"
---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: application
value: 0
globalDefault: true
preemptionPolicy: PreemptLowerPriority
description: "Default priority for application workloads"
```

**priority-classes/app/kustomization.yaml:**
```yaml
---
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - priorityclass.yaml
```

**priority-classes/ks.yaml:**
```yaml
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name priority-classes
  namespace: flux-system
spec:
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./kubernetes/apps/kube-system/priority-classes/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: false
  interval: 30m
  retryInterval: 1m
  timeout: 5m
```

**resource-defaults/app/limitrange.yaml:**
```yaml
---
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
spec:
  limits:
    - default:
        cpu: "1000m"
        memory: "512Mi"
      defaultRequest:
        cpu: "10m"
        memory: "64Mi"
      min:
        cpu: "1m"
        memory: "4Mi"
      max:
        cpu: "4000m"
        memory: "8Gi"
      type: Container
```

### Previous Story Intelligence

**From Story 2.5 (Configure Cilium LoadBalancer IP Pools):**
- Cilium BGP resources use v2 API for Cilium 1.18+
- Infrastructure resources go in `infrastructure/base/` or `kubernetes/apps/`
- Flux Kustomization hierarchy: infrastructure → apps → local

**From Story 2.4 (Deploy cert-manager with DNS-01 Validation):**
- ExternalSecret pattern for credentials established
- Flux Kustomization path format confirmed

**From Story 2.3 (Implement Zero Trust Network Policies):**
- Tier 0 namespaces (kube-system, flux-system) have unrestricted access
- Priority aligns with network tier: Tier 0 = system-critical, Tier 1 = cluster-services

**Key Learnings from Epic 2:**
- Use `.yaml` extension consistently
- Test in staging/infra first before apps cluster
- Keep infrastructure components simple and maintainable
- Document all configuration decisions

### Workload Priority Mapping

| Namespace | Priority Class | Rationale |
|-----------|---------------|-----------|
| kube-system | system-critical | Core K8s components, CNI, DNS |
| flux-system | cluster-services | GitOps controller |
| rook-ceph | cluster-services | Storage operator |
| databases | cluster-services | CNPG, Dragonfly |
| observability | cluster-services | VictoriaMetrics, Grafana |
| cert-manager | cluster-services | TLS management |
| external-secrets | cluster-services | Secret sync |
| networking | cluster-services | Envoy Gateway, external-dns |
| business | application | Odoo, n8n, user apps |
| platform | cluster-services | Strimzi, Keycloak, OpenBao |
| selfhosted | application | Harbor, Mattermost |

### LimitRange Application Strategy

**Apply LimitRange to namespaces where:**
- Ad-hoc pods might be created (debugging, jobs)
- HelmReleases don't always specify resources
- Default resource allocation is acceptable

**Skip LimitRange for namespaces where:**
- All workloads have explicit resource specifications
- Operator manages pod resources (e.g., CNPG sets PostgreSQL resources)

**Recommended namespaces for LimitRange:**
- business (user applications)
- selfhosted (self-hosted apps)
- platform (development platform services)

### ResourceQuota Considerations

**Implementation is OPTIONAL for home lab:**
- Home lab typically doesn't need hard quotas
- Quotas can prevent legitimate workloads from scheduling
- Priority classes handle resource contention better

**If implementing quotas, consider:**
- Set generous limits to avoid blocking workloads
- Focus on preventing runaway resource usage
- Apply to user-facing namespaces (business, selfhosted)

### Verification Commands

```bash
# Check PriorityClasses
kubectl get priorityclasses
kubectl describe priorityclass cluster-services

# Check LimitRanges
kubectl get limitrange -A
kubectl describe limitrange default-limits -n business

# Check ResourceQuotas
kubectl get resourcequota -A
kubectl describe resourcequota compute-quota -n business

# Verify pod priorities
kubectl get pods -A -o custom-columns='NAMESPACE:.metadata.namespace,NAME:.metadata.name,PRIORITY:.spec.priorityClassName,VALUE:.spec.priority'

# Test LimitRange defaults
kubectl run test-pod --image=nginx -n business --dry-run=client -o yaml
# Should show default resources applied

# Check actual resource allocation
kubectl top pods -A
kubectl describe nodes | grep -A5 "Allocated resources"
```

### Critical Implementation Rules

1. **Priority Class Values:**
   - system-critical: 1000000000 (billion-level for K8s system components)
   - cluster-services: 100000000 (hundred-million for operators)
   - application: 0 (default for user workloads)
   - Gap between values allows future granularity

2. **GlobalDefault Setting:**
   - Only ONE PriorityClass should have `globalDefault: true`
   - Set on `application` class so user pods get default priority
   - System components explicitly set their priority

3. **Preemption Policy:**
   - Use `PreemptLowerPriority` for all classes
   - Allows higher-priority pods to evict lower-priority when resources constrained
   - Critical for home lab with limited resources

4. **LimitRange Scope:**
   - Applies to new containers only (not retroactive)
   - Won't affect existing pods until recreation
   - Set reasonable defaults that work for most workloads

5. **Cluster-Scoped vs Namespace-Scoped:**
   - PriorityClass: Cluster-scoped (no namespace in metadata)
   - LimitRange: Namespace-scoped (requires targetNamespace)
   - ResourceQuota: Namespace-scoped (requires targetNamespace)

### Project Structure Notes

- **Location:** `kubernetes/apps/kube-system/` for cluster-wide policies
- **Deployment:** BOTH clusters via Flux reconciliation
- **Dependencies:** Priority classes should deploy early in reconciliation order

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.6: Configure Resource Management Policies]
- [Source: _bmad-output/planning-artifacts/architecture.md#Resource Efficiency (NFR30-33)]
- [Source: docs/project-context.md#Technology Stack & Versions]
- [Kubernetes PriorityClass](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/)
- [Kubernetes LimitRange](https://kubernetes.io/docs/concepts/policy/limit-range/)
- [Kubernetes ResourceQuota](https://kubernetes.io/docs/concepts/policy/resource-quotas/)

### Validation Checklist

Before marking complete, verify:
- [ ] PriorityClasses created: system-critical, cluster-services, application
- [ ] `application` priority class has `globalDefault: true`
- [ ] LimitRange created with sensible defaults
- [ ] Priority classes deploy to both clusters
- [ ] Test pod without resources gets LimitRange defaults
- [ ] Application pods use `application` priority by default
- [ ] Documentation updated with priority class usage

### Git Commit Message Format

```
feat(kube-system): configure resource management policies

- Add PriorityClasses: system-critical, cluster-services, application
- Add LimitRange with default CPU/memory for containers
- Set application priority as global default
- FR30: Configure namespace resource quotas and limit ranges
- FR31: Assign workloads to priority classes
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
