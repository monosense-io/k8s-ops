# Story 6.5: Configure External-DNS and Alerting

Status: ready-for-dev

## Story

As a platform operator,
I want automatic DNS records and alert notifications,
so that services are discoverable and I'm notified of issues promptly.

## Acceptance Criteria

1. **AC1**: External-DNS deployed with dual provider configuration:
   - `kubernetes/apps/networking/external-dns/` contains complete deployment (shared across clusters)
   - External-DNS v0.19+ (or latest stable) via HelmRelease
   - Cloudflare provider for external DNS (`*.monosense.dev`, `*.monosense.io`)
   - RFC2136 (bind9) provider for internal DNS resolution
   - HTTPRoute and Gateway resources trigger automatic DNS record creation
   - DNS records created within 60 seconds of HTTPRoute creation (NFR36)

2. **AC2**: VMAlertmanager notification channels configured:
   - VMAlertmanager deployed as part of VictoriaMetrics stack (Story 6.1)
   - Notification channels configured: webhook, email (optional)
   - Alert routing configured based on severity labels
   - Test alert triggers notification delivery within 1 minute (NFR41)
   - High-availability with 2+ replicas using gossip protocol

3. **AC3**: VMAlert rules deployed for core platform alerting:
   - Alert rules migrated from any existing Prometheus rules to MetricsQL
   - Core alert categories: Node health, Pod failures, Storage issues, Flux reconciliation
   - Alert rules evaluating without errors
   - vmalert connected to VMAlertmanager for alert routing

4. **AC4**: Cloudflared tunnel deployed for secure external access:
   - `kubernetes/apps/networking/cloudflared/` contains deployment (shared OR per-cluster)
   - Infra cluster: tunnel to `monosense.dev` → `envoy-external`
   - Apps cluster: tunnel to `monosense.io` → `envoy-gateway-external`
   - QUIC transport enabled, post-quantum encryption, 2 replicas
   - Tunnel credentials via ExternalSecret (1Password)

5. **AC5**: Flux patterns and security:
   - All deployments use `helm.toolkit.fluxcd.io/v2` API version
   - Install/upgrade remediation configured per project-context.md
   - ExternalSecrets for all credentials (Cloudflare API, tunnel tokens)
   - CiliumNetworkPolicy for Tier 2 security
   - Uses `${CLUSTER_DOMAIN}` substitution from cluster-vars

## Tasks / Subtasks

- [ ] Task 1: Deploy External-DNS with dual providers (AC: #1)
  - [ ] Subtask 1.1: Create `kubernetes/apps/networking/external-dns/` directory structure
  - [ ] Subtask 1.2: Create HelmRelease for external-dns with Cloudflare provider
  - [ ] Subtask 1.3: Configure RFC2136 provider for bind9 internal DNS
  - [ ] Subtask 1.4: Create ExternalSecret for Cloudflare API credentials
  - [ ] Subtask 1.5: Configure source filters for Gateway API (HTTPRoute, Gateway)
  - [ ] Subtask 1.6: Create ks.yaml with proper dependencies
  - [ ] Subtask 1.7: Create CiliumNetworkPolicy for External-DNS
  - [ ] Subtask 1.8: Verify DNS record creation for test HTTPRoute

- [ ] Task 2: Configure VMAlertmanager notifications (AC: #2)
  - [ ] Subtask 2.1: Create VMAlertmanagerConfig CR for notification routing
  - [ ] Subtask 2.2: Configure webhook receiver for primary notifications
  - [ ] Subtask 2.3: Configure routing rules based on severity (critical, warning, info)
  - [ ] Subtask 2.4: Set inhibition rules to prevent alert storms
  - [ ] Subtask 2.5: Create ExternalSecret for webhook URL/credentials if needed
  - [ ] Subtask 2.6: Verify VMAlertmanager HA with 2 replicas and gossip
  - [ ] Subtask 2.7: Test alert delivery with `amtool`

- [ ] Task 3: Deploy VMAlert rules for platform monitoring (AC: #3)
  - [ ] Subtask 3.1: Create VMRule for node health alerts
  - [ ] Subtask 3.2: Create VMRule for pod failure alerts
  - [ ] Subtask 3.3: Create VMRule for storage alerts (Ceph, PVC)
  - [ ] Subtask 3.4: Create VMRule for Flux reconciliation alerts
  - [ ] Subtask 3.5: Create VMRule for certificate expiry alerts
  - [ ] Subtask 3.6: Verify all rules load without errors in vmalert
  - [ ] Subtask 3.7: Test alert triggering for each category

- [ ] Task 4: Deploy Cloudflared tunnel for external access (AC: #4)
  - [ ] Subtask 4.1: Create `kubernetes/apps/networking/cloudflared/` directory structure
  - [ ] Subtask 4.2: Create HelmRelease or app-template deployment for Cloudflared
  - [ ] Subtask 4.3: Configure infra tunnel: `monosense.dev` → `envoy-external`
  - [ ] Subtask 4.4: Configure apps tunnel: `monosense.io` → `envoy-gateway-external`
  - [ ] Subtask 4.5: Create ExternalSecret for tunnel credentials
  - [ ] Subtask 4.6: Enable QUIC transport and post-quantum encryption
  - [ ] Subtask 4.7: Configure 2 replicas for high availability
  - [ ] Subtask 4.8: Create CiliumNetworkPolicy for Cloudflared
  - [ ] Subtask 4.9: Verify external access works via tunnel

- [ ] Task 5: Integration testing and validation (AC: #1-5)
  - [ ] Subtask 5.1: Create test HTTPRoute and verify DNS record creation
  - [ ] Subtask 5.2: Trigger test alert and verify notification delivery
  - [ ] Subtask 5.3: Verify external access via Cloudflare Tunnel
  - [ ] Subtask 5.4: Verify alert visualization in Grafana (from Story 6.4)
  - [ ] Subtask 5.5: Document any operational procedures in runbooks

## Dev Notes

### Architecture Context

**Purpose of This Story:**
Complete the observability stack by adding:
1. **External-DNS**: Automatic DNS record management for Gateway API resources
2. **VMAlertmanager**: Alert routing and notification delivery
3. **VMAlert Rules**: Platform health monitoring alerts
4. **Cloudflared**: Secure external access without exposing public IPs

**Observability Stack Completion:**
```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       INFRA CLUSTER (Observability Hub)                       │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                    observability namespace                               │  │
│  │                                                                          │  │
│  │  ┌───────────────────┐  ┌───────────────────┐  ┌────────────────────┐   │  │
│  │  │  VictoriaMetrics  │  │   VictoriaLogs    │  │     Grafana        │   │  │
│  │  │   (Story 6.1)     │  │    (Story 6.2)    │  │    (Story 6.4)     │   │  │
│  │  └────────┬──────────┘  └───────────────────┘  └────────────────────┘   │  │
│  │           │                                                              │  │
│  │           │ alerts                                                       │  │
│  │           ▼                                                              │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐   │  │
│  │  │                     THIS STORY (6.5)                               │   │  │
│  │  │                                                                    │   │  │
│  │  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐   │   │  │
│  │  │  │    VMAlert      │  │  VMAlertmanager │  │    VMRules       │   │   │  │
│  │  │  │  (evaluates)    │──│  (routes/sends) │  │  (definitions)   │   │   │  │
│  │  │  └─────────────────┘  └────────┬────────┘  └──────────────────┘   │   │  │
│  │  │                                │                                   │   │  │
│  │  │                                │ notifications                     │   │  │
│  │  │                                ▼                                   │   │  │
│  │  │                       ┌─────────────────┐                         │   │  │
│  │  │                       │   Webhooks/     │                         │   │  │
│  │  │                       │   Email/Slack   │                         │   │  │
│  │  │                       └─────────────────┘                         │   │  │
│  │  └───────────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                    networking namespace                                  │  │
│  │                                                                          │  │
│  │  ┌───────────────────────────────────────────────────────────────────┐   │  │
│  │  │                     THIS STORY (6.5)                               │   │  │
│  │  │                                                                    │   │  │
│  │  │  ┌─────────────────┐            ┌─────────────────────────────┐   │   │  │
│  │  │  │  External-DNS   │            │        Cloudflared          │   │   │  │
│  │  │  │                 │            │                             │   │   │  │
│  │  │  │ - Cloudflare    │            │ - Tunnel: monosense.dev     │   │   │  │
│  │  │  │ - bind9/RFC2136 │            │ - → envoy-external          │   │   │  │
│  │  │  └────────┬────────┘            │ - QUIC + post-quantum       │   │   │  │
│  │  │           │                     └─────────────┬───────────────┘   │   │  │
│  │  │           │ watches                           │ routes to         │   │  │
│  │  │           ▼                                   ▼                   │   │  │
│  │  │  ┌─────────────────┐            ┌─────────────────────────────┐   │   │  │
│  │  │  │ HTTPRoute/      │            │     Envoy Gateway           │   │   │  │
│  │  │  │ Gateway         │            │     (envoy-external)        │   │   │  │
│  │  │  └─────────────────┘            └─────────────────────────────┘   │   │  │
│  │  └───────────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack Versions

| Component | Version | Source |
|-----------|---------|--------|
| External-DNS | v0.19+ (latest v0.20.0 available) | Helm chart external-dns/external-dns |
| VMAlertmanager | Part of VictoriaMetrics Operator v0.66.1 | VictoriaMetrics Operator CRD |
| Cloudflared | 2025.9.1 (infra) / 2025.8.1 (apps) | Docker image cloudflare/cloudflared |

**External-DNS Notes (v0.19+):**
- Migrating from CloudFlare SDK v0 to v4 for improved performance
- Support for Cloudflare DNS record tags via `external-dns.alpha.kubernetes.io/cloudflare-tags` annotation
- Fixed infinite reconciliation loop with cloudflare-record-comment flag
- min-ttl support added

### Directory Structure

```
kubernetes/apps/networking/external-dns/
├── app/
│   ├── helmrelease.yaml           # External-DNS HelmRelease
│   ├── kustomization.yaml         # Local kustomization
│   ├── externalsecret.yaml        # Cloudflare API credentials
│   └── networkpolicy.yaml         # CiliumNetworkPolicy
└── ks.yaml                        # Flux Kustomization

kubernetes/apps/networking/cloudflared/
├── app/
│   ├── helmrelease.yaml           # Cloudflared deployment
│   ├── kustomization.yaml         # Local kustomization
│   ├── externalsecret.yaml        # Tunnel credentials
│   └── networkpolicy.yaml         # CiliumNetworkPolicy
└── ks.yaml                        # Flux Kustomization

# VMAlertmanager config and rules are in the VictoriaMetrics directory:
clusters/infra/apps/observability/victoria-metrics/
├── app/
│   ├── vmalertmanager.yaml        # VMAlertmanager CR (if not already present)
│   ├── vmalertmanagerconfig.yaml  # Notification routing config
│   └── vmrules/                   # Alert rule definitions
│       ├── node-alerts.yaml
│       ├── pod-alerts.yaml
│       ├── storage-alerts.yaml
│       ├── flux-alerts.yaml
│       └── cert-alerts.yaml
└── ...
```

### External-DNS HelmRelease Configuration

```yaml
# kubernetes/apps/networking/external-dns/app/helmrelease.yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: external-dns
spec:
  interval: 1h
  chart:
    spec:
      chart: external-dns
      version: "1.19.x"  # Check latest - corresponds to app v0.19+
      sourceRef:
        kind: HelmRepository
        name: external-dns
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
    # ============================================================
    # PROVIDER CONFIGURATION: Cloudflare
    # ============================================================
    provider:
      name: cloudflare

    # ============================================================
    # SOURCE CONFIGURATION: Gateway API
    # ============================================================
    sources:
      - gateway-httproute
      - gateway-grpcroute
      - gateway-tcproute
      - gateway-udproute
      - ingress
      - service

    # ============================================================
    # CLOUDFLARE CONFIGURATION
    # ============================================================
    env:
      - name: CF_API_TOKEN
        valueFrom:
          secretKeyRef:
            name: external-dns-cloudflare-secret
            key: api-token

    # Domain filter - only manage these zones
    domainFilters:
      - monosense.dev
      - monosense.io

    # ============================================================
    # POLICY CONFIGURATION
    # ============================================================
    policy: upsert-only  # Never delete records automatically
    txtOwnerId: "k8s-ops-${CLUSTER_NAME}"  # Unique per cluster
    txtPrefix: "k8s."  # Prefix for TXT ownership records

    # ============================================================
    # INTERVAL CONFIGURATION
    # ============================================================
    interval: 1m  # How often to sync
    triggerLoopOnEvent: true  # React immediately to resource changes

    # ============================================================
    # RESOURCES
    # ============================================================
    resources:
      requests:
        cpu: 10m
        memory: 64Mi
      limits:
        memory: 128Mi

    # ============================================================
    # SECURITY CONTEXT
    # ============================================================
    securityContext:
      runAsNonRoot: true
      runAsUser: 65534
      fsGroup: 65534
      seccompProfile:
        type: RuntimeDefault

    containerSecurityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL

    # ============================================================
    # SERVICE ACCOUNT
    # ============================================================
    serviceAccount:
      create: true
      name: external-dns

    # ============================================================
    # POD ANNOTATIONS
    # ============================================================
    podAnnotations:
      reloader.stakater.com/auto: "true"
```

### External-DNS ExternalSecret

```yaml
# kubernetes/apps/networking/external-dns/app/externalsecret.yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: external-dns-cloudflare-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword-connect
  target:
    name: external-dns-cloudflare-secret
    creationPolicy: Owner
  data:
    - secretKey: api-token
      remoteRef:
        key: cloudflare
        property: api_token_dns
```

### VMAlertmanagerConfig for Notifications

```yaml
# clusters/infra/apps/observability/victoria-metrics/app/vmalertmanagerconfig.yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMAlertmanagerConfig
metadata:
  name: platform-alerts
  namespace: observability
spec:
  route:
    receiver: default
    group_by: ['alertname', 'cluster', 'namespace']
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 12h
    routes:
      # Critical alerts - immediate notification
      - match:
          severity: critical
        receiver: critical-webhook
        continue: false

      # Warning alerts - standard notification
      - match:
          severity: warning
        receiver: warning-webhook
        continue: false

  receivers:
    - name: default
      webhook_configs:
        - url: 'http://alertmanager-webhook.monitoring.svc:8080/webhook'
          send_resolved: true

    - name: critical-webhook
      webhook_configs:
        - url: 'http://alertmanager-webhook.monitoring.svc:8080/critical'
          send_resolved: true

    - name: warning-webhook
      webhook_configs:
        - url: 'http://alertmanager-webhook.monitoring.svc:8080/warning'
          send_resolved: true

  # Inhibition rules - prevent alert storms
  inhibit_rules:
    # If cluster is down, inhibit node alerts
    - source_match:
        alertname: ClusterDown
      target_match_re:
        alertname: Node.*
      equal: ['cluster']

    # If node is down, inhibit pod alerts on that node
    - source_match:
        alertname: NodeDown
      target_match_re:
        alertname: Pod.*
      equal: ['node']
```

### VMRule for Core Platform Alerts

```yaml
# clusters/infra/apps/observability/victoria-metrics/app/vmrules/node-alerts.yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMRule
metadata:
  name: node-alerts
  namespace: observability
spec:
  groups:
    - name: node-health
      interval: 30s
      rules:
        - alert: NodeNotReady
          expr: kube_node_status_condition{condition="Ready",status="true"} == 0
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Node {{ $labels.node }} is not ready"
            description: "Node {{ $labels.node }} in cluster {{ $labels.cluster }} has been not ready for more than 5 minutes."

        - alert: NodeHighCPU
          expr: 100 - (avg by(instance, cluster) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
          for: 15m
          labels:
            severity: warning
          annotations:
            summary: "High CPU usage on {{ $labels.instance }}"
            description: "CPU usage is above 90% for more than 15 minutes on {{ $labels.instance }} in cluster {{ $labels.cluster }}."

        - alert: NodeHighMemory
          expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
          for: 15m
          labels:
            severity: warning
          annotations:
            summary: "High memory usage on {{ $labels.instance }}"
            description: "Memory usage is above 90% for more than 15 minutes on {{ $labels.instance }} in cluster {{ $labels.cluster }}."

        - alert: NodeDiskPressure
          expr: kube_node_status_condition{condition="DiskPressure",status="true"} == 1
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Disk pressure on {{ $labels.node }}"
            description: "Node {{ $labels.node }} in cluster {{ $labels.cluster }} is experiencing disk pressure."
```

```yaml
# clusters/infra/apps/observability/victoria-metrics/app/vmrules/flux-alerts.yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMRule
metadata:
  name: flux-alerts
  namespace: observability
spec:
  groups:
    - name: flux-reconciliation
      interval: 1m
      rules:
        - alert: FluxReconciliationFailure
          expr: gotk_reconcile_condition{status="False",type="Ready"} == 1
          for: 15m
          labels:
            severity: warning
          annotations:
            summary: "Flux reconciliation failed for {{ $labels.name }}"
            description: "{{ $labels.kind }}/{{ $labels.name }} in namespace {{ $labels.namespace }} has been failing for more than 15 minutes."

        - alert: FluxSuspended
          expr: gotk_suspend_status == 1
          for: 24h
          labels:
            severity: info
          annotations:
            summary: "Flux resource {{ $labels.name }} suspended"
            description: "{{ $labels.kind }}/{{ $labels.name }} has been suspended for more than 24 hours. Was this intentional?"

        - alert: FluxHelmReleaseNotReady
          expr: gotk_reconcile_condition{type="Ready",status="True",kind="HelmRelease"} == 0
          for: 30m
          labels:
            severity: warning
          annotations:
            summary: "HelmRelease {{ $labels.name }} not ready"
            description: "HelmRelease {{ $labels.name }} in namespace {{ $labels.namespace }} has not been ready for 30 minutes."
```

```yaml
# clusters/infra/apps/observability/victoria-metrics/app/vmrules/storage-alerts.yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMRule
metadata:
  name: storage-alerts
  namespace: observability
spec:
  groups:
    - name: storage-health
      interval: 1m
      rules:
        - alert: CephClusterUnhealthy
          expr: ceph_health_status != 0
          for: 15m
          labels:
            severity: critical
          annotations:
            summary: "Ceph cluster is not healthy"
            description: "Ceph cluster health status is {{ $value }}. Check cluster status immediately."

        - alert: CephOSDDown
          expr: ceph_osd_up == 0
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Ceph OSD {{ $labels.osd }} is down"
            description: "OSD {{ $labels.osd }} has been down for more than 5 minutes."

        - alert: PVCAlmostFull
          expr: kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes > 0.85
          for: 15m
          labels:
            severity: warning
          annotations:
            summary: "PVC {{ $labels.persistentvolumeclaim }} almost full"
            description: "PVC {{ $labels.persistentvolumeclaim }} in namespace {{ $labels.namespace }} is {{ $value | humanizePercentage }} full."

        - alert: PVCFull
          expr: kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes > 0.95
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "PVC {{ $labels.persistentvolumeclaim }} is full"
            description: "PVC {{ $labels.persistentvolumeclaim }} in namespace {{ $labels.namespace }} is {{ $value | humanizePercentage }} full. Immediate action required."
```

```yaml
# clusters/infra/apps/observability/victoria-metrics/app/vmrules/cert-alerts.yaml
apiVersion: operator.victoriametrics.com/v1beta1
kind: VMRule
metadata:
  name: cert-alerts
  namespace: observability
spec:
  groups:
    - name: certificate-expiry
      interval: 1h
      rules:
        - alert: CertificateExpiringSoon
          expr: certmanager_certificate_expiration_timestamp_seconds - time() < 30 * 24 * 3600
          for: 1h
          labels:
            severity: warning
          annotations:
            summary: "Certificate {{ $labels.name }} expiring soon"
            description: "Certificate {{ $labels.name }} in namespace {{ $labels.namespace }} expires in {{ $value | humanizeDuration }}."

        - alert: CertificateExpired
          expr: certmanager_certificate_expiration_timestamp_seconds < time()
          for: 0m
          labels:
            severity: critical
          annotations:
            summary: "Certificate {{ $labels.name }} has expired"
            description: "Certificate {{ $labels.name }} in namespace {{ $labels.namespace }} has expired!"

        - alert: CertificateRenewalFailed
          expr: certmanager_certificate_ready_status{condition="True"} == 0
          for: 24h
          labels:
            severity: warning
          annotations:
            summary: "Certificate {{ $labels.name }} renewal failing"
            description: "Certificate {{ $labels.name }} in namespace {{ $labels.namespace }} has been failing to renew for 24 hours."
```

### Cloudflared Deployment

```yaml
# kubernetes/apps/networking/cloudflared/app/helmrelease.yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: cloudflared
spec:
  interval: 1h
  chartRef:
    kind: OCIRepository
    name: app-template
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
    controllers:
      cloudflared:
        replicas: 2

        strategy: RollingUpdate

        containers:
          app:
            image:
              repository: docker.io/cloudflare/cloudflared
              tag: 2025.9.1@sha256:4604b477520dc8322af5427da68b44f0bf814938e9d2e4814f2249ee4b03ffdf

            args:
              - tunnel
              - --config
              - /etc/cloudflared/config/config.yaml
              - run
              - --token
              - $(TUNNEL_TOKEN)

            env:
              TUNNEL_TOKEN:
                valueFrom:
                  secretKeyRef:
                    name: cloudflared-tunnel-secret
                    key: token

            probes:
              liveness:
                enabled: true
                custom: true
                spec:
                  httpGet:
                    path: /ready
                    port: 2000
                  initialDelaySeconds: 0
                  periodSeconds: 10
                  timeoutSeconds: 1
                  failureThreshold: 3
              readiness:
                enabled: true
                custom: true
                spec:
                  httpGet:
                    path: /ready
                    port: 2000
                  initialDelaySeconds: 0
                  periodSeconds: 10
                  timeoutSeconds: 1
                  failureThreshold: 3

            resources:
              requests:
                cpu: 10m
                memory: 64Mi
              limits:
                memory: 128Mi

            securityContext:
              allowPrivilegeEscalation: false
              readOnlyRootFilesystem: true
              capabilities:
                drop:
                  - ALL

        pod:
          securityContext:
            runAsUser: 65534
            runAsGroup: 65534
            runAsNonRoot: true
            seccompProfile:
              type: RuntimeDefault

          topologySpreadConstraints:
            - maxSkew: 1
              topologyKey: kubernetes.io/hostname
              whenUnsatisfiable: DoNotSchedule
              labelSelector:
                matchLabels:
                  app.kubernetes.io/name: cloudflared

          annotations:
            reloader.stakater.com/auto: "true"

    persistence:
      config:
        type: configMap
        name: cloudflared-config
        globalMounts:
          - path: /etc/cloudflared/config
            readOnly: true

    configMaps:
      config:
        data:
          config.yaml: |
            tunnel: ${CLUSTER_NAME}-tunnel
            credentials-file: /etc/cloudflared/creds/credentials.json
            metrics: 0.0.0.0:2000
            no-autoupdate: true
            protocol: quic
            post-quantum: true
            ingress:
              - hostname: "*.${CLUSTER_DOMAIN}"
                service: http://envoy-external.networking.svc:80
              - service: http_status:404
```

### Cloudflared ExternalSecret

```yaml
# kubernetes/apps/networking/cloudflared/app/externalsecret.yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: cloudflared-tunnel-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword-connect
  target:
    name: cloudflared-tunnel-secret
    creationPolicy: Owner
  data:
    - secretKey: token
      remoteRef:
        key: cloudflare-tunnel-${CLUSTER_NAME}
        property: token
```

### CiliumNetworkPolicy for External-DNS

```yaml
# kubernetes/apps/networking/external-dns/app/networkpolicy.yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: external-dns
spec:
  endpointSelector:
    matchLabels:
      app.kubernetes.io/name: external-dns

  egress:
    # Allow to Cloudflare API
    - toFQDNs:
        - matchName: "api.cloudflare.com"
      toPorts:
        - ports:
            - port: "443"
              protocol: TCP

    # Allow to Kubernetes API for watching resources
    - toEntities:
        - kube-apiserver
      toPorts:
        - ports:
            - port: "6443"
              protocol: TCP

    # Allow to internal bind9 DNS server (RFC2136)
    - toFQDNs:
        - matchPattern: "*.monosense.dev"
      toPorts:
        - ports:
            - port: "53"
              protocol: TCP
            - port: "53"
              protocol: UDP

    # Allow DNS resolution
    - toEndpoints:
        - matchLabels:
            k8s:io.kubernetes.pod.namespace: kube-system
            k8s-app: kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: UDP
```

### Flux Kustomization for External-DNS

```yaml
# kubernetes/apps/networking/external-dns/ks.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name external-dns
  namespace: flux-system
spec:
  targetNamespace: networking
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./kubernetes/apps/networking/external-dns/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: true
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  dependsOn:
    - name: external-secrets-stores  # ClusterSecretStore needed
    - name: envoy-gateway            # Gateway resources to watch
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

### Verification Commands

```bash
# ============================================================
# External-DNS Verification
# ============================================================

# Verify External-DNS pod running
kubectl --context infra get pods -n networking -l app.kubernetes.io/name=external-dns

# Check External-DNS logs for record creation
kubectl --context infra logs -n networking -l app.kubernetes.io/name=external-dns | grep -i "create\|update\|cloudflare"

# Verify ExternalSecret synced
kubectl --context infra get externalsecret -n networking external-dns-cloudflare-secret

# Test DNS record creation - create a test HTTPRoute
# Then check Cloudflare dashboard or use dig:
dig grafana.monosense.dev

# ============================================================
# VMAlertmanager Verification
# ============================================================

# Check VMAlertmanager status
kubectl --context infra get vmalertmanager -n observability

# Verify replicas and gossip cluster
kubectl --context infra get pods -n observability -l app.kubernetes.io/name=vmalertmanager

# Check VMAlertmanagerConfig applied
kubectl --context infra get vmalertmanagerconfig -n observability

# View current alerts
kubectl --context infra port-forward -n observability svc/vmalertmanager-vmalertmanager 9093:9093
# Then: curl http://localhost:9093/api/v2/alerts

# Test alert delivery (trigger a test alert via VMAlert)
# Create a test VMRule that fires immediately, verify notification received

# ============================================================
# VMAlert Rules Verification
# ============================================================

# Check VMRules loaded
kubectl --context infra get vmrule -n observability

# Verify rules loaded in vmalert
kubectl --context infra port-forward -n observability svc/vmalert-vmalert 8880:8880
# Then: curl http://localhost:8880/api/v1/rules | jq

# Check for rule evaluation errors
kubectl --context infra logs -n observability -l app.kubernetes.io/name=vmalert | grep -i error

# ============================================================
# Cloudflared Verification
# ============================================================

# Verify Cloudflared pods running
kubectl --context infra get pods -n networking -l app.kubernetes.io/name=cloudflared

# Check tunnel health
kubectl --context infra logs -n networking -l app.kubernetes.io/name=cloudflared | grep -i "connected\|tunnel"

# Verify readiness probe
kubectl --context infra exec -n networking deploy/cloudflared -- wget -qO- http://localhost:2000/ready

# Test external access
curl -I https://grafana.monosense.dev
# Should return 200 OK (or redirect to auth if SSO enabled)

# ============================================================
# End-to-End Verification
# ============================================================

# 1. Create test HTTPRoute
cat <<EOF | kubectl apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: test-route
  namespace: default
spec:
  parentRefs:
    - name: envoy-external
      namespace: networking
  hostnames:
    - "test.monosense.dev"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: kubernetes
          port: 443
EOF

# 2. Wait for DNS record creation (up to 60 seconds)
sleep 60

# 3. Verify DNS record exists
dig test.monosense.dev

# 4. Cleanup test route
kubectl delete httproute test-route -n default

# ============================================================
# Timing Verification (NFRs)
# ============================================================

# NFR36: DNS record creation < 60 seconds
# Timestamp HTTPRoute creation, measure time until DNS propagates

# NFR41: Alert notification < 1 minute
# Create test alert, measure time until webhook receives notification
```

### Anti-Patterns to Avoid

1. **DO NOT** hardcode Cloudflare API tokens in values.yaml - use ExternalSecret
2. **DO NOT** set external-dns policy to `sync` in production - use `upsert-only` to prevent accidental deletions
3. **DO NOT** forget txtOwnerId - this prevents conflicts between multiple external-dns instances
4. **DO NOT** use the same tunnel token for both clusters - each cluster needs its own tunnel
5. **DO NOT** configure VMAlertmanager without inhibition rules - this leads to alert storms
6. **DO NOT** skip HA configuration for VMAlertmanager - single replica loses alerts during restarts
7. **DO NOT** forget cluster labels in alert rules - multi-cluster visibility requires `{{ $labels.cluster }}`
8. **DO NOT** use HTTP for webhook notifications in production - use HTTPS with proper certs
9. **DO NOT** skip network policies - External-DNS needs internet access, Cloudflared needs tunnel egress

### Edge Cases

**Scenario: DNS record creation fails**
- Check External-DNS logs for Cloudflare API errors
- Verify API token has DNS edit permissions for the zone
- Check zone ID is correct in Cloudflare dashboard
- Verify domain filter matches the zone

**Scenario: Alerts not being delivered**
- Check VMAlertmanager logs for webhook errors
- Verify webhook endpoint is reachable from observability namespace
- Check network policies allow egress to webhook service
- Verify VMAlertmanagerConfig was loaded (check generated secret)

**Scenario: Cloudflared tunnel disconnects**
- Check Cloudflare dashboard for tunnel status
- Verify tunnel token is valid and not expired
- Check QUIC/post-quantum settings if firewall blocks UDP
- Review pod logs for connection errors

**Scenario: Multi-cluster alert routing**
- Ensure `cluster` label is present on all metrics
- VMAlert on infra cluster receives both infra and apps metrics
- Route alerts based on cluster label if needed:
  ```yaml
  routes:
    - match:
        cluster: apps
      receiver: apps-team-webhook
  ```

### Dependencies

| This Story Depends On | Required For |
|-----------------------|--------------|
| Story 6.1 (VictoriaMetrics on Infra) | VMAlertmanager, VMAlert, VMRule CRDs |
| Story 6.3 (Apps Cluster Agents) | Multi-cluster metrics with cluster labels |
| Story 6.4 (Grafana) | Alert visualization |
| Story 4.1 (Envoy Gateway) | HTTPRoute resources for External-DNS to watch |
| External Secrets (Story 1.4) | Cloudflare API token, tunnel credentials |

| Stories That Depend On This | Reason |
|-----------------------------|--------|
| Story 5.4 (Multi-Cluster Validation) | External access for validation testing |
| Epic 7 (Backup & DR) | Alert rules for backup failures |
| Epic 8 (ArsipQ Platform) | DNS for platform services |

### Previous Story Learnings (Story 6.4)

From Grafana Multi-Cluster Dashboards deployment:
- Multi-cluster data is flowing with `cluster` labels
- VictoriaMetrics datasource plugin ID: `victoriametrics-metrics-datasource`
- Grafana accessible via `grafana.monosense.dev`
- OAuth/SSO with Authentik is configured
- Network policies allow cross-namespace communication

**Relevant for this story:**
- Alerts can be visualized in Grafana via VMAlertmanager datasource
- HTTPRoute pattern established for external services
- Cloudflare Tunnel will route to same Gateway as Grafana

### Project Structure Alignment

**App Location Rule Compliance:**
- External-DNS: `kubernetes/apps/networking/external-dns/` (shared across clusters)
- Cloudflared: `kubernetes/apps/networking/cloudflared/` (shared, uses cluster-vars for tunnel config)
- VMAlertmanager/VMRules: `clusters/infra/apps/observability/victoria-metrics/` (infra only, part of VM stack)

**Naming Conventions:**
- HelmRelease names: `external-dns`, `cloudflared`
- Namespace: `networking` (consistent with other networking components)
- Labels follow `app.kubernetes.io/name: <app>` pattern

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#DNS Strategy (Split DNS)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Hub/Spoke Observability Architecture]
- [Source: _bmad-output/planning-artifacts/prd.md#FR51 Automatic DNS record creation]
- [Source: _bmad-output/planning-artifacts/prd.md#FR44 VMAlertmanager notifications]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR36 Cloudflare DNS within 60 seconds]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR41 Alert notification within 1 minute]
- [Source: docs/project-context.md#Networking - external-dns v0.19.0]
- [Source: docs/project-context.md#Networking - Cloudflared]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.5]

### External Documentation

**External-DNS:**
- [External-DNS GitHub](https://github.com/kubernetes-sigs/external-dns)
- [External-DNS Cloudflare Provider](https://kubernetes-sigs.github.io/external-dns/latest/docs/tutorials/cloudflare/)
- [External-DNS Releases](https://github.com/kubernetes-sigs/external-dns/releases)

**VictoriaMetrics Alerting:**
- [VMAlertmanager CRD](https://docs.victoriametrics.com/operator/resources/vmalertmanager/)
- [VMAlertmanagerConfig CRD](https://docs.victoriametrics.com/operator/resources/vmalertmanagerconfig/)
- [VMRule CRD](https://docs.victoriametrics.com/operator/resources/vmrule/)
- [VMAlert Documentation](https://docs.victoriametrics.com/vmalert/)

**Cloudflared:**
- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Cloudflared Docker Image](https://hub.docker.com/r/cloudflare/cloudflared)
- [Tunnel Configuration](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/configuration/)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
