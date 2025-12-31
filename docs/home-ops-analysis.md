# home-ops Repository Analysis

## Cluster Identity

| Property | Value |
|----------|-------|
| Cluster Name | k8s |
| API Endpoint | https://k8s.monosense.io:6443 |
| Primary Domain | monosense.dev |
| Secondary Domain | monosense.io |
| Node Network | 10.25.11.0/24 |
| Node IPs | 10.25.11.11-16 |

## Repository Structure

```
home-ops/
├── bootstrap/              # Helmfile-based cluster bootstrap
│   ├── helmfile.d/        # Ordered bootstrap releases
│   └── secrets.yaml.tpl   # Bootstrap secret templates
├── kubernetes/
│   ├── apps/              # Application manifests (16 namespaces)
│   ├── flux/              # Flux configuration
│   │   ├── cluster/       # Cluster-level kustomizations
│   │   └── repositories/  # Helm/OCI repository definitions
│   └── components/        # Reusable kustomize components
├── talos/                  # Talos machine configs (Jinja2 templates)
├── terraform/              # Infrastructure as Code
├── docs/                   # Documentation
├── .github/                # GitHub Actions workflows
├── .renovate/              # Renovate configuration modules
└── .taskfiles/             # Task automation
```

## Namespaces & Applications (80 HelmReleases)

### kube-system (Core Infrastructure)
- cilium (v1.18.2) - eBPF networking
- coredns (v1.44.3) - DNS server
- metrics-server - Metrics collection
- spegel (v0.4.0) - OCI registry mirror
- csi-driver-nfs - NFS CSI driver
- descheduler - Pod rescheduling
- generic-device-plugin - Device framework
- intel-device-plugin - Intel GPU support
- reloader - Config change restarts

### flux-system (GitOps)
- flux-operator (v0.31.0)
- flux-instance (v0.31.0)
- headlamp - K8s dashboard
- tofu-controller - Terraform/OpenTofu controller

### cert-manager
- cert-manager (v1.19.0) - Let's Encrypt integration

### external-secrets
- external-secrets-operator (v0.20.2) - 1Password integration

### networking
- envoy-gateway (v1.5.2) - Gateway API
- external-dns - Cloudflare DNS sync
- cloudflared - Cloudflare tunnel
- multus - Multi-homed networking
- tailscale-operator - VPN integration
- smtp-relay - Email relay
- echo-server - Test server

### observability (16+ tools)
- kube-prometheus-stack (v77.14.0)
- loki - Log aggregation
- promtail - Log collector
- fluentbit - Log forwarding
- victoria-metrics - Metrics database
- victoria-logs - Log storage
- alloy - Data collection
- grafana - Visualization
- keda (v2.17.2) - Event-driven autoscaling
- kromgo - Metrics API
- gatus - Health monitoring
- silence-operator - Alert silence
- blackbox-exporter - Availability probing
- snmp-exporter - Network monitoring
- smartctl-exporter - Disk health
- omada-exporter - Network devices
- speedtest-exporter - Internet speed

### databases
- cloudnative-pg - PostgreSQL operator
- pgadmin - PostgreSQL UI
- dragonfly-operator - Redis/Dragonfly

### storage
- minio - S3-compatible storage

### rook-ceph
- rook-ceph - Distributed storage

### openebs-system
- openebs - Container-attached storage

### volsync-system
- volsync - PV backup/recovery
- snapshot-controller

### system-upgrade
- system-upgrade-controller

### actions-runner-system
- actions-runner-controller
- home-ops-runner
- synergy-flow-runner

### downloads (Media Stack)
- plex - Media streaming
- sonarr - TV automation (PostgreSQL)
- radarr - Movie automation (PostgreSQL)
- qbittorrent - Torrent client (WireGuard VPN)
- prowlarr - Indexer management
- overseerr - Media requests

### selfhosted
- harbor (v2.x) - Container registry
- mattermost - Team chat (PostgreSQL)

### security
- authentik - Identity provider

## Bootstrap Configuration

### Helmfile Deployment Order
1. cilium (v1.18.2) - Network CNI
2. coredns (v1.44.3) - DNS
3. spegel (v0.4.0) - Image mirror
4. cert-manager (v1.19.0) - Certificates
5. flux-operator (v0.31.0)
6. flux-instance (v0.31.0)

### Talos Configuration
- OS: Talos Linux v1.11.2
- Kubernetes: v1.34.1
- Machine types: controlplane, worker
- Network: Bonded 10G interfaces (LACP 802.3ad)
- MTU: 9000 (jumbo frames)
- VLAN support

#### System Extensions
- intel-ucode (CPU microcode)
- i915-ucode (Intel GPU)
- iscsi-tools
- nfsrahead

#### Kernel Tuning
- NFS optimizations
- 10Gb networking (BBR)
- Hugepages for PostgreSQL
- inotify limits

## Helm/OCI Repositories

### HelmRepositories (5)
- fluent
- mattermost
- harbor
- harbor-container-webhook
- rocketchat

### OCI Repositories (11)
- app-template (v4.3.0)
- cert-manager (v1.19.0)
- cilium (v1.18.2)
- coredns (v1.44.3)
- spegel (v0.4.0)
- external-secrets (v0.20.2)
- envoy-gateway (v1.5.2)
- keda (v2.17.2)
- kube-prometheus-stack (v77.14.0)
- flux-operator (v0.31.0)
- flux-instance (v0.31.0)

## Infrastructure Patterns

### Kustomize Components
Reusable components in `kubernetes/components/`:
- cnpg (CloudNative PostgreSQL)
- volsync (Backup)
- gatus (Health checks)
- dragonfly
- nfs-scaler
- secpol

### GitHub Actions (8 workflows)
- renovate.yaml - Dependency updates
- flux-local.yaml - Flux validation
- image-pull.yaml - Image pre-pulling
- label-sync.yaml - Label sync
- labeler.yaml - PR labeling
- tag.yaml - Git tags
- terraform-diff.yaml - TF plan
- terraform-publish.yaml - TF apply

### Renovate Groups (10)
- 1Password Connect
- Actions Runner Controller
- Cert-Manager
- Cilium
- CoreDNS
- External Secrets
- Flux
- Intel Device Plugins
- Rook-Ceph
- Spegel

## External Integrations

### 1Password Connect
- ClusterSecretStore: `onepassword`
- Vaults: Infra, Prod, Dev
- 37 ExternalSecret resources

### Cloudflare
- cloudflared tunnel
- External-DNS sync

### GitHub
- Actions Runner Controller
- Self-hosted runners

## Key Endpoints

| Service | URL |
|---------|-----|
| Metrics | https://kromgo.monosense.dev |
| Status | https://status.monosense.dev |
