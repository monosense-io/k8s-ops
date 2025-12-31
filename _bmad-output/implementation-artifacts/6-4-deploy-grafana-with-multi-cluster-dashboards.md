# Story 6.4: Deploy Grafana with Multi-Cluster Dashboards

Status: ready-for-dev

## Story

As a platform operator,
I want Grafana dashboards showing metrics from both clusters,
so that I have visual insight into cluster and application health from a single centralized location.

## Acceptance Criteria

1. **AC1**: Grafana deployed on infra cluster with HelmRelease:
   - `clusters/infra/apps/observability/grafana/` contains complete deployment
   - HelmRelease uses `helm.toolkit.fluxcd.io/v2` API version
   - Install/upgrade remediation configured per project-context.md
   - Grafana accessible via `grafana.monosense.dev` HTTPRoute
   - Grafana uses Rook-Ceph persistent storage for dashboards/settings

2. **AC2**: SSO authentication via Authentik configured:
   - Generic OAuth configured with Authentik as identity provider
   - Client secret stored in ExternalSecret (1Password)
   - Role mapping: Authentik groups → Grafana roles (Admin, Editor, Viewer)
   - Auto-login enabled (no local password auth)
   - Callback URL properly configured for `grafana.monosense.dev`

3. **AC3**: VictoriaMetrics datasource configured:
   - `victoriametrics-metrics-datasource` plugin installed
   - Datasource URL points to local VMSingle: `http://vmsingle-vmsingle.observability.svc:8429`
   - Set as default datasource
   - Provisioned via sidecar/configuration (not manual)
   - Query response < 2 seconds for 95th percentile (NFR3)

4. **AC4**: VictoriaLogs datasource configured:
   - `victoriametrics-logs-datasource` plugin installed
   - Datasource URL points to local VictoriaLogs: `http://victoria-logs.observability.svc:9428`
   - LogsQL query support enabled
   - Provisioned via sidecar/configuration

5. **AC5**: Required dashboards deployed:
   - **Cluster Overview**: Node health, pod counts, resource usage (both clusters visible via `cluster` label)
   - **Flux GitOps**: Reconciliation status, sync times, error rates
   - **Application Health**: Per-namespace pod status, restart counts, ingress latency
   - Dashboards provisioned via ConfigMaps with sidecar
   - Dashboards load with data within 10 seconds

6. **AC6**: Flux patterns and dependencies:
   - Dependencies on `victoria-metrics` and `victoria-logs` kustomizations
   - Dependencies on `authentik` for SSO
   - Uses `${CLUSTER_DOMAIN}` substitution from cluster-vars
   - CiliumNetworkPolicy for Tier 2 security

## Tasks / Subtasks

- [ ] Task 1: Create Grafana HelmRelease deployment (AC: #1)
  - [ ] Subtask 1.1: Create `clusters/infra/apps/observability/grafana/` directory structure
  - [ ] Subtask 1.2: Create HelmRelease using Grafana Helm chart (latest stable)
  - [ ] Subtask 1.3: Configure persistent storage using `ceph-block` StorageClass
  - [ ] Subtask 1.4: Configure resource requests/limits
  - [ ] Subtask 1.5: Enable dashboard/datasource sidecars for ConfigMap provisioning
  - [ ] Subtask 1.6: Create ks.yaml with proper dependencies
  - [ ] Subtask 1.7: Verify Grafana pod is Running and Ready

- [ ] Task 2: Configure HTTPRoute and external access (AC: #1)
  - [ ] Subtask 2.1: Create HTTPRoute for `grafana.${CLUSTER_DOMAIN}`
  - [ ] Subtask 2.2: Reference `envoy-external` Gateway for Cloudflare Tunnel access
  - [ ] Subtask 2.3: Configure TLS via wildcard certificate
  - [ ] Subtask 2.4: Verify access via `grafana.monosense.dev`

- [ ] Task 3: Configure Authentik SSO OAuth (AC: #2)
  - [ ] Subtask 3.1: Create ExternalSecret for Authentik OAuth client credentials
  - [ ] Subtask 3.2: Configure `auth.generic_oauth` in grafana.ini values
  - [ ] Subtask 3.3: Set `auth_url`, `token_url`, `api_url` to Authentik endpoints
  - [ ] Subtask 3.4: Configure `role_attribute_path` JMESPath for group→role mapping
  - [ ] Subtask 3.5: Enable auto-login and disable password auth
  - [ ] Subtask 3.6: Create Authentik OAuth application and provider (if not exists)
  - [ ] Subtask 3.7: Test SSO login and role assignment

- [ ] Task 4: Configure VictoriaMetrics datasource (AC: #3)
  - [ ] Subtask 4.1: Add `victoriametrics-metrics-datasource` to `GF_INSTALL_PLUGINS`
  - [ ] Subtask 4.2: Create datasource provisioning ConfigMap
  - [ ] Subtask 4.3: Set datasource type to `victoriametrics-metrics-datasource`
  - [ ] Subtask 4.4: Set URL to `http://vmsingle-vmsingle.observability.svc:8429`
  - [ ] Subtask 4.5: Set as default datasource (`isDefault: true`)
  - [ ] Subtask 4.6: Verify datasource connectivity in Grafana UI

- [ ] Task 5: Configure VictoriaLogs datasource (AC: #4)
  - [ ] Subtask 5.1: Add `victoriametrics-logs-datasource` to `GF_INSTALL_PLUGINS`
  - [ ] Subtask 5.2: Create datasource provisioning ConfigMap (or add to existing)
  - [ ] Subtask 5.3: Set datasource type to `victoriametrics-logs-datasource`
  - [ ] Subtask 5.4: Set URL to `http://victoria-logs.observability.svc:9428`
  - [ ] Subtask 5.5: Verify LogsQL queries work

- [ ] Task 6: Deploy required dashboards (AC: #5)
  - [ ] Subtask 6.1: Create ConfigMap for Cluster Overview dashboard
  - [ ] Subtask 6.2: Create ConfigMap for Flux GitOps dashboard
  - [ ] Subtask 6.3: Create ConfigMap for Application Health dashboard
  - [ ] Subtask 6.4: Add `grafana_dashboard: "1"` label to enable sidecar discovery
  - [ ] Subtask 6.5: Verify dashboards appear in Grafana UI
  - [ ] Subtask 6.6: Verify multi-cluster data (filter by `cluster` label)

- [ ] Task 7: Network policy and security (AC: #6)
  - [ ] Subtask 7.1: Create CiliumNetworkPolicy for Grafana
  - [ ] Subtask 7.2: Allow ingress from Envoy Gateway
  - [ ] Subtask 7.3: Allow egress to VictoriaMetrics, VictoriaLogs, Authentik
  - [ ] Subtask 7.4: Verify network connectivity after policy applied

## Dev Notes

### Architecture Context

**Purpose of This Story:**
Deploy Grafana as the unified visualization layer for the hub/spoke observability architecture. Grafana runs on the infra cluster (hub) and queries data from VictoriaMetrics and VictoriaLogs which receive metrics/logs from both clusters.

**Observability Stack Visualization:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       INFRA CLUSTER (Observability Hub)                      │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    observability namespace                              │ │
│  │                                                                         │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │ │
│  │  │                          GRAFANA                                  │  │ │
│  │  │                     (This Story - 6.4)                            │  │ │
│  │  │                                                                   │  │ │
│  │  │  Datasources:                    Dashboards:                      │  │ │
│  │  │  ┌───────────────────────┐      ┌────────────────────────────┐   │  │ │
│  │  │  │ VictoriaMetrics       │      │ Cluster Overview           │   │  │ │
│  │  │  │ (Metrics)             │      │ - Node health (both)       │   │  │ │
│  │  │  │ type: victoriametrics-│      │ - Pod counts (both)        │   │  │ │
│  │  │  │       metrics-datasrc │      │ - Resource usage (both)    │   │  │ │
│  │  │  └───────────┬───────────┘      └────────────────────────────┘   │  │ │
│  │  │              │                  ┌────────────────────────────┐   │  │ │
│  │  │  ┌───────────┴───────────┐      │ Flux GitOps                │   │  │ │
│  │  │  │ VictoriaLogs          │      │ - Reconciliation status    │   │  │ │
│  │  │  │ (Logs)                │      │ - Sync times               │   │  │ │
│  │  │  │ type: victoriametrics-│      │ - Error rates              │   │  │ │
│  │  │  │       logs-datasource │      └────────────────────────────┘   │  │ │
│  │  │  └───────────────────────┘      ┌────────────────────────────┐   │  │ │
│  │  │                                 │ Application Health         │   │  │ │
│  │  │  Authentication:                │ - Pod status/restarts      │   │  │ │
│  │  │  ┌───────────────────────┐      │ - Ingress latency          │   │  │ │
│  │  │  │ Authentik SSO (OAuth) │      │ - Error rates              │   │  │ │
│  │  │  │ - Auto-login          │      └────────────────────────────┘   │  │ │
│  │  │  │ - Group → Role mapping│                                       │  │ │
│  │  │  └───────────────────────┘                                       │  │ │
│  │  └──────────────────────────────────────────────────────────────────┘  │ │
│  │                 │                            │                          │ │
│  │                 │ queries                    │ queries                  │ │
│  │                 ▼                            ▼                          │ │
│  │  ┌─────────────────────────┐    ┌─────────────────────────────────────┐│ │
│  │  │   VictoriaMetrics       │    │        VictoriaLogs                 ││ │
│  │  │   (Story 6.1)           │    │        (Story 6.2)                  ││ │
│  │  │                         │    │                                     ││ │
│  │  │  Contains metrics with: │    │  Contains logs with:                ││ │
│  │  │  cluster="infra"        │    │  cluster="infra"                    ││ │
│  │  │  cluster="apps"         │    │  cluster="apps"                     ││ │
│  │  └─────────────────────────┘    └─────────────────────────────────────┘│ │
│  │               ▲                              ▲                          │ │
│  └───────────────┼──────────────────────────────┼──────────────────────────┘ │
│                  │ local scrape                 │ local ship                 │
│                  │                              │                            │
│   ┌──────────────┴────────────┐  ┌──────────────┴──────────────────────────┐ │
│   │ VMAgent (local)           │  │ Fluent-bit (local)                      │ │
│   │ external_labels:          │  │ Record: cluster=infra                   │ │
│   │   cluster: infra          │  └─────────────────────────────────────────┘ │
│   └───────────────────────────┘                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                               ▲                  ▲
                               │ remote-write     │ remote-write
                               │ (from Story 6.3) │ (from Story 6.3)
┌──────────────────────────────┴──────────────────┴────────────────────────────┐
│                       APPS CLUSTER (Spoke)                                    │
│  VMAgent (cluster="apps") + Fluent-bit (cluster="apps")                       │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Technology Stack Versions

| Component | Version | Source |
|-----------|---------|--------|
| Grafana | 11.x (latest stable) | Helm chart grafana/grafana |
| VictoriaMetrics Datasource Plugin | Latest | `victoriametrics-metrics-datasource` |
| VictoriaLogs Datasource Plugin | Latest | `victoriametrics-logs-datasource` |
| Authentik | 2025.x | Already deployed (kubernetes/apps/security/authentik) |

**Important Plugin Note:**
The VictoriaMetrics plugin ID changed to `victoriametrics-metrics-datasource` (breaking change from older `victoriametrics-datasource`). The provisioning type MUST match this new ID.

### Directory Structure

```
clusters/infra/apps/observability/grafana/
├── app/
│   ├── helmrelease.yaml           # Grafana HelmRelease
│   ├── kustomization.yaml         # Local kustomization
│   ├── externalsecret.yaml        # Authentik OAuth credentials
│   ├── httproute.yaml             # External access via Gateway
│   ├── networkpolicy.yaml         # CiliumNetworkPolicy
│   └── dashboards/                # Dashboard ConfigMaps
│       ├── cluster-overview.yaml
│       ├── flux-gitops.yaml
│       └── application-health.yaml
└── ks.yaml                        # Flux Kustomization
```

### HelmRelease Configuration

```yaml
# clusters/infra/apps/observability/grafana/app/helmrelease.yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: grafana
spec:
  interval: 1h
  chart:
    spec:
      chart: grafana
      version: "8.11.x"  # Check latest stable
      sourceRef:
        kind: HelmRepository
        name: grafana
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
    replicas: 1

    # ============================================================
    # PLUGINS: VictoriaMetrics + VictoriaLogs Datasources
    # ============================================================
    plugins:
      - victoriametrics-metrics-datasource
      - victoriametrics-logs-datasource

    # Alternative via env var:
    # env:
    #   GF_INSTALL_PLUGINS: "victoriametrics-metrics-datasource,victoriametrics-logs-datasource"

    # ============================================================
    # PERSISTENCE: Ceph Block Storage
    # ============================================================
    persistence:
      enabled: true
      type: pvc
      storageClassName: ceph-block
      size: 10Gi

    # ============================================================
    # SIDECAR: Dashboard/Datasource ConfigMap Discovery
    # ============================================================
    sidecar:
      dashboards:
        enabled: true
        searchNamespace: ALL
        label: grafana_dashboard
        labelValue: "1"
        folderAnnotation: grafana_folder
      datasources:
        enabled: true
        searchNamespace: ALL
        label: grafana_datasource
        labelValue: "1"

    # ============================================================
    # AUTHENTIK SSO CONFIGURATION
    # ============================================================
    grafana.ini:
      server:
        root_url: https://grafana.${CLUSTER_DOMAIN}

      # Disable local auth - use SSO only
      auth:
        disable_login_form: true
      auth.basic:
        enabled: false

      # Authentik Generic OAuth
      auth.generic_oauth:
        enabled: true
        name: Authentik
        allow_sign_up: true
        auto_login: true
        client_id: $__env{GRAFANA_OAUTH_CLIENT_ID}
        client_secret: $__env{GRAFANA_OAUTH_CLIENT_SECRET}
        scopes: openid profile email
        auth_url: https://auth.${CLUSTER_DOMAIN}/application/o/authorize/
        token_url: https://auth.${CLUSTER_DOMAIN}/application/o/token/
        api_url: https://auth.${CLUSTER_DOMAIN}/application/o/userinfo/
        # Role mapping: Authentik groups → Grafana roles
        role_attribute_path: "contains(groups[*], 'Grafana Admins') && 'Admin' || contains(groups[*], 'Grafana Editors') && 'Editor' || 'Viewer'"
        role_attribute_strict: false
        allow_assign_grafana_admin: true

    # Inject OAuth credentials from ExternalSecret
    envFromSecrets:
      - name: grafana-oauth-secret

    # ============================================================
    # RESOURCES
    # ============================================================
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
      limits:
        memory: 512Mi

    # ============================================================
    # SECURITY CONTEXT
    # ============================================================
    securityContext:
      runAsNonRoot: true
      runAsUser: 472
      runAsGroup: 472
      fsGroup: 472

    containerSecurityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
          - ALL
      readOnlyRootFilesystem: true

    # ============================================================
    # POD ANNOTATIONS
    # ============================================================
    podAnnotations:
      reloader.stakater.com/auto: "true"
```

### Datasource Provisioning ConfigMap

```yaml
# Can be in helmrelease values or separate ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
  labels:
    grafana_datasource: "1"
data:
  datasources.yaml: |
    apiVersion: 1
    deleteDatasources:
      - name: Prometheus
        orgId: 1
    datasources:
      - name: VictoriaMetrics
        type: victoriametrics-metrics-datasource
        uid: victoriametrics
        url: http://vmsingle-vmsingle.observability.svc:8429
        access: proxy
        isDefault: true
        editable: false
        jsonData:
          # MetricsQL is PromQL-compatible
          httpMethod: POST

      - name: VictoriaLogs
        type: victoriametrics-logs-datasource
        uid: victorialogs
        url: http://victoria-logs.observability.svc:9428
        access: proxy
        isDefault: false
        editable: false
```

### ExternalSecret for Authentik OAuth

```yaml
# clusters/infra/apps/observability/grafana/app/externalsecret.yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: grafana-oauth-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword-connect
  target:
    name: grafana-oauth-secret
    creationPolicy: Owner
  data:
    - secretKey: GRAFANA_OAUTH_CLIENT_ID
      remoteRef:
        key: grafana
        property: oauth_client_id
    - secretKey: GRAFANA_OAUTH_CLIENT_SECRET
      remoteRef:
        key: grafana
        property: oauth_client_secret
```

### HTTPRoute for External Access

```yaml
# clusters/infra/apps/observability/grafana/app/httproute.yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: grafana
spec:
  parentRefs:
    - name: envoy-external
      namespace: networking
      sectionName: https
  hostnames:
    - "grafana.${CLUSTER_DOMAIN}"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: grafana
          port: 80
```

### CiliumNetworkPolicy

```yaml
# clusters/infra/apps/observability/grafana/app/networkpolicy.yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: grafana
spec:
  endpointSelector:
    matchLabels:
      app.kubernetes.io/name: grafana

  ingress:
    # Allow from Envoy Gateway
    - fromEndpoints:
        - matchLabels:
            app.kubernetes.io/name: envoy
            io.kubernetes.pod.namespace: networking
      toPorts:
        - ports:
            - port: "3000"
              protocol: TCP

  egress:
    # Allow to VictoriaMetrics
    - toEndpoints:
        - matchLabels:
            app.kubernetes.io/name: vmsingle
      toPorts:
        - ports:
            - port: "8429"
              protocol: TCP

    # Allow to VictoriaLogs
    - toEndpoints:
        - matchLabels:
            app.kubernetes.io/name: victoria-logs
      toPorts:
        - ports:
            - port: "9428"
              protocol: TCP

    # Allow to Authentik for OAuth
    - toEndpoints:
        - matchLabels:
            app.kubernetes.io/name: authentik
            io.kubernetes.pod.namespace: security
      toPorts:
        - ports:
            - port: "9000"
              protocol: TCP

    # Allow DNS
    - toEndpoints:
        - matchLabels:
            k8s:io.kubernetes.pod.namespace: kube-system
            k8s-app: kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: UDP
```

### Dashboard ConfigMaps

```yaml
# clusters/infra/apps/observability/grafana/app/dashboards/cluster-overview.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboard-cluster-overview
  labels:
    grafana_dashboard: "1"
  annotations:
    grafana_folder: "Kubernetes"
data:
  cluster-overview.json: |
    {
      "title": "Cluster Overview",
      "description": "Multi-cluster node health, pod counts, and resource usage",
      "templating": {
        "list": [
          {
            "name": "cluster",
            "type": "query",
            "datasource": "VictoriaMetrics",
            "query": "label_values(cluster)",
            "multi": true,
            "includeAll": true
          }
        ]
      },
      "panels": [
        {
          "title": "Node Status by Cluster",
          "type": "stat",
          "targets": [
            {
              "expr": "sum(kube_node_status_condition{condition='Ready', status='true', cluster=~'$cluster'}) by (cluster)",
              "legendFormat": "{{cluster}}"
            }
          ]
        },
        {
          "title": "Pod Count by Cluster",
          "type": "stat",
          "targets": [
            {
              "expr": "sum(kube_pod_status_phase{phase='Running', cluster=~'$cluster'}) by (cluster)",
              "legendFormat": "{{cluster}}"
            }
          ]
        },
        {
          "title": "CPU Usage by Cluster",
          "type": "timeseries",
          "targets": [
            {
              "expr": "sum(rate(container_cpu_usage_seconds_total{cluster=~'$cluster'}[5m])) by (cluster)",
              "legendFormat": "{{cluster}}"
            }
          ]
        },
        {
          "title": "Memory Usage by Cluster",
          "type": "timeseries",
          "targets": [
            {
              "expr": "sum(container_memory_working_set_bytes{cluster=~'$cluster'}) by (cluster)",
              "legendFormat": "{{cluster}}"
            }
          ]
        }
      ]
    }
```

**Note:** Full dashboard JSONs should be sourced from:
- Community dashboards for Kubernetes: https://grafana.com/grafana/dashboards/
- VictoriaMetrics provided dashboards
- Flux GitOps dashboard: https://grafana.com/grafana/dashboards/16714

### Flux Kustomization

```yaml
# clusters/infra/apps/observability/grafana/ks.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name grafana
  namespace: flux-system
spec:
  targetNamespace: observability
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./clusters/infra/apps/observability/grafana/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: true
  interval: 30m
  retryInterval: 1m
  timeout: 10m
  dependsOn:
    - name: victoria-metrics        # VictoriaMetrics must be running
    - name: victoria-logs           # VictoriaLogs must be running
    - name: authentik               # Authentik for SSO
    - name: rook-ceph-cluster       # Storage for persistence
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

### Authentik OAuth Application Setup

**Required Authentik Configuration (if not already exists):**

1. **Create OAuth2/OIDC Provider:**
   - Name: `Grafana`
   - Authorization flow: `default-provider-authorization-explicit-consent`
   - Client type: `Confidential`
   - Client ID: (auto-generated, store in 1Password as `grafana.oauth_client_id`)
   - Client Secret: (auto-generated, store in 1Password as `grafana.oauth_client_secret`)
   - Redirect URIs: `https://grafana.monosense.dev/login/generic_oauth`
   - Scopes: `openid`, `profile`, `email`

2. **Create Application:**
   - Name: `Grafana`
   - Slug: `grafana`
   - Provider: `Grafana` (the one created above)
   - Launch URL: `https://grafana.monosense.dev`

3. **Create Groups (for role mapping):**
   - `Grafana Admins` → Maps to Grafana Admin role
   - `Grafana Editors` → Maps to Grafana Editor role
   - Users not in either group → Viewer role

### Verification Commands

```bash
# ============================================================
# Grafana Deployment Verification
# ============================================================

# Verify Grafana pod running
kubectl --context infra get pods -n observability -l app.kubernetes.io/name=grafana

# Check Grafana logs for plugin installation
kubectl --context infra logs -n observability -l app.kubernetes.io/name=grafana | grep -i plugin

# Verify PVC created
kubectl --context infra get pvc -n observability | grep grafana

# ============================================================
# Datasource Verification
# ============================================================

# Port-forward to access Grafana locally
kubectl --context infra port-forward -n observability svc/grafana 3000:80

# Via API (after logging in):
curl -s http://localhost:3000/api/datasources | jq '.[] | {name, type, url}'

# Expected output:
# {
#   "name": "VictoriaMetrics",
#   "type": "victoriametrics-metrics-datasource",
#   "url": "http://vmsingle-vmsingle.observability.svc:8429"
# }
# {
#   "name": "VictoriaLogs",
#   "type": "victoriametrics-logs-datasource",
#   "url": "http://victoria-logs.observability.svc:9428"
# }

# ============================================================
# Multi-Cluster Data Verification
# ============================================================

# Test VictoriaMetrics query for both clusters
curl -s 'http://localhost:8428/api/v1/label/cluster/values' | jq
# Should return: {"status":"success","data":["apps","infra"]}

# Test query with cluster filter
curl -s 'http://localhost:8428/api/v1/query?query=up{cluster="apps"}' | jq '.data.result | length'

# ============================================================
# OAuth/SSO Verification
# ============================================================

# Check OAuth configuration
kubectl --context infra exec -n observability deploy/grafana -- grafana-cli plugins ls
# Should show victoriametrics plugins installed

# Verify ExternalSecret synced
kubectl --context infra get externalsecret -n observability grafana-oauth-secret

# Check secret exists
kubectl --context infra get secret -n observability grafana-oauth-secret

# ============================================================
# Dashboard Verification
# ============================================================

# List dashboards via API
curl -s http://localhost:3000/api/search?type=dash-db | jq '.[].title'

# Verify multi-cluster variable works
# Access Grafana UI → Cluster Overview → Check cluster dropdown shows "infra" and "apps"

# ============================================================
# HTTPRoute/Access Verification
# ============================================================

# Verify HTTPRoute
kubectl --context infra get httproute -n observability grafana

# Test external access
curl -I https://grafana.monosense.dev
# Should redirect to Authentik login if not authenticated

# ============================================================
# Network Policy Verification
# ============================================================

# Verify policy exists
kubectl --context infra get ciliumnetworkpolicy -n observability grafana

# Test connectivity from Grafana to VictoriaMetrics
kubectl --context infra exec -n observability deploy/grafana -- wget -qO- http://vmsingle-vmsingle.observability.svc:8429/health
```

### Anti-Patterns to Avoid

1. **DO NOT** use the old plugin ID `victoriametrics-datasource` - must use `victoriametrics-metrics-datasource`
2. **DO NOT** provision datasources manually in UI - use ConfigMap/sidecar for GitOps consistency
3. **DO NOT** hardcode OAuth credentials in values.yaml - use ExternalSecret
4. **DO NOT** forget to add `cluster` variable to dashboard templates for multi-cluster filtering
5. **DO NOT** skip network policies - Grafana is internet-accessible via Cloudflare Tunnel
6. **DO NOT** use `localhost` URLs for datasources - use service DNS names
7. **DO NOT** forget dependencies in ks.yaml - Grafana needs VictoriaMetrics/VictoriaLogs running first
8. **DO NOT** set `isDefault: true` for VictoriaLogs - only VictoriaMetrics should be default

### Edge Cases

**Scenario: Plugin installation fails**
- Check Grafana logs for plugin download errors
- Verify network egress to `grafana.com` is allowed
- Consider pre-downloading plugins and mounting as volume

**Scenario: OAuth login loop**
- Verify redirect URI in Authentik matches exactly
- Check `root_url` in grafana.ini matches actual URL
- Verify Authentik application is not disabled

**Scenario: Dashboards not appearing**
- Verify ConfigMaps have `grafana_dashboard: "1"` label
- Check sidecar logs for discovery errors
- Verify JSON syntax in dashboard ConfigMaps

**Scenario: Multi-cluster data not showing**
- Verify VMAgent on apps cluster is sending data with `cluster=apps` label
- Check VictoriaMetrics for metrics with cluster label: `curl localhost:8428/api/v1/label/cluster/values`
- Verify dashboard queries use `cluster=~"$cluster"` filter

**Scenario: Grafana slow to load**
- Check VictoriaMetrics query latency (should be < 2s)
- Review dashboard complexity and query efficiency
- Consider increasing Grafana resources

### Dependencies

| This Story Depends On | Required For |
|-----------------------|--------------|
| Story 6.1 (VictoriaMetrics on Infra) | Metrics datasource |
| Story 6.2 (VictoriaLogs on Infra) | Logs datasource |
| Story 6.3 (Apps Cluster Agents) | Multi-cluster data availability |
| Authentik (kubernetes/apps/security/authentik) | SSO authentication |
| Rook-Ceph (Story 2.1) | Persistent storage |

| Stories That Depend On This | Reason |
|-----------------------------|--------|
| Story 6.5 (External-DNS and Alerting) | Alerts visualization |
| Story 5.4 (Multi-Cluster Validation) | Cross-cluster visibility verification |

### Previous Story Learnings (Story 6.3)

From Apps Cluster Observability Agents deployment:
- Multi-cluster data flows are working: `cluster=apps` and `cluster=infra` labels in use
- VMAgent remote-write pattern is established
- Fluent-bit shipping logs with cluster labels
- Cross-cluster network connectivity patterns documented
- Buffer configurations for resilience during outages

### Project Structure Alignment

**App Location Rule Compliance:**
- This is an infra-cluster-only deployment: `clusters/infra/apps/observability/grafana/`
- NOT shared (Grafana is centralized on infra cluster only)
- Follows same directory pattern as other observability components

**Naming Conventions:**
- HelmRelease name: `grafana`
- Namespace: `observability` (consistent with VictoriaMetrics/VictoriaLogs)
- Labels follow `app.kubernetes.io/name: grafana` pattern

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Hub/Spoke Observability Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Observability Component Locations]
- [Source: _bmad-output/planning-artifacts/prd.md#FR41-FR51 Observability Requirements]
- [Source: docs/project-context.md#Observability Pattern]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.4]
- [Source: _bmad-output/implementation-artifacts/6-3-configure-apps-cluster-observability-agents.md]

### External Documentation

**Grafana:**
- [Grafana Helm Chart](https://github.com/grafana/helm-charts/tree/main/charts/grafana)
- [Grafana Generic OAuth Configuration](https://grafana.com/docs/grafana/latest/setup-grafana/configure-access/configure-authentication/generic-oauth/)
- [Grafana Provisioning Datasources](https://grafana.com/docs/grafana/latest/administration/provisioning/#datasources)
- [Grafana Provisioning Dashboards](https://grafana.com/docs/grafana/latest/administration/provisioning/#dashboards)

**VictoriaMetrics Datasource:**
- [VictoriaMetrics Grafana Datasource](https://docs.victoriametrics.com/victoriametrics/victoriametrics-datasource/)
- [VictoriaMetrics Plugin on Grafana](https://grafana.com/grafana/plugins/victoriametrics-metrics-datasource/)

**VictoriaLogs Datasource:**
- [VictoriaLogs Grafana Datasource](https://docs.victoriametrics.com/victorialogs/victorialogs-datasource/)
- [VictoriaLogs Plugin on Grafana](https://grafana.com/grafana/plugins/victoriametrics-logs-datasource/)

**Authentik Integration:**
- [Configuring Grafana OAuth with Authentik](https://timvw.be/2025/03/19/configuring-grafana-oauth-with-authentik/)
- [Authentik Helm Chart](https://charts.goauthentik.io)

**Community Dashboards:**
- [Kubernetes Cluster Overview](https://grafana.com/grafana/dashboards/315)
- [Flux GitOps Dashboard](https://grafana.com/grafana/dashboards/16714)
- [Node Exporter Dashboard](https://grafana.com/grafana/dashboards/1860)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
