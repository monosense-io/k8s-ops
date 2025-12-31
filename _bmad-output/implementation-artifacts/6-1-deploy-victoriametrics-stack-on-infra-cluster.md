# Story 6.1: Deploy VictoriaMetrics Stack on Infra Cluster

Status: ready-for-dev

## Story

As a platform operator,
I want VictoriaMetrics providing centralized metrics storage and alerting,
so that I have a single source for all cluster metrics with efficient resource usage.

## Acceptance Criteria

1. **AC1**: VictoriaMetrics Operator is deployed and healthy:
   - `clusters/infra/apps/observability/victoria-metrics-operator/` contains operator HelmRelease
   - Operator version v0.66.1 or latest stable
   - Operator pods running in `observability` namespace
   - CRDs installed: VMSingle, VMAgent, VMAlert, VMAlertmanager, etc.

2. **AC2**: VMSingle is deployed for metrics storage:
   - VMSingle CR deployed with 90-day retention (NFR43)
   - Storage using `ceph-block` StorageClass with appropriate size
   - Resource limits configured (total observability < 4GB RAM per NFR31)
   - Metrics queryable via VictoriaMetrics API at `/api/v1/query`

3. **AC3**: VMAgent is deployed for local metric scraping:
   - VMAgent CR deployed with ServiceMonitor/PodMonitor discovery
   - Scrapes all infra cluster targets (no remote-write, local only)
   - Discovers targets via `spec.serviceScrapeSelector` and `spec.podScrapeSelector`
   - All expected scrape targets discovered (100% coverage)

4. **AC4**: VMAlertmanager is deployed for alert routing:
   - VMAlertmanager CR deployed with persistent storage
   - Configuration via ExternalSecret (alertmanager.yaml)
   - Ready to receive alerts from VMAlert

5. **AC5**: VMAlert is deployed for alerting rules:
   - VMAlert CR deployed and connected to VMSingle
   - Alert rules loaded from ConfigMap or VMRule CRs
   - Alerts route to VMAlertmanager
   - Basic cluster health rules included (node down, pod crash looping)

6. **AC6**: Performance requirements met:
   - Query response < 2 seconds for 95th percentile (NFR3)
   - Total observability stack RAM < 4GB (NFR31)
   - VMSingle handles infra cluster metric volume without issues

7. **AC7**: Flux patterns followed correctly:
   - HelmRelease uses `helm.toolkit.fluxcd.io/v2` API version
   - Install/upgrade remediation configured per project-context.md
   - Dependencies declared via `spec.dependsOn` (rook-ceph-cluster)
   - Uses `${CLUSTER_NAME}` substitution from cluster-vars

## Tasks / Subtasks

- [ ] Task 1: Deploy VictoriaMetrics Operator (AC: #1)
  - [ ] Subtask 1.1: Create `clusters/infra/apps/observability/victoria-metrics-operator/` directory
  - [ ] Subtask 1.2: Create HelmRelease for victoria-metrics-operator chart
  - [ ] Subtask 1.3: Configure operator with appropriate resource limits
  - [ ] Subtask 1.4: Create Flux Kustomization entry point (ks.yaml)
  - [ ] Subtask 1.5: Verify CRDs installed after reconciliation

- [ ] Task 2: Deploy VMSingle for metrics storage (AC: #2, #6)
  - [ ] Subtask 2.1: Create `clusters/infra/apps/observability/vmsingle/` directory
  - [ ] Subtask 2.2: Create VMSingle CR with 90-day retention
  - [ ] Subtask 2.3: Configure storage (ceph-block, size based on expected volume)
  - [ ] Subtask 2.4: Set resource requests/limits (memory efficient)
  - [ ] Subtask 2.5: Create ks.yaml with dependency on operator
  - [ ] Subtask 2.6: Verify VMSingle pod running and accepting writes

- [ ] Task 3: Deploy VMAgent for metric collection (AC: #3)
  - [ ] Subtask 3.1: Create `clusters/infra/apps/observability/vmagent/` directory
  - [ ] Subtask 3.2: Create VMAgent CR with scrape configuration
  - [ ] Subtask 3.3: Configure serviceScrapeSelector for ServiceMonitor discovery
  - [ ] Subtask 3.4: Configure podScrapeSelector for PodMonitor discovery
  - [ ] Subtask 3.5: Point remoteWrite to local VMSingle
  - [ ] Subtask 3.6: Verify all targets discovered via VMAgent UI

- [ ] Task 4: Deploy VMAlertmanager for alert routing (AC: #4)
  - [ ] Subtask 4.1: Create `clusters/infra/apps/observability/vmalertmanager/` directory
  - [ ] Subtask 4.2: Create VMAlertmanager CR with persistent storage
  - [ ] Subtask 4.3: Create ExternalSecret for alertmanager configuration
  - [ ] Subtask 4.4: Configure notification receivers (webhook, email placeholders)
  - [ ] Subtask 4.5: Verify VMAlertmanager ready and configuration loaded

- [ ] Task 5: Deploy VMAlert for alerting rules (AC: #5)
  - [ ] Subtask 5.1: Create `clusters/infra/apps/observability/vmalert/` directory
  - [ ] Subtask 5.2: Create VMAlert CR connected to VMSingle datasource
  - [ ] Subtask 5.3: Configure VMAlertmanager as notification target
  - [ ] Subtask 5.4: Create VMRule CRs for basic cluster health alerts
  - [ ] Subtask 5.5: Verify alerts evaluating without errors

- [ ] Task 6: Integration testing and validation (AC: #1-7)
  - [ ] Subtask 6.1: Verify query API returns metrics
  - [ ] Subtask 6.2: Test alert firing and routing to alertmanager
  - [ ] Subtask 6.3: Measure query response times
  - [ ] Subtask 6.4: Verify total RAM usage < 4GB
  - [ ] Subtask 6.5: Document any tuning adjustments made

## Dev Notes

### Architecture Context

**Purpose of This Story:**
Deploy the centralized VictoriaMetrics observability stack on the infra cluster. This forms the "hub" of the hub/spoke observability architecture where:
- Infra cluster: Full stack (VMSingle, VMAgent, VMAlert, VMAlertmanager)
- Apps cluster: Lightweight agents only (VMAgent remote-write to infra)

**Hub/Spoke Observability Pattern:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     INFRA CLUSTER (Hub)                                  │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    observability namespace                           ││
│  │                                                                      ││
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────────────┐││
│  │  │  VMAgent    │──▶│  VMSingle   │◀──│ VMAlert                     │││
│  │  │  (scraper)  │   │ (storage)   │   │ (rules evaluation)          │││
│  │  │             │   │  90d retain │   │                             │││
│  │  └─────────────┘   └──────┬──────┘   └──────────────┬──────────────┘││
│  │        │                  │                         │               ││
│  │        │                  │                         ▼               ││
│  │        │                  │              ┌─────────────────────────┐││
│  │        │                  │              │   VMAlertmanager        │││
│  │        │                  │              │   (notifications)       │││
│  │        │                  │              └─────────────────────────┘││
│  │        │                  │                                         ││
│  │        │                  ▼                                         ││
│  │        │         ┌─────────────────┐                                ││
│  │        │         │ Grafana (6.4)   │  ◀── Story 6.4 (later)        ││
│  │        │         │ (dashboards)    │                                ││
│  │        │         └─────────────────┘                                ││
│  │        ▼                                                            ││
│  │  ┌─────────────────────────────────────────────────────────────────┐││
│  │  │              Scrape Targets (infra cluster)                      │││
│  │  │  - kube-state-metrics, node-exporter, kubelet                   │││
│  │  │  - Flux controllers, Rook-Ceph, CNPG, Envoy Gateway             │││
│  │  │  - cert-manager, external-secrets, cilium                       │││
│  │  └─────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
           ▲
           │ remote-write (Story 6.3)
           │
┌──────────┴──────────────────────────────────────────────────────────────┐
│                     APPS CLUSTER (Spoke)                                 │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │   VMAgent (remote-write only) ──────────────────────────────────────▶││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack Versions

| Component | Version | Chart/Image |
|-----------|---------|-------------|
| VictoriaMetrics Operator | v0.66.1 | `victoria-metrics-operator` Helm chart |
| VictoriaMetrics | v1.131.0 | Used by VMSingle/VMAgent |
| Alertmanager | Compatible | Bundled with operator |

**Source:** [VictoriaMetrics Operator Changelog](https://docs.victoriametrics.com/operator/changelog/)

### Directory Structure

```
clusters/infra/apps/observability/
├── victoria-metrics-operator/
│   ├── app/
│   │   ├── helmrelease.yaml
│   │   └── kustomization.yaml
│   └── ks.yaml
├── vmsingle/
│   ├── app/
│   │   ├── vmsingle.yaml
│   │   └── kustomization.yaml
│   └── ks.yaml
├── vmagent/
│   ├── app/
│   │   ├── vmagent.yaml
│   │   ├── scrapeconfigs/         # Optional additional scrape configs
│   │   └── kustomization.yaml
│   └── ks.yaml
├── vmalertmanager/
│   ├── app/
│   │   ├── vmalertmanager.yaml
│   │   ├── externalsecret.yaml    # alertmanager.yaml config
│   │   └── kustomization.yaml
│   └── ks.yaml
└── vmalert/
    ├── app/
    │   ├── vmalert.yaml
    │   ├── rules/                  # VMRule CRs
    │   │   ├── cluster-health.yaml
    │   │   └── kustomization.yaml
    │   └── kustomization.yaml
    └── ks.yaml
```

### VictoriaMetrics Operator HelmRelease

```yaml
# clusters/infra/apps/observability/victoria-metrics-operator/app/helmrelease.yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: victoria-metrics-operator
spec:
  interval: 1h
  chartRef:
    kind: HelmRepository
    name: victoria-metrics
    namespace: flux-system
  chart:
    spec:
      chart: victoria-metrics-operator
      version: "0.66.1"  # Pin to specific version
  install:
    crds: CreateReplace
    remediation:
      retries: 3
  upgrade:
    crds: CreateReplace
    cleanupOnFail: true
    remediation:
      strategy: rollback
      retries: 3
  values:
    operator:
      # Disable prometheus-operator CRD conversion (we don't have prometheus-operator)
      disable_prometheus_converter: false  # Keep enabled for ServiceMonitor support
      enable_converter_ownership: true
    resources:
      requests:
        cpu: 50m
        memory: 128Mi
      limits:
        memory: 256Mi
```

### VMSingle CR

```yaml
# clusters/infra/apps/observability/vmsingle/app/vmsingle.yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMSingle
metadata:
  name: vmsingle
  namespace: observability
spec:
  # Retention period - 90 days per NFR43
  retentionPeriod: "90d"

  # Storage configuration
  storage:
    storageClassName: ceph-block
    resources:
      requests:
        storage: 50Gi  # Adjust based on expected metric volume

  # Resource limits for memory efficiency
  resources:
    requests:
      cpu: 100m
      memory: 512Mi
    limits:
      memory: 2Gi  # Allow headroom but cap at 2GB

  # Extra args for performance tuning
  extraArgs:
    dedup.minScrapeInterval: 30s
    search.maxConcurrentRequests: "8"
    search.maxQueueDuration: 30s
```

### VMAgent CR

```yaml
# clusters/infra/apps/observability/vmagent/app/vmagent.yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMAgent
metadata:
  name: vmagent
  namespace: observability
spec:
  # Scrape configuration
  selectAllByDefault: false
  serviceScrapeSelector:
    matchLabels: {}  # Select all ServiceScrapes
  podScrapeSelector:
    matchLabels: {}  # Select all PodScrapes
  probeSelector:
    matchLabels: {}
  staticScrapeSelector:
    matchLabels: {}

  # Write to local VMSingle (no remote)
  remoteWrite:
    - url: http://vmsingle-vmsingle.observability.svc:8429/api/v1/write

  # Resource limits
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      memory: 512Mi

  # Extra args
  extraArgs:
    promscrape.streamParse: "true"
    promscrape.maxScrapeSize: "64MB"
```

### VMAlertmanager CR

```yaml
# clusters/infra/apps/observability/vmalertmanager/app/vmalertmanager.yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMAlertmanager
metadata:
  name: vmalertmanager
  namespace: observability
spec:
  replicaCount: 1

  # Configuration from secret
  configSecret: vmalertmanager-config

  # Persistent storage
  storage:
    storageClassName: ceph-block
    resources:
      requests:
        storage: 1Gi

  resources:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      memory: 128Mi
```

### VMAlert CR

```yaml
# clusters/infra/apps/observability/vmalert/app/vmalert.yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMAlert
metadata:
  name: vmalert
  namespace: observability
spec:
  # Data source
  datasource:
    url: http://vmsingle-vmsingle.observability.svc:8429

  # Send alerts to alertmanager
  notifiers:
    - url: http://vmalertmanager-vmalertmanager.observability.svc:9093

  # Rule selectors
  ruleSelector:
    matchLabels: {}  # Select all VMRule resources

  # Evaluation interval
  evaluationInterval: 30s

  resources:
    requests:
      cpu: 50m
      memory: 128Mi
    limits:
      memory: 256Mi
```

### Basic Alert Rules (VMRule)

```yaml
# clusters/infra/apps/observability/vmalert/app/rules/cluster-health.yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMRule
metadata:
  name: cluster-health
  namespace: observability
spec:
  groups:
    - name: cluster-health
      interval: 1m
      rules:
        - alert: NodeNotReady
          expr: kube_node_status_condition{condition="Ready",status="true"} == 0
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Node {{ $labels.node }} is not ready"
            description: "Node has been in NotReady state for more than 5 minutes"

        - alert: PodCrashLooping
          expr: rate(kube_pod_container_status_restarts_total[15m]) * 60 * 15 > 3
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Pod {{ $labels.namespace }}/{{ $labels.pod }} is crash looping"
            description: "Pod has restarted more than 3 times in 15 minutes"

        - alert: HighMemoryUsage
          expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High memory usage on {{ $labels.instance }}"
            description: "Memory usage is above 90%"

        - alert: FluxReconciliationFailure
          expr: gotk_reconcile_condition{status="False",type="Ready"} == 1
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "Flux reconciliation failing for {{ $labels.name }}"
            description: "Flux resource has been failing reconciliation for 10 minutes"
```

### ExternalSecret for Alertmanager Config

```yaml
# clusters/infra/apps/observability/vmalertmanager/app/externalsecret.yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: vmalertmanager-config
  namespace: observability
spec:
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword
  target:
    name: vmalertmanager-config
    creationPolicy: Owner
  data:
    - secretKey: alertmanager.yaml
      remoteRef:
        key: vmalertmanager-config
        property: alertmanager.yaml
```

**1Password Entry Template (alertmanager.yaml):**
```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  routes:
    - receiver: 'critical'
      match:
        severity: critical
    - receiver: 'warning'
      match:
        severity: warning

receivers:
  - name: 'default'
    # Configure webhook, email, slack, etc.
  - name: 'critical'
    # Critical notifications
  - name: 'warning'
    # Warning notifications

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'namespace']
```

### Flux Kustomization Pattern

```yaml
# clusters/infra/apps/observability/victoria-metrics-operator/ks.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name victoria-metrics-operator
  namespace: flux-system
spec:
  targetNamespace: observability
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./clusters/infra/apps/observability/victoria-metrics-operator/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: true
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  dependsOn:
    - name: rook-ceph-cluster  # Storage dependency
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

### Resource Budget Analysis

| Component | Memory Request | Memory Limit | Notes |
|-----------|---------------|--------------|-------|
| VM Operator | 128Mi | 256Mi | Lightweight controller |
| VMSingle | 512Mi | 2Gi | Main storage, needs headroom |
| VMAgent | 256Mi | 512Mi | Scraping overhead |
| VMAlertmanager | 64Mi | 128Mi | Minimal footprint |
| VMAlert | 128Mi | 256Mi | Rule evaluation |
| **Total** | **1088Mi** | **3.2Gi** | **Under 4GB limit (NFR31)** |

### Scrape Target Discovery

VMAgent discovers targets via:

1. **VMServiceScrape** - Kubernetes Service endpoints
2. **VMPodScrape** - Pod annotations
3. **VMProbe** - Blackbox probing
4. **VMStaticScrape** - Static targets

**Auto-Discovery Pattern:**
Most applications expose Prometheus metrics. The operator creates VMServiceScrape resources automatically when `prometheus.io/scrape: "true"` annotation is present.

For explicit control, create VMServiceScrape CRs:

```yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMServiceScrape
metadata:
  name: flux-controllers
  namespace: observability
spec:
  selector:
    matchLabels:
      app.kubernetes.io/part-of: flux
  namespaceSelector:
    matchNames:
      - flux-system
  endpoints:
    - port: http-prom
      path: /metrics
```

### Verification Commands

```bash
# Verify operator running
kubectl get pods -n observability -l app.kubernetes.io/name=victoria-metrics-operator

# Verify VMSingle
kubectl get vmsingle -n observability
kubectl logs -n observability -l app.kubernetes.io/name=vmsingle --tail=50

# Verify VMAgent targets
kubectl port-forward -n observability svc/vmagent-vmagent 8429:8429
# Visit http://localhost:8429/targets

# Test query API
kubectl port-forward -n observability svc/vmsingle-vmsingle 8428:8429
curl 'http://localhost:8428/api/v1/query?query=up'

# Check alert rules
kubectl get vmrule -n observability
kubectl get vmrule -n observability cluster-health -o yaml

# Verify alertmanager
kubectl get vmalertmanager -n observability
kubectl logs -n observability -l app.kubernetes.io/name=vmalertmanager
```

### Performance Tuning Notes

**Query Performance (< 2s for 95th percentile):**
- `search.maxConcurrentRequests: 8` - Limits concurrent queries
- `search.maxQueueDuration: 30s` - Timeout for queued queries
- Increase VMSingle memory if queries are slow

**Ingestion Performance:**
- `dedup.minScrapeInterval: 30s` - Deduplication window
- VMAgent memory buffer handles burst ingestion

**Storage Efficiency:**
- VictoriaMetrics uses ~70% less storage than Prometheus
- 50Gi should handle ~6 months for a small cluster
- Monitor with `vm_data_size_bytes` metric

### Anti-Patterns to Avoid

1. **DO NOT** use VMCluster for single-cluster setup - VMSingle is sufficient and simpler
2. **DO NOT** set memory limits too low - VictoriaMetrics needs memory for queries
3. **DO NOT** forget to set `retentionPeriod` - defaults may not match requirements
4. **DO NOT** skip ServiceScrape/PodScrape selectors - use empty labels `{}` to select all
5. **DO NOT** hardcode URLs - use Kubernetes service DNS names
6. **DO NOT** forget dependency on storage (rook-ceph-cluster)
7. **DO NOT** use deprecated `spec.storage` syntax - use `storage.storageClassName`

### Edge Cases

**Scenario: VMSingle OOM during large queries**
- Increase memory limit
- Add `search.maxMemoryPerQuery` arg to limit per-query memory
- Consider query timeout settings

**Scenario: VMAgent missing targets**
- Check serviceScrapeSelector/podScrapeSelector configuration
- Verify target namespace has correct labels
- Check VMServiceScrape resources created

**Scenario: Alerts not firing**
- Verify VMAlert can reach VMSingle datasource
- Check VMRule syntax (MetricsQL, not PromQL)
- Verify VMAlertmanager configuration loaded

### Dependencies

| This Story Depends On | Required For |
|-----------------------|--------------|
| Story 2.1 (Rook-Ceph) | Storage for VMSingle, VMAlertmanager |
| Story 1.4 (External Secrets) | Alertmanager config from 1Password |

| Stories That Depend On This | Reason |
|-----------------------------|--------|
| Story 6.2 (VictoriaLogs) | Same namespace, similar patterns |
| Story 6.3 (Apps Cluster Agents) | Remote-write target |
| Story 6.4 (Grafana) | Datasource |
| Story 5.4 (Multi-Cluster Validation) | VMAgent verification |

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Hub/Spoke Observability Architecture]
- [Source: _bmad-output/planning-artifacts/prd.md#Observability Architecture]
- [Source: docs/project-context.md#Observability Pattern]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.1]

### External Documentation

- [VictoriaMetrics Operator Quick Start](https://docs.victoriametrics.com/operator/quick-start/)
- [VMSingle Resource](https://docs.victoriametrics.com/operator/resources/vmsingle/)
- [VMAgent Resource](https://docs.victoriametrics.com/operator/resources/vmagent/)
- [VMAlert Resource](https://docs.victoriametrics.com/operator/resources/vmalert/)
- [VictoriaMetrics Operator Changelog](https://docs.victoriametrics.com/operator/changelog/)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
