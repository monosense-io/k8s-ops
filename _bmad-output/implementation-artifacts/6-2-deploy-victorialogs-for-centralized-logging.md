# Story 6.2: Deploy VictoriaLogs for Centralized Logging

Status: ready-for-dev

## Story

As a platform operator,
I want VictoriaLogs aggregating logs from all clusters,
so that I can search and analyze logs from a single location with efficient storage and fast queries.

## Acceptance Criteria

1. **AC1**: VictoriaLogs is deployed on infra cluster:
   - `clusters/infra/apps/observability/victoria-logs/` contains VictoriaLogs deployment
   - VictoriaLogs version v1.43.1 or latest stable (helm chart v0.11.23+)
   - VictoriaLogs pod running in `observability` namespace
   - 30-day log retention configured (NFR42)

2. **AC2**: Storage properly configured:
   - Persistent storage using `ceph-block` StorageClass
   - Storage size appropriate for expected log volume (minimum 50Gi)
   - Retention configured via `retentionPeriod` (30d minimum)

3. **AC3**: Fluent-bit deployed for local log shipping on infra cluster (Talos Linux optimized):
   - `clusters/infra/apps/observability/fluent-bit/` contains Fluent-bit DaemonSet
   - Fluent-bit ships logs to local VictoriaLogs instance
   - Cluster label `infra` added to distinguish log sources
   - JSON format with proper field mapping (_msg_field, _time_field, _stream_fields)
   - **Talos-specific**: Uses CRI multiline parser for containerd logs
   - **Talos-specific**: Volume mounts for `/var/log` and containerd paths
   - **Talos-specific**: Tolerations for control plane nodes

4. **AC4**: Log ingestion endpoint accessible:
   - VictoriaLogs HTTP endpoint available at port 9428
   - `/insert/jsonline` endpoint accepting log data
   - gzip compression enabled for bandwidth efficiency

5. **AC5**: Logs are searchable:
   - VictoriaLogs query API returns log data
   - Logs searchable by namespace, pod, container
   - Cluster label filtering works correctly
   - Search response < 5 seconds for 95th percentile (NFR4)

6. **AC6**: Flux patterns followed correctly:
   - HelmRelease uses `helm.toolkit.fluxcd.io/v2` API version
   - Install/upgrade remediation configured per project-context.md
   - Dependencies declared via `spec.dependsOn` (victoria-metrics-operator, rook-ceph-cluster)
   - Uses `${CLUSTER_NAME}` substitution from cluster-vars

7. **AC7**: Resource efficiency maintained:
   - VictoriaLogs + Fluent-bit RAM usage reasonable
   - Fits within total observability budget (< 4GB per NFR31)
   - CPU usage minimal for log ingestion

## Tasks / Subtasks

- [ ] Task 1: Deploy VictoriaLogs (AC: #1, #2, #4)
  - [ ] Subtask 1.1: Create `clusters/infra/apps/observability/victoria-logs/` directory structure
  - [ ] Subtask 1.2: Create HelmRelease for victoria-logs-single chart v0.11.23+
  - [ ] Subtask 1.3: Configure 30-day retention via `retentionPeriod: 30d`
  - [ ] Subtask 1.4: Configure persistent storage with ceph-block StorageClass (50Gi+)
  - [ ] Subtask 1.5: Set resource requests/limits for memory efficiency
  - [ ] Subtask 1.6: Create Flux Kustomization (ks.yaml) with proper dependencies
  - [ ] Subtask 1.7: Verify VictoriaLogs pod running and endpoint accessible

- [ ] Task 2: Deploy Fluent-bit for infra cluster - Talos Linux Optimized (AC: #3, #4)
  - [ ] Subtask 2.1: Create `clusters/infra/apps/observability/fluent-bit/` directory structure
  - [ ] Subtask 2.2: Create HelmRelease for fluent-bit DaemonSet
  - [ ] Subtask 2.3: Configure volume mounts for Talos (`/var/log`, `/var/lib/containerd/...`)
  - [ ] Subtask 2.4: Configure CRI multiline parser for containerd logs (`multiline.parser: cri`)
  - [ ] Subtask 2.5: Configure Kubernetes filter with nest filter to lift fields
  - [ ] Subtask 2.6: Add cluster label `infra` via record_modifier filter
  - [ ] Subtask 2.7: Configure HTTP output to local VictoriaLogs with jsonline format
  - [ ] Subtask 2.8: Enable gzip compression for bandwidth efficiency
  - [ ] Subtask 2.9: Configure tolerations for control plane nodes
  - [ ] Subtask 2.10: (Optional) Configure TCP input for Talos system logs
  - [ ] Subtask 2.11: (Optional) Configure audit log collection with DAC_READ_SEARCH capability
  - [ ] Subtask 2.12: Create ks.yaml with dependency on victoria-logs
  - [ ] Subtask 2.13: Verify container logs appearing in VictoriaLogs
  - [ ] Subtask 2.14: Verify multiline logs (stack traces) appear correctly

- [ ] Task 3: Integration testing and validation (AC: #5, #6, #7)
  - [ ] Subtask 3.1: Test log queries via VictoriaLogs API
  - [ ] Subtask 3.2: Verify logs from all namespaces are collected
  - [ ] Subtask 3.3: Test filtering by cluster label, namespace, pod
  - [ ] Subtask 3.4: Measure query response times (target < 5s)
  - [ ] Subtask 3.5: Verify resource usage within budget
  - [ ] Subtask 3.6: Document any tuning adjustments made

## Dev Notes

### Architecture Context

**Purpose of This Story:**
Deploy VictoriaLogs as the centralized log storage on the infra cluster. This complements the VictoriaMetrics stack from Story 6.1 to complete the "hub" of the hub/spoke observability architecture:
- Infra cluster: VictoriaLogs + Fluent-bit (local shipping)
- Apps cluster: Fluent-bit only (remote-write to infra) - Story 6.3

**Log Flow Architecture:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       INFRA CLUSTER (Hub)                                    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    observability namespace                              │ │
│  │                                                                         │ │
│  │  ┌───────────────────────┐     ┌───────────────────────────────────┐  │ │
│  │  │     Fluent-bit        │────▶│         VictoriaLogs               │  │ │
│  │  │     (DaemonSet)       │     │         (StatefulSet)              │  │ │
│  │  │                       │     │                                    │  │ │
│  │  │  - Collects all logs  │     │  - 30-day retention                │  │ │
│  │  │  - Adds cluster=infra │     │  - LogsQL queries                  │  │ │
│  │  │  - gzip compression   │     │  - ceph-block storage              │  │ │
│  │  └───────────────────────┘     └──────────────┬────────────────────┘  │ │
│  │                                               │                        │ │
│  │                                               ▼                        │ │
│  │                                 ┌───────────────────────────────────┐  │ │
│  │                                 │    Grafana (Story 6.4)            │  │ │
│  │                                 │    VictoriaLogs datasource        │  │ │
│  │                                 └───────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Scrapes logs from ALL pods in infra cluster:                                │
│  - kube-system, flux-system, observability, databases, etc.                  │
└─────────────────────────────────────────────────────────────────────────────┘
           ▲
           │ remote-write (Story 6.3)
           │
┌──────────┴───────────────────────────────────────────────────────────────────┐
│                       APPS CLUSTER (Spoke)                                    │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │   Fluent-bit (remote-write to infra VictoriaLogs via Gateway, HTTPS)   │ │
│  │   cluster=apps label                                                    │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack Versions (Latest - December 2025)

| Component | Version | Chart Version | Notes |
|-----------|---------|---------------|-------|
| VictoriaLogs | v1.43.1 | victoria-logs-single 0.11.23 | Latest stable |
| Fluent-bit | 3.2.x | fluent-bit 0.48.x | DaemonSet with CRI parser |
| Talos Linux | v1.12.0 | N/A | Immutable OS, containerd runtime |

**Source:** [VictoriaLogs Single Changelog](https://docs.victoriametrics.com/helm/victorialogs-single/changelog/)

**Important Version Notes:**
- Chart v0.9.8+: Default PV size increased to 10Gi to prevent data loss
- Chart v0.8.0+: Vector replaced Fluent-bit as default collector (we'll use Fluent-bit explicitly)
- Chart v0.9.0+: New `.Values.server.mode` parameter (use 'statefulSet')
- Requirements: Helm v3.14+, Kubernetes 1.25+

### Talos Linux Logging Architecture (CRITICAL)

**Talos Linux has a unique logging architecture that differs from standard Kubernetes distributions:**

1. **Container Logs**: Located at `/var/log/containers/*.log` (standard K8s path)
   - Symlinks to actual logs in `/var/log/pods/`
   - Uses **containerd** runtime with **CRI log format** (NOT Docker format)
   - CRI format: `<timestamp> <stream> <P|F> <log message>`

2. **Kubernetes Audit Logs**: Located at `/var/log/audit/kube/*.log` (control plane only)
   - Talos ships with API server audit logging enabled by default
   - Written as `nobody` user - requires `DAC_READ_SEARCH` capability to read

3. **Talos System Logs**: NOT file-based - sent via TCP/UDP
   - Talos services (machined, kubelet, etc.) send logs via API
   - Must configure machine config to send to Fluent-bit TCP endpoint
   - Format: `json_lines` with fields: `msg`, `talos-level`, `talos-service`, `talos-time`

4. **Kernel Logs**: Require special kernel args
   - Must add `talos.logging.kernel=udp://...` in machine config
   - Requires system upgrade to take effect

**Log Sources Summary:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TALOS LINUX LOG SOURCES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. CONTAINER LOGS (all nodes)                                               │
│     Path: /var/log/containers/*.log                                          │
│     Format: CRI (containerd)                                                 │
│     Parser: cri or multiline.parser: cri                                     │
│                                                                              │
│  2. KUBERNETES AUDIT LOGS (control plane only)                               │
│     Path: /var/log/audit/kube/*.log                                          │
│     Format: JSON                                                             │
│     Note: Requires DAC_READ_SEARCH capability                                │
│                                                                              │
│  3. TALOS SYSTEM LOGS (optional - requires machine config)                   │
│     Protocol: TCP/UDP to Fluent-bit                                          │
│     Format: json_lines                                                       │
│     Machine config: machine.logging.destinations                             │
│                                                                              │
│  4. KERNEL LOGS (optional - requires kernel args + upgrade)                  │
│     Kernel arg: talos.logging.kernel=udp://127.0.0.1:10002/                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
clusters/infra/apps/observability/
├── victoria-logs/
│   ├── app/
│   │   ├── helmrelease.yaml
│   │   └── kustomization.yaml
│   └── ks.yaml
└── fluent-bit/
    ├── app/
    │   ├── helmrelease.yaml
    │   ├── configmap.yaml           # Optional: custom config overrides
    │   └── kustomization.yaml
    └── ks.yaml
```

### VictoriaLogs HelmRelease

```yaml
# clusters/infra/apps/observability/victoria-logs/app/helmrelease.yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: victoria-logs
spec:
  interval: 1h
  chart:
    spec:
      chart: victoria-logs-single
      version: "0.11.23"  # Pin to specific version
      sourceRef:
        kind: HelmRepository
        name: victoria-metrics
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
    server:
      # Retention - 30 days per NFR42
      retentionPeriod: 30d

      # Storage configuration
      persistentVolume:
        enabled: true
        storageClassName: ceph-block
        size: 50Gi  # Adjust based on expected log volume

      # Resource limits for efficiency
      resources:
        requests:
          cpu: 100m
          memory: 256Mi
        limits:
          memory: 1Gi

      # Deployment mode
      mode: statefulSet

      # Extra args for tuning
      extraArgs:
        - "-loggerLevel=INFO"
        - "-httpListenAddr=:9428"
```

### Fluent-bit HelmRelease (Talos Linux Optimized)

```yaml
# clusters/infra/apps/observability/fluent-bit/app/helmrelease.yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: fluent-bit
spec:
  interval: 1h
  chart:
    spec:
      chart: fluent-bit
      version: "0.48.1"  # Check for latest stable
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
    # DaemonSet configuration
    kind: DaemonSet

    # Resource limits
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
    # TALOS LINUX: Volume Mounts for Container Logs
    # ============================================================
    # Talos stores container logs at /var/log/containers/*.log
    # These are symlinks to /var/log/pods/ - must mount /var/log
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

    # ============================================================
    # TALOS LINUX: Extra Ports for System Logs (Optional)
    # ============================================================
    # If you want to collect Talos system logs, expose TCP port
    extraPorts:
      - port: 5170
        containerPort: 5170
        protocol: TCP
        name: talos-logs

    # ============================================================
    # Fluent-bit Configuration for Talos Linux
    # ============================================================
    config:
      # Service configuration with filesystem buffering
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
      # INPUTS: Container Logs + Optional Talos System Logs
      # ============================================================
      inputs: |
        # Kubernetes container logs (CRI format from containerd)
        [INPUT]
            Name              tail
            Tag               kube.*
            Path              /var/log/containers/*.log
            # CRITICAL: Use multiline CRI parser for containerd logs
            multiline.parser  cri
            DB                /var/log/flb-storage/flb_kube.db
            DB.locking        true
            Mem_Buf_Limit     5MB
            Skip_Long_Lines   On
            Refresh_Interval  10
            Rotate_Wait       30
            storage.type      filesystem
            Read_from_Head    False

        # Kubernetes API Audit logs (control plane nodes only)
        # Talos enables audit logging by default at /var/log/audit/kube/
        [INPUT]
            Name              tail
            Tag               audit.*
            Path              /var/log/audit/kube/*.log
            Parser            json
            DB                /var/log/flb-storage/flb_audit.db
            DB.locking        true
            Mem_Buf_Limit     5MB
            Skip_Long_Lines   On
            Refresh_Interval  10
            storage.type      filesystem
            Read_from_Head    False

        # Talos System Logs (requires machine config to send to this endpoint)
        # Machine config: machine.logging.destinations[].endpoint: tcp://<node-ip>:5170
        [INPUT]
            Name              tcp
            Tag               talos.*
            Listen            0.0.0.0
            Port              5170
            Format            json
            Chunk_Size        32KB
            Buffer_Size       64KB

      # ============================================================
      # CUSTOM PARSERS: CRI format for containerd (Talos)
      # ============================================================
      customParsers: |
        # CRI Parser for containerd logs (Talos Linux)
        # CRI format: <timestamp> <stream> <P|F> <log>
        # P = Partial, F = Full (end of multiline)
        [PARSER]
            Name        cri
            Format      regex
            Regex       ^(?<time>[^ ]+) (?<stream>stdout|stderr) (?<logtag>[^ ]*) (?<log>.*)$
            Time_Key    time
            Time_Format %Y-%m-%dT%H:%M:%S.%L%z

        # JSON parser for audit logs and Talos system logs
        [PARSER]
            Name        json
            Format      json
            Time_Key    time
            Time_Format %Y-%m-%dT%H:%M:%S.%LZ

      # ============================================================
      # FILTERS: Kubernetes metadata enrichment + cluster label
      # ============================================================
      filters: |
        # Kubernetes metadata enrichment for container logs
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

        # Lift kubernetes nested fields to root level for VictoriaLogs
        [FILTER]
            Name          nest
            Match         kube.*
            Operation     lift
            Nested_under  kubernetes
            Add_prefix    kubernetes_

        # Add cluster label for multi-cluster identification
        [FILTER]
            Name          record_modifier
            Match         kube.*
            Record        cluster ${CLUSTER_NAME}
            Record        log_type container

        # Add cluster label to audit logs
        [FILTER]
            Name          record_modifier
            Match         audit.*
            Record        cluster ${CLUSTER_NAME}
            Record        log_type audit

        # Process Talos system logs
        [FILTER]
            Name          record_modifier
            Match         talos.*
            Record        cluster ${CLUSTER_NAME}
            Record        log_type talos_system

      # ============================================================
      # OUTPUTS: VictoriaLogs with proper field mapping
      # ============================================================
      outputs: |
        # Container logs to VictoriaLogs
        [OUTPUT]
            Name              http
            Match             kube.*
            Host              victoria-logs.observability.svc.cluster.local
            Port              9428
            URI               /insert/jsonline?_stream_fields=stream,kubernetes_pod_name,kubernetes_namespace_name,cluster&_msg_field=log&_time_field=time
            Format            json_lines
            Json_Date_Format  iso8601
            Json_Date_Key     time
            compress          gzip
            Retry_Limit       5
            net.keepalive     on

        # Audit logs to VictoriaLogs
        [OUTPUT]
            Name              http
            Match             audit.*
            Host              victoria-logs.observability.svc.cluster.local
            Port              9428
            URI               /insert/jsonline?_stream_fields=log_type,cluster&_msg_field=requestURI&_time_field=requestReceivedTimestamp
            Format            json_lines
            Json_Date_Format  iso8601
            compress          gzip
            Retry_Limit       5

        # Talos system logs to VictoriaLogs
        [OUTPUT]
            Name              http
            Match             talos.*
            Host              victoria-logs.observability.svc.cluster.local
            Port              9428
            URI               /insert/jsonline?_stream_fields=talos-service,cluster&_msg_field=msg&_time_field=talos-time
            Format            json_lines
            Json_Date_Format  iso8601
            compress          gzip
            Retry_Limit       5

    # Pod annotations
    podAnnotations:
      reloader.stakater.com/auto: "true"

    # Pod security context for reading audit logs (written as nobody)
    podSecurityContext:
      fsGroup: 65534  # nobody group

    # Security context - need DAC_READ_SEARCH for audit logs
    securityContext:
      capabilities:
        add:
          - DAC_READ_SEARCH
      readOnlyRootFilesystem: false  # Need write for DB files
```

### Talos Machine Config for System Logs (Optional)

To collect Talos system logs (machined, kubelet, etc.), add to your Talos machine config:

```yaml
# talos/patches/logging.yaml (apply to all nodes)
machine:
  logging:
    destinations:
      - endpoint: "tcp://fluent-bit.observability.svc.cluster.local:5170"
        format: "json_lines"
        extraTags:
          node: "${HOSTNAME}"
```

**Note:** This requires Fluent-bit to be accessible from the host network. Consider using a NodePort or HostNetwork for the TCP input if needed. For initial deployment, container logs alone are sufficient.

### Fluent-bit Configuration Details (Talos Linux)

**Critical Talos Linux Considerations:**

| Aspect | Standard K8s | Talos Linux |
|--------|--------------|-------------|
| Container Runtime | Docker or containerd | containerd only |
| Log Format | Docker JSON or CRI | CRI format only |
| Parser Required | `docker` or `cri` | `cri` or `multiline.parser: cri` |
| System Logs | Files in /var/log | TCP/UDP via machine config |
| Audit Logs | Varies | `/var/log/audit/kube/*.log` |
| File Permissions | Standard | `nobody` user for audit logs |

**VictoriaLogs URI Parameters:**
- `_stream_fields=stream,kubernetes_pod_name,kubernetes_namespace_name,cluster` - Fields used to group log streams
- `_msg_field=log` - Primary log message field (maps to CRI parser's `log` field)
- `_time_field=time` - Timestamp field (maps to CRI parser's `time` field)
- `compress gzip` - 80% bandwidth reduction for remote destinations

**CRI Log Format (containerd on Talos):**
```
2025-01-15T10:30:45.123456789Z stdout F This is the actual log message
│                             │      │ └─ Log message content
│                             │      └─── P=Partial, F=Full (multiline indicator)
│                             └────────── Stream (stdout/stderr)
└──────────────────────────────────────── RFC3339Nano timestamp
```

**Kubernetes Labels Added (after nest filter lifts fields):**
- `kubernetes_namespace_name` - Namespace
- `kubernetes_pod_name` - Pod name
- `kubernetes_container_name` - Container name
- `kubernetes_host` - Node name
- `cluster` - Cluster identifier (infra/apps)
- `log_type` - Log source (container/audit/talos_system)

### Flux Kustomization Pattern

```yaml
# clusters/infra/apps/observability/victoria-logs/ks.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name victoria-logs
  namespace: flux-system
spec:
  targetNamespace: observability
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./clusters/infra/apps/observability/victoria-logs/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: true
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  dependsOn:
    - name: rook-ceph-cluster      # Storage dependency
    - name: victoria-metrics-operator  # Same namespace patterns
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

```yaml
# clusters/infra/apps/observability/fluent-bit/ks.yaml
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
  path: ./clusters/infra/apps/observability/fluent-bit/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: false
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  dependsOn:
    - name: victoria-logs  # Must have VictoriaLogs running first
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

### Resource Budget Analysis

| Component | Memory Request | Memory Limit | Notes |
|-----------|---------------|--------------|-------|
| VictoriaLogs | 256Mi | 1Gi | Log storage and queries |
| Fluent-bit (per node) | 64Mi | 128Mi | Log collection daemon |
| **Total (6 nodes)** | **~640Mi** | **~1.8Gi** | Fluent-bit on all nodes |

**Combined with Story 6.1 (VictoriaMetrics):**
- VictoriaMetrics stack: ~1.1Gi request, ~3.2Gi limit
- VictoriaLogs + Fluent-bit: ~0.6Gi request, ~1.8Gi limit
- **Total observability: ~1.7Gi request, ~5Gi limit**

Note: Limits may exceed 4GB target if all components hit limits simultaneously, but requests are well under. Consider tuning if memory pressure occurs.

### Verification Commands

```bash
# ============================================================
# VictoriaLogs Verification
# ============================================================

# Verify VictoriaLogs running
kubectl get pods -n observability -l app.kubernetes.io/name=victoria-logs
kubectl get statefulset -n observability victoria-logs

# Check VictoriaLogs logs
kubectl logs -n observability -l app.kubernetes.io/name=victoria-logs --tail=50

# Test VictoriaLogs query API
kubectl port-forward -n observability svc/victoria-logs 9428:9428
# In another terminal:
curl 'http://localhost:9428/select/logsql/query?query=*&limit=10'

# Query logs from specific namespace
curl 'http://localhost:9428/select/logsql/query?query=kubernetes_namespace_name:kube-system&limit=10'

# Query logs with cluster label
curl 'http://localhost:9428/select/logsql/query?query=cluster:infra&limit=10'

# Check ingested log streams
curl 'http://localhost:9428/select/logsql/streams?limit=100'

# Verify storage usage
kubectl exec -n observability victoria-logs-0 -- df -h /storage

# ============================================================
# Fluent-bit Verification (Talos Linux Specific)
# ============================================================

# Verify Fluent-bit DaemonSet running on all nodes
kubectl get daemonset -n observability fluent-bit
kubectl get pods -n observability -l app.kubernetes.io/name=fluent-bit -o wide

# Check Fluent-bit logs for errors (especially parser errors)
kubectl logs -n observability -l app.kubernetes.io/name=fluent-bit --tail=100 | grep -i error

# Verify volume mounts are correct (Talos paths)
kubectl exec -it $(kubectl get pods -n observability -l app.kubernetes.io/name=fluent-bit -o jsonpath='{.items[0].metadata.name}') -n observability -- ls -la /var/log/containers/

# Verify container log symlinks resolve correctly
kubectl exec -it $(kubectl get pods -n observability -l app.kubernetes.io/name=fluent-bit -o jsonpath='{.items[0].metadata.name}') -n observability -- head -5 /var/log/containers/*.log

# Check Fluent-bit metrics endpoint
kubectl port-forward -n observability svc/fluent-bit 2020:2020
curl http://localhost:2020/api/v1/metrics

# Check Fluent-bit health
curl http://localhost:2020/api/v1/health

# ============================================================
# Talos Linux Log Verification
# ============================================================

# Verify container logs exist on Talos nodes
talosctl -n <node-ip> ls /var/log/containers/

# Verify audit logs exist on control plane (Talos)
talosctl -n <control-plane-ip> ls /var/log/audit/kube/

# Check Talos system logs directly (for comparison)
talosctl -n <node-ip> logs machined --tail 20

# Verify CRI log format on Talos node
talosctl -n <node-ip> read /var/log/containers/<pod-log-file> | head -5

# ============================================================
# End-to-End Log Flow Verification
# ============================================================

# Generate test log and verify it appears in VictoriaLogs
kubectl run test-log --image=busybox --rm -it --restart=Never -- echo "TEST-LOG-$(date +%s)"
# Wait 30 seconds then query:
curl 'http://localhost:9428/select/logsql/query?query=log:TEST-LOG&limit=10'

# Verify multiline logs work (stack trace test)
kubectl run test-multiline --image=python:3.11 --rm -it --restart=Never -- python -c "raise Exception('Test multiline')" 2>&1 || true
# Query should show full traceback as single entry:
curl 'http://localhost:9428/select/logsql/query?query=kubernetes_pod_name:test-multiline&limit=10'
```

### LogsQL Query Examples

```sql
# All logs from flux-system namespace
kubernetes_namespace_name:flux-system

# Error logs only
log:error OR log:ERROR

# Logs from specific pod
kubernetes_pod_name:victoria-metrics-operator-*

# Logs from infra cluster (for multi-cluster setup)
cluster:infra

# Combined filter
kubernetes_namespace_name:observability AND log:error

# Time-range query (last hour)
_time:1h kubernetes_namespace_name:flux-system
```

### Performance Tuning Notes

**Query Performance (< 5s for 95th percentile):**
- VictoriaLogs is optimized for fast queries over large datasets
- Use specific stream fields to narrow search scope
- Avoid unbounded `*` queries on large time ranges

**Ingestion Performance:**
- gzip compression reduces network I/O by ~80%
- Fluent-bit `Mem_Buf_Limit: 5MB` handles burst ingestion
- `Retry_Limit: 5` ensures delivery during brief VictoriaLogs unavailability

**Storage Efficiency:**
- VictoriaLogs uses efficient columnar storage
- 50Gi should handle ~30 days for moderate log volume
- Monitor with disk usage and adjust as needed

### Anti-Patterns to Avoid

**General:**
1. **DO NOT** use Vector collector if Fluent-bit is already established in the environment
2. **DO NOT** skip cluster label - critical for multi-cluster log separation
3. **DO NOT** set memory limits too low on VictoriaLogs - needs headroom for queries
4. **DO NOT** forget `_stream_fields` in URI - needed for log stream organization
5. **DO NOT** use `json` format instead of `json_lines` - VictoriaLogs expects jsonline
6. **DO NOT** forget dependency on storage (rook-ceph-cluster)
7. **DO NOT** disable gzip compression for local deployment - still saves resources
8. **DO NOT** use hardcoded VictoriaLogs hostname - use Kubernetes DNS

**Talos Linux Specific:**
9. **DO NOT** use Docker parser - Talos uses containerd with CRI format only
10. **DO NOT** use `Parser: cri` for multiline logs - use `multiline.parser: cri` instead
11. **DO NOT** forget to mount `/var/log` - required for container log symlinks
12. **DO NOT** expect Talos system logs as files - they're sent via TCP/UDP
13. **DO NOT** try to read audit logs without `DAC_READ_SEARCH` capability
14. **DO NOT** assume syslog or journald exist - Talos is immutable and minimal
15. **DO NOT** forget to mount `/var/lib/containerd` for following symlinks properly

### Edge Cases

**Scenario: VictoriaLogs OOM during large queries**
- Increase memory limit
- Add query timeout settings
- Consider adding `maxConcurrentSelects` limit

**Scenario: Fluent-bit missing logs**
- Check Fluent-bit pod logs for errors
- Verify log path `/var/log/containers/*.log` is accessible
- Check Mem_Buf_Limit - increase if dropping logs

**Scenario: High disk usage**
- Reduce retention period
- Increase storage size
- Check if specific namespace is generating excessive logs
- Consider adding ignore patterns for noisy logs

**Scenario: Logs not queryable by namespace/pod**
- Verify Kubernetes filter is enabled in Fluent-bit
- Check `_stream_fields` includes kubernetes fields
- Verify labels are being added correctly

**Talos Linux Specific Scenarios:**

**Scenario: Multiline logs broken/split incorrectly**
- Ensure using `multiline.parser: cri` not `Parser: cri`
- CRI format has P/F indicator for partial/full - multiline parser handles this
- Stack traces should appear as single log entries

**Scenario: Audit logs not being collected**
- Verify Fluent-bit pod has `DAC_READ_SEARCH` capability
- Check audit logs exist: `talosctl -n <node> ls /var/log/audit/kube/`
- Audit logs only exist on control plane nodes
- Check fsGroup is set to 65534 (nobody)

**Scenario: Talos system logs not appearing**
- Verify machine config has `machine.logging.destinations` configured
- Check Fluent-bit TCP port 5170 is accessible from host network
- May need NodePort service or hostNetwork: true
- Verify with: `talosctl -n <node> logs machined --follow`

**Scenario: Container logs symlink resolution fails**
- Mount both `/var/log` and `/var/lib/containerd/...`
- Verify mounts are correct: `kubectl exec -it <fluent-bit-pod> -- ls -la /var/log/containers/`
- Container log files are symlinks to `/var/log/pods/` which symlinks to containerd

**Scenario: Logs have wrong timestamps**
- CRI format uses RFC3339Nano: `%Y-%m-%dT%H:%M:%S.%L%z`
- Ensure `Time_Format` in parser matches
- VictoriaLogs `_time_field` should reference correct field name (`time` not `date`)

### Previous Story Learnings (Story 6.1)

From VictoriaMetrics deployment:
- Use `ceph-block` StorageClass consistently
- Dependencies must include `rook-ceph-cluster`
- Operator patterns use `retries: -1` for install, regular apps use `retries: 3`
- Resource budgets are critical - stay within 4GB total observability
- Service DNS names follow pattern: `{name}.observability.svc.cluster.local`
- VMAgent/VictoriaLogs use similar scrape/collection patterns

### Project Structure Notes

**App Location Rule:**
- This is an infra-cluster-only deployment: `clusters/infra/apps/observability/`
- Apps cluster will have its own Fluent-bit (Story 6.3) that remote-writes to this VictoriaLogs

**Naming Conventions:**
- HelmRelease name: `victoria-logs`, `fluent-bit`
- Service name follows helm chart defaults
- Namespace: `observability` (same as VictoriaMetrics)

### Dependencies

| This Story Depends On | Required For |
|-----------------------|--------------|
| Story 2.1 (Rook-Ceph) | Storage for VictoriaLogs |
| Story 6.1 (VictoriaMetrics) | Same namespace, operator patterns |

| Stories That Depend On This | Reason |
|-----------------------------|--------|
| Story 6.3 (Apps Cluster Agents) | Remote-write target for apps cluster |
| Story 6.4 (Grafana) | VictoriaLogs datasource |

### HelmRepository Requirement

Ensure the VictoriaMetrics HelmRepository exists in flux-system namespace:

```yaml
# infrastructure/base/repositories/helm/victoria-metrics.yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: victoria-metrics
  namespace: flux-system
spec:
  interval: 1h
  url: https://victoriametrics.github.io/helm-charts/
```

And the Fluent HelmRepository:

```yaml
# infrastructure/base/repositories/helm/fluent.yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: HelmRepository
metadata:
  name: fluent
  namespace: flux-system
spec:
  interval: 1h
  url: https://fluent.github.io/helm-charts
```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Hub/Spoke Observability Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Observability Component Locations]
- [Source: _bmad-output/planning-artifacts/prd.md#FR42 - VictoriaLogs log queries]
- [Source: _bmad-output/planning-artifacts/prd.md#FR49 - Fluent-bit log collection]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR4 - VictoriaLogs search response < 5 seconds]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR42 - Log retention 30 days minimum]
- [Source: docs/project-context.md#Observability Pattern]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.2]
- [Source: _bmad-output/implementation-artifacts/6-1-deploy-victoriametrics-stack-on-infra-cluster.md]

### External Documentation

**VictoriaLogs:**
- [VictoriaLogs Single Helm Chart](https://docs.victoriametrics.com/helm/victorialogs-single/)
- [VictoriaLogs Quick Start](https://docs.victoriametrics.com/victorialogs/quickstart/)
- [VictoriaLogs Fluent-bit Integration](https://docs.victoriametrics.com/victorialogs/data-ingestion/fluentbit/)
- [VictoriaLogs Query Language (LogsQL)](https://docs.victoriametrics.com/victorialogs/querying/)

**Fluent-bit:**
- [Fluent-bit Helm Chart](https://github.com/fluent/helm-charts/tree/main/charts/fluent-bit)
- [Fluent-bit Kubernetes Installation](https://docs.fluentbit.io/manual/installation/kubernetes)
- [Fluent-bit CRI Parser](https://docs.fluentbit.io/manual/pipeline/parsers/configuring-parser)
- [Parsing CRI JSON logs with Fluent Bit (Microsoft)](https://github.com/microsoft/fluentbit-containerd-cri-o-json-log)

**Talos Linux Logging:**
- [Talos Linux Logging Configuration](https://www.talos.dev/v1.11/talos-guides/configuration/logging/)
- [Talos Linux System Logs with VictoriaLogs (ITNEXT)](https://itnext.io/kubernetes-monitoring-a-complete-solution-part-9-talos-linux-system-logs-with-victorialogs-and-65c1f1e44a23)
- [Pi Kubernetes Cluster - Fluent-bit Setup](https://picluster.ricsanfre.com/docs/fluentbit/)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
