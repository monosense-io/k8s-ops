# Story 2.5: Configure Cilium LoadBalancer IP Pools

Status: ready-for-dev

## Story

As a **platform operator**,
I want **Cilium BGP Control Plane announcing LoadBalancer IPs from configured IP pools**,
So that **services are accessible via predictable IP addresses and the infrastructure integrates with my network via BGP peering with the Juniper SRX 320 router**.

## Acceptance Criteria

1. **Given** Cilium with BGP Control Plane enabled
   **When** IP pools are configured
   **Then** `infrastructure/base/cilium/` contains:
   - CiliumLoadBalancerIPPool for infra cluster IP range
   - CiliumBGPPeeringPolicy (or v2 BGP resources) for Juniper SRX 320 peering

2. **And** BGP session establishes with upstream router (ASN configured)

3. **And** creating a LoadBalancer Service allocates IP from pool

4. **And** IP is announced via BGP and reachable from network

5. **And** `cilium bgp peers` shows established session

## Tasks / Subtasks

- [ ] Task 1: Create Cilium BGP Resources Directory Structure (AC: #1)
  - [ ] Create `infrastructure/base/cilium/bgp/` directory for BGP resources
  - [ ] Create `infrastructure/base/cilium/bgp/kustomization.yaml`
  - [ ] Determine whether to use legacy CiliumBGPPeeringPolicy or new CiliumBGPClusterConfig v2 APIs
  - [ ] Note: v2 APIs (CiliumBGPClusterConfig, CiliumBGPPeerConfig, CiliumBGPAdvertisement) are recommended for Cilium 1.18+

- [ ] Task 2: Create CiliumLoadBalancerIPPool for Infra Cluster (AC: #1, #3)
  - [ ] Create `infrastructure/base/cilium/bgp/loadbalancer-ip-pool-infra.yaml`
  - [ ] Configure IP range for infra cluster LoadBalancer services
  - [ ] Set `allowFirstLastIPs: "No"` to reserve network/broadcast addresses
  - [ ] Add serviceSelector to restrict pool to specific namespaces or labels if needed
  - [ ] Configure pool name: `infra-lb-pool`

- [ ] Task 3: Create CiliumLoadBalancerIPPool for Apps Cluster (AC: #1, #3)
  - [ ] Create `infrastructure/base/cilium/bgp/loadbalancer-ip-pool-apps.yaml`
  - [ ] Configure IP range for apps cluster LoadBalancer services
  - [ ] Set `allowFirstLastIPs: "No"` to reserve network/broadcast addresses
  - [ ] Configure pool name: `apps-lb-pool`
  - [ ] Use Flux variable substitution `${CLUSTER_NAME}` for cluster-specific pool selection

- [ ] Task 4: Create CiliumBGPClusterConfig (v2 API) (AC: #1, #2)
  - [ ] Create `infrastructure/base/cilium/bgp/bgp-cluster-config.yaml`
  - [ ] Configure nodeSelector to match control plane or all nodes
  - [ ] Set localASN for the cluster (private ASN range 64512-65534)
  - [ ] Configure Juniper SRX 320 as peer with its peerASN and peerAddress
  - [ ] Reference CiliumBGPPeerConfig for session parameters
  - [ ] Configure localPort: 179 (requires CAP_NET_BIND_SERVICE)

- [ ] Task 5: Create CiliumBGPPeerConfig (AC: #2)
  - [ ] Create `infrastructure/base/cilium/bgp/bgp-peer-config.yaml`
  - [ ] Configure BGP timers optimized for datacenter:
    - connectRetryTimeSeconds: 5
    - holdTimeSeconds: 9
    - keepAliveTimeSeconds: 3
  - [ ] Enable graceful restart for session continuity during agent restarts
  - [ ] Configure address families (IPv4 unicast)
  - [ ] Reference CiliumBGPAdvertisement for route advertisement

- [ ] Task 6: Create CiliumBGPAdvertisement (AC: #4)
  - [ ] Create `infrastructure/base/cilium/bgp/bgp-advertisement.yaml`
  - [ ] Configure advertisementType: "Service" for LoadBalancer VIPs
  - [ ] Set service.addresses to include: LoadBalancerIP
  - [ ] Add communities for route identification (optional)
  - [ ] Consider adding PodCIDR advertisement if inter-cluster routing needed

- [ ] Task 7: Update infrastructure/base/cilium Kustomization (AC: #1)
  - [ ] Update `infrastructure/base/cilium/kustomization.yaml` to include bgp/ resources
  - [ ] Ensure proper resource ordering (IP pools before BGP configs)
  - [ ] Verify Cilium Helm values enable BGP Control Plane

- [ ] Task 8: Configure Juniper SRX 320 BGP Peering (Manual/Documented) (AC: #2)
  - [ ] Document required Juniper SRX 320 configuration commands
  - [ ] Enable host-inbound-traffic protocols bgp on the zone
  - [ ] Configure BGP neighbor with Cilium node IPs
  - [ ] Set peer ASN to match cluster localASN
  - [ ] Configure import/export policies on SRX to accept/advertise routes
  - [ ] Add to `docs/runbooks/cilium.md`

- [ ] Task 9: Verify BGP Session Establishment (AC: #2, #5)
  - [ ] Deploy Cilium BGP configuration to infra cluster
  - [ ] Run `cilium bgp peers` to verify session state
  - [ ] Check BGP session shows "Established" state
  - [ ] Verify peering with correct remote ASN
  - [ ] Check Cilium agent logs for any BGP errors

- [ ] Task 10: Verify LoadBalancer IP Allocation (AC: #3)
  - [ ] Create test LoadBalancer Service
  - [ ] Verify Service receives IP from configured pool
  - [ ] Check `kubectl get svc` shows EXTERNAL-IP
  - [ ] Verify CiliumLoadBalancerIPPool status shows allocation
  - [ ] Clean up test service after verification

- [ ] Task 11: Verify BGP Route Advertisement (AC: #4)
  - [ ] Check `cilium bgp routes advertised` shows LoadBalancer IP
  - [ ] Verify route appears in Juniper SRX 320 routing table
  - [ ] Test connectivity to LoadBalancer IP from network
  - [ ] Verify traffic reaches the service correctly

- [ ] Task 12: Document and Finalize
  - [ ] Update `docs/runbooks/cilium.md` with BGP troubleshooting section
  - [ ] Document BGP peering verification commands
  - [ ] Document IP pool management procedures
  - [ ] Add network topology diagram reference

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document (architecture.md):**

1. **Technology Stack Versions (December 2025):**
   | Component | Version | Notes |
   |-----------|---------|-------|
   | Cilium | v1.18.5 | eBPF, BGP Control Plane |
   | Juniper SRX 320 | - | Upstream BGP router |

2. **FRs Covered:**
   - FR25: Operator can allocate LoadBalancer IPs from defined Cilium IP pools
   - FR21: Operator can deploy Cilium CNI with eBPF and native routing

3. **Cilium Cluster Identity (Critical):**
   | Cluster | cluster.id | cluster.name | Network CIDR |
   |---------|------------|--------------|--------------|
   | Infra | 1 | `infra` | 10.25.11.0/24 |
   | Apps | 2 | `apps` | 10.25.13.0/24 |

4. **BGP Peering with Juniper SRX 320:**
   - Both clusters peer with the same upstream router
   - Each cluster advertises its own LoadBalancer IP pool
   - Private ASN range: 64512-65534 recommended

5. **Network Topology:**
   - Infra cluster: 10.25.11.0/24
   - Apps cluster: 10.25.13.0/24
   - MTU: 9000
   - LACP bonding enabled

### Project Context Rules (Critical)

**From project-context.md:**

1. **Cilium Version Constraints:**
   - Cilium v1.18.5 with eBPF datapath
   - cluster.id: infra=1, apps=2 (for future Cluster Mesh)

2. **App Location Rules:**
   - Cilium BGP resources go in `infrastructure/base/cilium/` (shared infrastructure)
   - Deployed to BOTH clusters via Flux reconciliation

3. **File Naming Standards:**
   - Use `.yaml` extension (not `.yml`)
   - Use `kustomization.yaml` for Kustomize files

4. **Flux Variable Substitution:**
   - Use `${VARIABLE_NAME}` syntax
   - Variables from `cluster-vars` ConfigMap via `postBuild.substituteFrom`

### Cilium BGP Control Plane v1.18 Configuration

**From Web Research (December 2025):**

1. **API Version Decision:**
   - **Legacy (v1):** CiliumBGPPeeringPolicy - will be deprecated
   - **New (v2):** CiliumBGPClusterConfig, CiliumBGPPeerConfig, CiliumBGPAdvertisement
   - **Recommendation:** Use v2 APIs for new deployments in Cilium 1.18+
   - **Warning:** Do NOT mix v1 and v2 resources - choose one or the other

2. **CiliumLoadBalancerIPPool Configuration:**
   ```yaml
   apiVersion: cilium.io/v2
   kind: CiliumLoadBalancerIPPool
   metadata:
     name: infra-lb-pool
   spec:
     blocks:
       - cidr: "10.25.11.200/28"  # Example: 14 usable IPs
     allowFirstLastIPs: "No"
   ```

3. **CiliumBGPClusterConfig (v2 API):**
   ```yaml
   apiVersion: cilium.io/v2
   kind: CiliumBGPClusterConfig
   metadata:
     name: cilium-bgp
   spec:
     nodeSelector:
       matchLabels:
         kubernetes.io/os: linux
     bgpInstances:
       - name: "cluster-bgp"
         localASN: 65001  # Private ASN for infra cluster
         localPort: 179
         peers:
           - name: "juniper-srx"
             peerASN: 65000  # SRX ASN
             peerAddress: "10.25.11.1"  # SRX interface IP
             peerConfigRef:
               name: "cilium-peer-config"
   ```

4. **CiliumBGPPeerConfig:**
   ```yaml
   apiVersion: cilium.io/v2
   kind: CiliumBGPPeerConfig
   metadata:
     name: cilium-peer-config
   spec:
     timers:
       connectRetryTimeSeconds: 5
       holdTimeSeconds: 9
       keepAliveTimeSeconds: 3
     gracefulRestart:
       enabled: true
       restartTimeSeconds: 15
     families:
       - afi: ipv4
         safi: unicast
         advertisements:
           matchLabels:
             advertise: "bgp"
   ```

5. **CiliumBGPAdvertisement:**
   ```yaml
   apiVersion: cilium.io/v2
   kind: CiliumBGPAdvertisement
   metadata:
     name: bgp-advertisements
     labels:
       advertise: bgp
   spec:
     advertisements:
       - advertisementType: "Service"
         service:
           addresses:
             - LoadBalancerIP
   ```

6. **Juniper SRX 320 Configuration (Required on Router):**
   ```
   # Enable BGP on the interface/zone
   set security zones security-zone trust host-inbound-traffic protocols bgp

   # Configure BGP routing
   set routing-options autonomous-system 65000
   set protocols bgp group k8s-clusters type external
   set protocols bgp group k8s-clusters peer-as 65001
   set protocols bgp group k8s-clusters neighbor 10.25.11.11
   set protocols bgp group k8s-clusters neighbor 10.25.11.12
   set protocols bgp group k8s-clusters neighbor 10.25.11.13
   # ... for all control plane nodes

   # Import policy to accept routes
   set policy-options policy-statement accept-k8s-routes term 1 then accept
   set protocols bgp group k8s-clusters import accept-k8s-routes
   ```

7. **Key Considerations:**
   - BGP session lost during Cilium agent restart (mitigated by graceful restart)
   - Graceful restart keeps routes for `restartTimeSeconds` during agent restart
   - Port 179 requires CAP_NET_BIND_SERVICE capability
   - ECMP path limits on routers may require checking with network admin

### Directory Structure

```
infrastructure/base/cilium/
├── bgp/
│   ├── kustomization.yaml
│   ├── loadbalancer-ip-pool-infra.yaml
│   ├── loadbalancer-ip-pool-apps.yaml
│   ├── bgp-cluster-config.yaml
│   ├── bgp-peer-config.yaml
│   └── bgp-advertisement.yaml
├── app/
│   ├── helmrelease.yaml
│   └── kustomization.yaml
└── kustomization.yaml
```

### Resource Templates

**loadbalancer-ip-pool-infra.yaml:**
```yaml
---
apiVersion: cilium.io/v2
kind: CiliumLoadBalancerIPPool
metadata:
  name: infra-lb-pool
spec:
  blocks:
    - cidr: "${CLUSTER_LB_CIDR}"  # e.g., 10.25.11.200/28
  allowFirstLastIPs: "No"
  serviceSelector:
    matchExpressions:
      - key: io.kubernetes.service.namespace
        operator: NotIn
        values:
          - kube-system  # Exclude kube-system services if needed
```

**bgp-cluster-config.yaml:**
```yaml
---
apiVersion: cilium.io/v2
kind: CiliumBGPClusterConfig
metadata:
  name: cilium-bgp-${CLUSTER_NAME}
spec:
  nodeSelector:
    matchLabels:
      kubernetes.io/os: linux
  bgpInstances:
    - name: "bgp-instance-${CLUSTER_ID}"
      localASN: ${CLUSTER_BGP_ASN}
      localPort: 179
      peers:
        - name: "juniper-srx-320"
          peerASN: ${ROUTER_BGP_ASN}
          peerAddress: "${ROUTER_IP}"
          peerConfigRef:
            name: "cilium-peer-config"
```

**bgp-peer-config.yaml:**
```yaml
---
apiVersion: cilium.io/v2
kind: CiliumBGPPeerConfig
metadata:
  name: cilium-peer-config
spec:
  timers:
    connectRetryTimeSeconds: 5
    holdTimeSeconds: 9
    keepAliveTimeSeconds: 3
  gracefulRestart:
    enabled: true
    restartTimeSeconds: 15
  families:
    - afi: ipv4
      safi: unicast
      advertisements:
        matchLabels:
          advertise: "bgp"
```

**bgp-advertisement.yaml:**
```yaml
---
apiVersion: cilium.io/v2
kind: CiliumBGPAdvertisement
metadata:
  name: bgp-advertisements
  labels:
    advertise: bgp
spec:
  advertisements:
    - advertisementType: "Service"
      service:
        addresses:
          - LoadBalancerIP
      attributes:
        communities:
          standard:
            - "${CLUSTER_BGP_ASN}:100"  # Community for identification
```

**bgp/kustomization.yaml:**
```yaml
---
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - loadbalancer-ip-pool-infra.yaml
  - loadbalancer-ip-pool-apps.yaml
  - bgp-cluster-config.yaml
  - bgp-peer-config.yaml
  - bgp-advertisement.yaml
```

### Previous Story Intelligence

**From Story 2.4 (Deploy cert-manager with DNS-01 Validation):**
- Network policies in Tier 1 allow controlled egress
- ExternalSecret pattern for Cloudflare integration established
- Flux Kustomization path format: `./kubernetes/apps/...` or `./infrastructure/base/...`

**From Story 2.3 (Implement Zero Trust Network Policies):**
- Cilium CNI is operational with network policies
- Default-deny with tiered exceptions pattern established
- Tier 0 namespaces (kube-system, flux-system) have unrestricted access

**Key Learnings from Previous Stories:**
- Use `.yaml` extension consistently
- Infrastructure resources go in `infrastructure/base/`
- Use Flux variable substitution for cluster-specific values
- Test in staging/infra first before apps cluster

### Cluster Variables Required

Add to `clusters/{cluster}/flux/cluster-vars.yaml`:

```yaml
# Infra cluster
CLUSTER_LB_CIDR: "10.25.11.200/28"
CLUSTER_BGP_ASN: "65001"
ROUTER_BGP_ASN: "65000"
ROUTER_IP: "10.25.11.1"

# Apps cluster
CLUSTER_LB_CIDR: "10.25.13.200/28"
CLUSTER_BGP_ASN: "65002"
ROUTER_BGP_ASN: "65000"
ROUTER_IP: "10.25.13.1"
```

### Verification Commands

```bash
# Check Cilium BGP status
cilium bgp peers
cilium bgp routes advertised ipv4 unicast

# Check LoadBalancer IP Pool status
kubectl get ciliumloadbalancerippools
kubectl describe ciliumloadbalancerippools infra-lb-pool

# Check BGP resources (v2 API)
kubectl get ciliumbgpclusterconfigs
kubectl get ciliumbgppeerconfigs
kubectl get ciliumbgpadvertisements

# Check Cilium agent BGP logs
kubectl logs -n kube-system -l k8s-app=cilium --tail=100 | grep -i bgp

# Test LoadBalancer Service
kubectl create deployment nginx --image=nginx --port=80
kubectl expose deployment nginx --type=LoadBalancer --port=80
kubectl get svc nginx
# Verify EXTERNAL-IP is from the configured pool
kubectl delete deployment nginx
kubectl delete svc nginx

# From Juniper SRX 320 (SSH to router)
show bgp summary
show bgp neighbor
show route protocol bgp
```

### Critical Implementation Rules

1. **API Version Selection:**
   - Use v2 APIs (CiliumBGPClusterConfig, etc.) for Cilium 1.18+
   - Do NOT mix legacy CiliumBGPPeeringPolicy with v2 resources

2. **Node Selection:**
   - nodeSelector should match nodes that will peer with BGP router
   - Consider selecting only control plane nodes or all nodes based on topology

3. **ASN Planning:**
   - Use private ASN range: 64512-65534
   - Assign unique ASN per cluster for eBGP peering
   - Router ASN should be consistent across clusters

4. **IP Pool Planning:**
   - Ensure IP pools don't overlap between clusters
   - Reserve sufficient IPs for expected LoadBalancer services
   - Consider future growth in CIDR allocation

5. **Graceful Restart:**
   - Enable to prevent route withdrawal during agent restarts
   - Set reasonable restartTimeSeconds (15s typical)

6. **Port 179:**
   - Standard BGP port requires elevated privileges
   - Cilium Helm values must enable this capability

### Project Structure Notes

- **Location:** `infrastructure/base/cilium/bgp/` for shared BGP configuration
- **Deployment:** BOTH clusters via Flux reconciliation
- **Variable Substitution:** Cluster-specific values from cluster-vars ConfigMap

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.5: Configure Cilium LoadBalancer IP Pools]
- [Source: _bmad-output/planning-artifacts/architecture.md#Cilium Cluster Identity]
- [Source: docs/project-context.md#Technology Stack & Versions]
- [Cilium BGP Control Plane v2 Documentation](https://docs.cilium.io/en/stable/network/bgp-control-plane/bgp-control-plane-v2/)
- [Cilium LB IPAM Documentation](https://docs.cilium.io/en/stable/network/lb-ipam/)
- [Juniper BGP Configuration](https://www.juniper.net/documentation/us/en/software/junos/bgp/topics/topic-map/bgp-peering-sessions.html)

### Validation Checklist

Before marking complete, verify:
- [ ] `infrastructure/base/cilium/bgp/` directory structure created
- [ ] CiliumLoadBalancerIPPool resources configured for both clusters
- [ ] CiliumBGPClusterConfig deployed with correct ASN and peer configuration
- [ ] CiliumBGPPeerConfig with optimized timers and graceful restart
- [ ] CiliumBGPAdvertisement configured for LoadBalancerIP advertisement
- [ ] BGP session shows "Established" via `cilium bgp peers`
- [ ] Test LoadBalancer Service receives IP from pool
- [ ] Advertised routes visible via `cilium bgp routes advertised`
- [ ] Routes appear in Juniper SRX 320 routing table
- [ ] Traffic reaches LoadBalancer services from network
- [ ] Runbook documentation updated with BGP troubleshooting

### Git Commit Message Format

```
feat(cilium): configure BGP Control Plane and LoadBalancer IP pools

- Add CiliumLoadBalancerIPPool for infra and apps clusters
- Configure CiliumBGPClusterConfig v2 API for Juniper SRX 320 peering
- Enable graceful restart for session continuity
- Add LoadBalancerIP service advertisement
- FR25: Allocate LoadBalancer IPs from Cilium pools
- FR21: Cilium CNI with eBPF and BGP integration
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
