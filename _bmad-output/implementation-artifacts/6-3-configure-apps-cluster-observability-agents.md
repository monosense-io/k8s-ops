# Story 6.3: Configure Apps Cluster Observability Agents

Status: ready-for-dev

## Story

As a platform operator,
I want apps cluster metrics and logs forwarded to infra cluster,
so that I have unified cross-cluster visibility from a single observability hub.

## Acceptance Criteria

1. **AC1**: VMAgent deployed on apps cluster with remote-write to infra:
   - `clusters/apps/apps/observability/vmagent/` contains VMAgent deployment
   - Remote-write configured to infra cluster VictoriaMetrics
   - ServiceMonitor/PodMonitor discovery enabled for local scraping
   - Memory buffer configured for transient infra cluster unavailability
   - All apps cluster scrape targets discovered

2. **AC2**: Fluent-bit deployed on apps cluster with remote-write to infra:
   - `clusters/apps/apps/observability/fluent-bit/` contains Fluent-bit DaemonSet
   - Remote-write to infra cluster VictoriaLogs via Gateway (HTTPS)
   - Cluster label `apps` added to all logs
   - gzip compression enabled for bandwidth efficiency
   - Talos-specific configuration (CRI parser, volume mounts, tolerations)

3. **AC3**: Cross-cluster connectivity verified:
   - Apps cluster VMAgent successfully writes metrics to infra VictoriaMetrics
   - Apps cluster Fluent-bit successfully writes logs to infra VictoriaLogs
   - Apps cluster metrics appear in infra cluster metric queries
   - Apps cluster logs appear in infra VictoriaLogs searches with `cluster:apps` label

4. **AC4**: High availability and buffering:
   - VMAgent buffers metrics on disk during infra unavailability
   - Fluent-bit buffers logs during infra unavailability
   - No data loss during brief cross-cluster network issues
   - Recovery automatic when connectivity restored

5. **AC5**: Flux patterns followed correctly:
   - HelmRelease uses `helm.toolkit.fluxcd.io/v2` API version
   - Install/upgrade remediation configured per project-context.md
   - Dependencies declared via `spec.dependsOn`
   - Uses `${CLUSTER_NAME}` substitution from cluster-vars

6. **AC6**: Resource efficiency maintained:
   - VMAgent + Fluent-bit combined RAM reasonable on each node
   - Minimal CPU overhead for collection and forwarding
   - Network bandwidth optimized with compression

## Tasks / Subtasks

- [ ] Task 1: Deploy VMAgent on apps cluster (AC: #1, #3, #4)
  - [ ] Subtask 1.1: Create `clusters/apps/apps/observability/vmagent/` directory structure
  - [ ] Subtask 1.2: Create VMAgent CR with remote-write to infra VictoriaMetrics
  - [ ] Subtask 1.3: Configure remoteWrite URL: `http://vmsingle-vmsingle.observability.svc.infra.local:8429/api/v1/write`
  - [ ] Subtask 1.4: Configure serviceScrapeSelector for local target discovery
  - [ ] Subtask 1.5: Configure podScrapeSelector for PodMonitor discovery
  - [ ] Subtask 1.6: Configure disk-based buffering (`maxDiskUsagePerURL`)
  - [ ] Subtask 1.7: Add external label `cluster: apps` to all metrics
  - [ ] Subtask 1.8: Create ks.yaml with dependency on victoria-metrics-operator
  - [ ] Subtask 1.9: Verify remote-write success via VMAgent logs

- [ ] Task 2: Deploy Fluent-bit on apps cluster - Talos Linux Optimized (AC: #2, #3, #4)
  - [ ] Subtask 2.1: Create `clusters/apps/apps/observability/fluent-bit/` directory structure
  - [ ] Subtask 2.2: Create HelmRelease for Fluent-bit DaemonSet
  - [ ] Subtask 2.3: Configure volume mounts for Talos (`/var/log`, `/var/lib/containerd/...`)
  - [ ] Subtask 2.4: Configure CRI multiline parser for containerd logs
  - [ ] Subtask 2.5: Add cluster label `apps` via record_modifier filter
  - [ ] Subtask 2.6: Configure HTTP output to infra VictoriaLogs via Gateway (HTTPS)
  - [ ] Subtask 2.7: Enable gzip compression
  - [ ] Subtask 2.8: Configure filesystem-based buffering
  - [ ] Subtask 2.9: Configure tolerations for all nodes including control plane
  - [ ] Subtask 2.10: Create ks.yaml with appropriate dependencies
  - [ ] Subtask 2.11: Verify logs appearing in infra VictoriaLogs with cluster:apps label

- [ ] Task 3: Integration testing and validation (AC: #3, #5, #6)
  - [ ] Subtask 3.1: Verify apps cluster metrics queryable from infra cluster
  - [ ] Subtask 3.2: Verify apps cluster logs searchable from infra VictoriaLogs
  - [ ] Subtask 3.3: Test failover by temporarily blocking infra access
  - [ ] Subtask 3.4: Verify data recovery after connectivity restored
  - [ ] Subtask 3.5: Verify resource usage within acceptable limits
  - [ ] Subtask 3.6: Document any tuning adjustments made

## Dev Notes

### Architecture Context

**Purpose of This Story:**
Configure observability agents on the apps cluster to forward metrics and logs to the centralized observability stack on the infra cluster. This completes the "spoke" of the hub/spoke observability architecture:
- Infra cluster (Hub): Full VictoriaMetrics + VictoriaLogs stack (Story 6.1, 6.2)
- Apps cluster (Spoke): VMAgent + Fluent-bit agents forwarding to hub (This Story)

**Hub/Spoke Observability Architecture:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       INFRA CLUSTER (Hub) - Stories 6.1, 6.2                 │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    observability namespace                              │ │
│  │                                                                         │ │
│  │  ┌─────────────────────────┐    ┌─────────────────────────────────────┐│ │
│  │  │   VictoriaMetrics       │    │        VictoriaLogs                 ││ │
│  │  │   (VMSingle)            │    │        (StatefulSet)                ││ │
│  │  │                         │    │                                     ││ │
│  │  │  - 90-day retention     │    │  - 30-day retention                 ││ │
│  │  │  - Receives remote-write│    │  - Receives remote-write            ││ │
│  │  │  - Grafana datasource   │    │  - LogsQL queries                   ││ │
│  │  │                         │    │                                     ││ │
│  │  │  Endpoint:              │    │  Endpoint:                          ││ │
│  │  │  vmsingle-vmsingle:8429 │    │  victoria-logs:9428                 ││ │
│  │  └────────────┬────────────┘    └────────────┬────────────────────────┘│ │
│  │               │                              │                          │ │
│  └───────────────┼──────────────────────────────┼──────────────────────────┘ │
│                  │                              │                            │
│  ┌───────────────┴──────────────────────────────┴──────────────────────────┐ │
│  │              Envoy Gateway (envoy-external)                              │ │
│  │              - TLS termination for external access                       │ │
│  │              - HTTPS endpoint for cross-cluster access                   │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                               ▲                  ▲
                               │ remote-write     │ remote-write
                               │ (metrics)        │ (logs)
                               │                  │
┌──────────────────────────────┴──────────────────┴────────────────────────────┐
│                       APPS CLUSTER (Spoke) - This Story                       │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    observability namespace                               │ │
│  │                                                                          │ │
│  │  ┌─────────────────────────┐    ┌─────────────────────────────────────┐ │ │
│  │  │       VMAgent           │    │         Fluent-bit                  │ │ │
│  │  │                         │    │         (DaemonSet)                 │ │ │
│  │  │  - Scrapes local targets│    │                                     │ │ │
│  │  │  - Remote-write to infra│    │  - Collects container logs         │ │ │
│  │  │  - Disk buffering       │    │  - Adds cluster=apps label         │ │ │
│  │  │  - external_labels:     │    │  - Remote-write to infra           │ │ │
│  │  │      cluster: apps      │    │  - gzip compression                │ │ │
│  │  └─────────────────────────┘    └─────────────────────────────────────┘ │ │
│  │                                                                          │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  Scrapes metrics from ALL pods in apps cluster:                               │
│  - business, databases, flux-system, kube-system, etc.                        │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Critical Cross-Cluster Connectivity

**Network Path for Remote-Write:**

The apps cluster agents need to reach infra cluster services. There are two approaches:

**Option A: Direct Service Access (Recommended for Same Network)**
If both clusters are on the same network (10.25.11.0/24 and 10.25.13.0/24):
- VMAgent → `http://10.25.11.x:8429/api/v1/write` (VictoriaMetrics LoadBalancer IP)
- Fluent-bit → `http://10.25.11.x:9428/insert/jsonline` (VictoriaLogs LoadBalancer IP)

**Option B: Via Envoy Gateway (HTTPS, More Secure)**
If using Envoy Gateway with internal HTTPRoutes:
- VMAgent → `https://vmsingle.monosense.dev/api/v1/write`
- Fluent-bit → `https://vlogs.monosense.dev/insert/jsonline`

**IMPORTANT:** Per architecture.md, the apps cluster uses domain `monosense.io` and infra cluster uses `monosense.dev`. Cross-cluster access should use infra cluster's internal Gateway or LoadBalancer IPs.

### Technology Stack Versions

| Component | Version | Source |
|-----------|---------|--------|
| VictoriaMetrics Operator | v0.66.1 | Same as infra cluster (Story 6.1) |
| VMAgent | v1.131.0 | Via operator |
| Fluent-bit | 3.2.x | Helm chart 0.48.x |
| Talos Linux | v1.12.0 | Same as infra cluster |

### Directory Structure

```
clusters/apps/apps/observability/
├── vmagent/
│   ├── app/
│   │   ├── vmagent.yaml           # VMAgent CR
│   │   └── kustomization.yaml
│   └── ks.yaml
└── fluent-bit/
    ├── app/
    │   ├── helmrelease.yaml
    │   └── kustomization.yaml
    └── ks.yaml
```

### VMAgent CR (Apps Cluster - Remote-Write)

```yaml
# clusters/apps/apps/observability/vmagent/app/vmagent.yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMAgent
metadata:
  name: vmagent
  namespace: observability
spec:
  # Scrape configuration - discover all local targets
  selectAllByDefault: false
  serviceScrapeSelector:
    matchLabels: {}  # Select all ServiceScrapes
  podScrapeSelector:
    matchLabels: {}  # Select all PodScrapes
  probeSelector:
    matchLabels: {}
  staticScrapeSelector:
    matchLabels: {}

  # CRITICAL: Remote-write to INFRA cluster VictoriaMetrics
  # Use LoadBalancer IP or internal Gateway endpoint
  remoteWrite:
    - url: http://10.25.11.XX:8429/api/v1/write  # Replace with actual infra VictoriaMetrics LB IP
      # Or use: https://vmsingle.monosense.dev/api/v1/write via Gateway

  # Add cluster label to distinguish from infra metrics
  externalLabels:
    cluster: apps

  # Disk-based buffering for resilience during infra unavailability
  extraArgs:
    promscrape.streamParse: "true"
    promscrape.maxScrapeSize: "64MB"
    remoteWrite.maxDiskUsagePerURL: "1GB"  # Buffer up to 1GB on disk
    remoteWrite.queues: "4"
    remoteWrite.showURL: "true"

  # Resource limits
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      memory: 512Mi
```

**Key Differences from Infra Cluster VMAgent:**
- `remoteWrite.url` points to INFRA cluster (not local VMSingle)
- `externalLabels: cluster: apps` added to identify source
- `remoteWrite.maxDiskUsagePerURL` for cross-cluster resilience

### Fluent-bit HelmRelease (Apps Cluster - Remote-Write)

```yaml
# clusters/apps/apps/observability/fluent-bit/app/helmrelease.yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: fluent-bit
spec:
  interval: 1h
  chart:
    spec:
      chart: fluent-bit
      version: "0.48.1"
      sourceRef:
        kind: HelmRepository
        name: fluent
        namespace: flux-system
  install:
    remediation:
      retries: 3
  upgrade:
    cleanupOnFail: true
    remediation:
      strategy: rollback
      retries: 3
  values:
    kind: DaemonSet

    resources:
      requests:
        cpu: 50m
        memory: 64Mi
      limits:
        memory: 128Mi

    # Tolerations to run on ALL nodes including control plane (Talos)
    tolerations:
      - operator: Exists
        effect: NoSchedule

    # ============================================================
    # TALOS LINUX: Volume Mounts (same as infra cluster)
    # ============================================================
    daemonSetVolumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibcontainers
        hostPath:
          path: /var/lib/containerd/io.containerd.grpc.v1.cri/containers
          type: DirectoryOrCreate
      - name: machine-id
        hostPath:
          path: /etc/machine-id
          type: File
      # Filesystem buffer storage
      - name: flb-storage
        emptyDir: {}

    daemonSetVolumeMounts:
      - name: varlog
        mountPath: /var/log
        readOnly: true
      - name: varlibcontainers
        mountPath: /var/lib/containerd/io.containerd.grpc.v1.cri/containers
        readOnly: true
      - name: machine-id
        mountPath: /etc/machine-id
        readOnly: true
      - name: flb-storage
        mountPath: /var/log/flb-storage

    # ============================================================
    # Fluent-bit Configuration for Apps Cluster (Remote-Write)
    # ============================================================
    config:
      service: |
        [SERVICE]
            Daemon          Off
            Flush           1
            Log_Level       info
            Parsers_File    /fluent-bit/etc/parsers.conf
            Parsers_File    /fluent-bit/etc/conf/custom_parsers.conf
            HTTP_Server     On
            HTTP_Listen     0.0.0.0
            HTTP_Port       2020
            Health_Check    On
            storage.path    /var/log/flb-storage/
            storage.sync    normal
            storage.checksum off
            storage.backlog.mem_limit 5M

      # ============================================================
      # INPUTS: Container Logs (same as infra cluster)
      # ============================================================
      inputs: |
        [INPUT]
            Name              tail
            Tag               kube.*
            Path              /var/log/containers/*.log
            multiline.parser  cri
            DB                /var/log/flb-storage/flb_kube.db
            DB.locking        true
            Mem_Buf_Limit     5MB
            Skip_Long_Lines   On
            Refresh_Interval  10
            Rotate_Wait       30
            storage.type      filesystem
            Read_from_Head    False

      customParsers: |
        [PARSER]
            Name        cri
            Format      regex
            Regex       ^(?<time>[^ ]+) (?<stream>stdout|stderr) (?<logtag>[^ ]*) (?<log>.*)$
            Time_Key    time
            Time_Format %Y-%m-%dT%H:%M:%S.%L%z

      # ============================================================
      # FILTERS: Kubernetes metadata + APPS cluster label
      # ============================================================
      filters: |
        [FILTER]
            Name                kubernetes
            Match               kube.*
            Kube_URL            https://kubernetes.default.svc:443
            Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
            Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
            Kube_Tag_Prefix     kube.var.log.containers.
            Merge_Log           On
            Merge_Log_Key       log_processed
            Keep_Log            Off
            K8S-Logging.Parser  On
            K8S-Logging.Exclude Off
            Buffer_Size         512KB
            Annotations         Off
            Labels              On

        [FILTER]
            Name          nest
            Match         kube.*
            Operation     lift
            Nested_under  kubernetes
            Add_prefix    kubernetes_

        # CRITICAL: Add cluster=apps label for multi-cluster identification
        [FILTER]
            Name          record_modifier
            Match         kube.*
            Record        cluster apps
            Record        log_type container

      # ============================================================
      # OUTPUTS: Remote-write to INFRA cluster VictoriaLogs
      # ============================================================
      outputs: |
        [OUTPUT]
            Name              http
            Match             kube.*
            # CRITICAL: Remote-write to INFRA cluster VictoriaLogs
            Host              10.25.11.XX  # Replace with infra VictoriaLogs LB IP
            # Or use Gateway: Host victoria-logs.monosense.dev, Port 443, tls on
            Port              9428
            URI               /insert/jsonline?_stream_fields=stream,kubernetes_pod_name,kubernetes_namespace_name,cluster&_msg_field=log&_time_field=time
            Format            json_lines
            Json_Date_Format  iso8601
            Json_Date_Key     time
            compress          gzip
            Retry_Limit       10
            net.keepalive     on
            # Buffering for cross-cluster resilience
            storage.total_limit_size  512M

    podAnnotations:
      reloader.stakater.com/auto: "true"
```

**Key Differences from Infra Cluster Fluent-bit:**
- `Host` points to INFRA cluster VictoriaLogs (not localhost)
- `cluster: apps` label added (not `infra`)
- `Retry_Limit: 10` (higher for cross-cluster reliability)
- `storage.total_limit_size: 512M` for buffering during outages

### Flux Kustomization Pattern

```yaml
# clusters/apps/apps/observability/vmagent/ks.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name vmagent
  namespace: flux-system
spec:
  targetNamespace: observability
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./clusters/apps/apps/observability/vmagent/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: true
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  dependsOn:
    - name: victoria-metrics-operator  # Operator must be installed first
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

```yaml
# clusters/apps/apps/observability/fluent-bit/ks.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name fluent-bit
  namespace: flux-system
spec:
  targetNamespace: observability
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./clusters/apps/apps/observability/fluent-bit/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: false
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  dependsOn:
    - name: vmagent  # Deploy after VMAgent
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

### Determining Infra Cluster Endpoints

**CRITICAL: You must determine the actual infra cluster endpoints before deployment.**

**Option 1: LoadBalancer IPs (Simplest for Same Network)**
```bash
# From infra cluster context
kubectl --context infra get svc -n observability vmsingle-vmsingle -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
kubectl --context infra get svc -n observability victoria-logs -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

**Option 2: ClusterIP with Direct Pod Network Access**
If using Cilium Cluster Mesh (future) or VPN between clusters.

**Option 3: Envoy Gateway HTTPRoute (HTTPS)**
Create internal HTTPRoutes on infra cluster for cross-cluster access:
```yaml
# clusters/infra/apps/observability/httproutes/internal-vmsingle.yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: vmsingle-internal
  namespace: observability
spec:
  parentRefs:
    - name: envoy-internal
      namespace: networking
  hostnames:
    - "vmsingle.internal.monosense.dev"
  rules:
    - backendRefs:
        - name: vmsingle-vmsingle
          port: 8429
```

### Resource Budget Analysis

| Component | Memory Request | Memory Limit | Notes |
|-----------|---------------|--------------|-------|
| VMAgent (apps) | 256Mi | 512Mi | Scraping + remote-write buffer |
| Fluent-bit (per node, 6 nodes) | 64Mi x 6 = 384Mi | 128Mi x 6 = 768Mi | DaemonSet |
| **Total (apps cluster)** | **~640Mi** | **~1.3Gi** | Reasonable for agent-only |

### Verification Commands

```bash
# ============================================================
# VMAgent Verification (Apps Cluster)
# ============================================================

# Verify VMAgent running
kubectl --context apps get pods -n observability -l app.kubernetes.io/name=vmagent

# Check VMAgent logs for remote-write success
kubectl --context apps logs -n observability -l app.kubernetes.io/name=vmagent --tail=50 | grep -E "(remote|write|success|error)"

# Verify targets discovered
kubectl --context apps port-forward -n observability svc/vmagent-vmagent 8429:8429
curl http://localhost:8429/targets

# Verify remote-write metrics
curl http://localhost:8429/api/v1/status/remotewrite

# ============================================================
# Fluent-bit Verification (Apps Cluster)
# ============================================================

# Verify Fluent-bit DaemonSet running on all nodes
kubectl --context apps get daemonset -n observability fluent-bit
kubectl --context apps get pods -n observability -l app.kubernetes.io/name=fluent-bit -o wide

# Check Fluent-bit logs for errors
kubectl --context apps logs -n observability -l app.kubernetes.io/name=fluent-bit --tail=100 | grep -i error

# ============================================================
# Cross-Cluster Verification (From Infra Cluster)
# ============================================================

# Query metrics from apps cluster
kubectl --context infra port-forward -n observability svc/vmsingle-vmsingle 8428:8429
curl 'http://localhost:8428/api/v1/query?query=up{cluster="apps"}'

# Query logs from apps cluster
kubectl --context infra port-forward -n observability svc/victoria-logs 9428:9428
curl 'http://localhost:9428/select/logsql/query?query=cluster:apps&limit=10'

# Verify both clusters visible
curl 'http://localhost:8428/api/v1/label/cluster/values'
# Should return: ["apps", "infra"]
```

### Anti-Patterns to Avoid

1. **DO NOT** use localhost or 127.0.0.1 for remote-write endpoints - must point to infra cluster
2. **DO NOT** forget to add `cluster: apps` external label/record - critical for multi-cluster queries
3. **DO NOT** skip disk buffering configuration - cross-cluster connectivity can be unreliable
4. **DO NOT** use same endpoints as infra cluster - these agents WRITE to infra, not local
5. **DO NOT** forget to verify actual infra cluster IPs/hostnames before deployment
6. **DO NOT** use HTTPS without proper TLS configuration if going through Gateway
7. **DO NOT** set buffer sizes too small - cross-cluster needs more buffering than local
8. **DO NOT** forget tolerations - must run on ALL nodes including control plane

### Edge Cases

**Scenario: Infra cluster temporarily unavailable**
- VMAgent will buffer metrics to disk (up to 1GB configured)
- Fluent-bit will buffer logs (up to 512MB configured)
- Data will automatically flush when connectivity restored
- Monitor buffer usage via VMAgent/Fluent-bit metrics

**Scenario: Network latency between clusters**
- Increase `Retry_Limit` for Fluent-bit
- Consider gzip compression (already enabled)
- Monitor for write latency in VMAgent metrics

**Scenario: Apps cluster metrics not appearing in Grafana**
- Verify remote-write URL is correct
- Check VMAgent logs for errors
- Verify `cluster=apps` label is being added
- Test network connectivity from apps cluster to infra endpoint

**Scenario: Logs missing cluster label**
- Verify record_modifier filter is applied
- Check Fluent-bit config for proper filter order
- Verify `_stream_fields` includes `cluster` parameter

### Dependencies

| This Story Depends On | Required For |
|-----------------------|--------------|
| Story 5.1 (Bootstrap Apps Cluster) | Apps cluster must be running |
| Story 6.1 (VictoriaMetrics on Infra) | Remote-write target for metrics |
| Story 6.2 (VictoriaLogs on Infra) | Remote-write target for logs |
| VictoriaMetrics Operator on Apps | VMAgent CRD availability |

| Stories That Depend On This | Reason |
|-----------------------------|--------|
| Story 6.4 (Grafana Dashboards) | Multi-cluster data for dashboards |
| Story 5.4 (Multi-Cluster Validation) | Cross-cluster observability verification |

### Previous Story Learnings (Stories 6.1, 6.2)

From VictoriaMetrics and VictoriaLogs deployment:
- Use consistent namespace `observability`
- VMAgent CR follows same pattern but with different `remoteWrite` target
- Fluent-bit Talos configuration is well-documented and tested
- CRI multiline parser is CRITICAL for Talos containerd logs
- Volume mounts must include both `/var/log` and `/var/lib/containerd/...`
- Tolerations `operator: Exists` ensures running on all nodes
- gzip compression provides ~80% bandwidth savings

### Project Structure Alignment

**App Location Rule Compliance:**
- This is an apps-cluster-only deployment: `clusters/apps/apps/observability/`
- NOT shared (infra has different config - local vs remote-write)
- Parallel structure to infra cluster observability components

**Naming Conventions:**
- HelmRelease/CR name: `vmagent`, `fluent-bit`
- Namespace: `observability` (same as infra cluster)
- Cluster label value: `apps` (matches cluster-vars `${CLUSTER_NAME}`)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Hub/Spoke Observability Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Observability Component Locations]
- [Source: _bmad-output/planning-artifacts/prd.md#FR41-FR51 Observability Requirements]
- [Source: docs/project-context.md#Observability Pattern]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.3]
- [Source: _bmad-output/implementation-artifacts/6-1-deploy-victoriametrics-stack-on-infra-cluster.md]
- [Source: _bmad-output/implementation-artifacts/6-2-deploy-victorialogs-for-centralized-logging.md]

### External Documentation

**VMAgent Remote-Write:**
- [VictoriaMetrics vmagent Documentation](https://docs.victoriametrics.com/victoriametrics/vmagent/)
- [VMAgent Kubernetes Operator Resource](https://docs.victoriametrics.com/operator/resources/vmagent/)
- [VictoriaMetrics Data Ingestion](https://docs.victoriametrics.com/victoriametrics/data-ingestion/vmagent/)

**Fluent-bit Remote-Write:**
- [VictoriaLogs Fluent-bit Integration](https://docs.victoriametrics.com/victorialogs/data-ingestion/fluentbit/)
- [Fluent-bit HTTP Output](https://docs.fluentbit.io/manual/pipeline/outputs/http)
- [Fluent-bit Prometheus Remote Write](https://docs.fluentbit.io/manual/data-pipeline/outputs/prometheus-remote-write)

**Cross-Cluster:**
- [VictoriaMetrics Cluster Version](https://docs.victoriametrics.com/victoriametrics/cluster-victoriametrics/)
- [VictoriaLogs Cluster](https://docs.victoriametrics.com/victorialogs/cluster/)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
