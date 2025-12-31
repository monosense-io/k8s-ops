# Story 2.3: Implement Zero Trust Network Policies

Status: ready-for-dev

## Story

As a **platform operator**,
I want **default-deny network policies with tiered exceptions**,
So that **pod-to-pod communication is secure by default and I have defense-in-depth security**.

## Acceptance Criteria

1. **Given** Cilium CNI is operational
   **When** Zero Trust network policies are deployed
   **Then** `kubernetes/apps/security/network-policies/` contains:
   - CiliumClusterwideNetworkPolicy `default-deny-all` (excludes kube-system, flux-system)
   - CiliumClusterwideNetworkPolicy `allow-dns` (UDP/53 to kube-dns)
   - CiliumClusterwideNetworkPolicy `allow-metrics-scraping` (from observability namespace)

2. **And** Tier 0 namespaces (kube-system, flux-system) have unrestricted access

3. **And** Tier 1 namespaces (observability, cert-manager, external-secrets) have controlled access

4. **And** Tier 2 namespaces have default-deny requiring explicit CiliumNetworkPolicy

5. **And** `cilium connectivity test` passes after policies are applied

6. **And** debug bypass annotation `policy.cilium.io/enforce=false` works for troubleshooting

## Tasks / Subtasks

- [ ] Task 1: Deploy Hubble Observability Before Policies (AC: #5, #6)
  - [ ] Verify Hubble is enabled in Cilium HelmRelease (clusters/infra/talos bootstrap already configures this)
  - [ ] Verify Hubble UI is accessible for traffic flow visualization
  - [ ] Test `hubble observe` CLI command works from cilium-agent pod
  - [ ] Document baseline traffic patterns before applying policies

- [ ] Task 2: Create Network Policies Directory Structure (AC: #1)
  - [ ] Create `kubernetes/apps/security/network-policies/` directory
  - [ ] Create `kubernetes/apps/security/network-policies/app/` subdirectory for policies
  - [ ] Create `kubernetes/apps/security/network-policies/ks.yaml` Flux Kustomization entry point
  - [ ] Create `kubernetes/apps/security/network-policies/app/kustomization.yaml`

- [ ] Task 3: Implement CiliumClusterwideNetworkPolicy default-deny-all (AC: #1, #4)
  - [ ] Create `kubernetes/apps/security/network-policies/app/default-deny-all.yaml`
  - [ ] Configure `endpointSelector: {}` to match all pods
  - [ ] Set empty `ingress: [{}]` and `egress: [{}]` sections for default deny
  - [ ] Exclude Tier 0 namespaces using `matchExpressions` with NotIn operator
  - [ ] Exclude: kube-system, flux-system, cilium (system namespaces)

- [ ] Task 4: Implement CiliumClusterwideNetworkPolicy allow-dns (AC: #1)
  - [ ] Create `kubernetes/apps/security/network-policies/app/allow-dns-ingress.yaml`
  - [ ] Allow ingress to kube-dns pods from all endpoints on UDP/53
  - [ ] Create `kubernetes/apps/security/network-policies/app/allow-dns-egress.yaml`
  - [ ] Allow egress to kube-dns from all endpoints on UDP/53
  - [ ] Test DNS resolution works after policies applied

- [ ] Task 5: Implement CiliumClusterwideNetworkPolicy allow-metrics-scraping (AC: #1, #3)
  - [ ] Create `kubernetes/apps/security/network-policies/app/allow-metrics-scraping.yaml`
  - [ ] Allow ingress from observability namespace to pods with metrics endpoints
  - [ ] Target pods with standard prometheus scrape labels
  - [ ] Allow port 9090, 8080, and other common metrics ports

- [ ] Task 6: Configure Tier 0 Namespace Exemptions (AC: #2)
  - [ ] Verify Tier 0 namespaces are excluded from default-deny via matchExpressions
  - [ ] Namespaces: kube-system, flux-system, cilium, cilium-secrets
  - [ ] Document that these namespaces have unrestricted network access

- [ ] Task 7: Configure Tier 1 Namespace Policies (AC: #3)
  - [ ] Create `kubernetes/apps/security/network-policies/app/tier1-observability.yaml`
  - [ ] Allow observability namespace to scrape metrics from all namespaces
  - [ ] Allow observability egress to VictoriaMetrics endpoints
  - [ ] Create `kubernetes/apps/security/network-policies/app/tier1-cert-manager.yaml`
  - [ ] Allow cert-manager egress to ACME providers (Let's Encrypt)
  - [ ] Create `kubernetes/apps/security/network-policies/app/tier1-external-secrets.yaml`
  - [ ] Allow external-secrets egress to 1Password Connect

- [ ] Task 8: Configure Flux Dependencies (AC: #1)
  - [ ] Update `kubernetes/apps/security/network-policies/ks.yaml` with proper dependsOn
  - [ ] Network policies depend on cluster-infrastructure (Cilium must be ready)
  - [ ] Add to `kubernetes/apps/security/kustomization.yaml` resource list
  - [ ] Ensure `prune: true` for policy cleanup on removal

- [ ] Task 9: Verify Cilium Connectivity Tests (AC: #5)
  - [ ] Run `cilium connectivity test` on infra cluster
  - [ ] Verify all tests pass with network policies applied
  - [ ] Document any expected failures (if policies are too restrictive)
  - [ ] Adjust policies if legitimate traffic is blocked

- [ ] Task 10: Verify Debug Bypass Works (AC: #6)
  - [ ] Create test pod with annotation `policy.cilium.io/enforce: "false"`
  - [ ] Verify pod can communicate bypassing policies
  - [ ] Document usage in runbook for troubleshooting
  - [ ] Clean up test resources

- [ ] Task 11: Document and Finalize
  - [ ] Update `docs/runbooks/cilium.md` with network policy debugging section
  - [ ] Document tiered namespace strategy
  - [ ] Document how to add Tier 2 app-specific policies
  - [ ] Add verification commands to runbook

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document (architecture.md):**

1. **Zero Trust with Tiered Exceptions Pattern:**
   ```
   Tier 0: System Namespaces (Always Allow)
   ├── kube-system: Full access
   ├── flux-system: Git/registry egress
   └── DNS: Allow from all pods

   Tier 1: Platform Services (Controlled Access)
   ├── observability: Allow scraping from all
   ├── cert-manager: ACME egress
   └── external-secrets: 1Password Connect egress

   Tier 2: Application Namespaces (Default Deny + Explicit Allow)
   ├── Each namespace gets default-deny policy
   ├── Apps define their own ingress/egress rules
   └── Cross-namespace access requires explicit CiliumNetworkPolicy
   ```

2. **Technology Stack Versions (December 2025):**
   | Component | Version | Notes |
   |-----------|---------|-------|
   | Cilium | v1.18.5 | eBPF, BGP Control Plane, CiliumClusterwideNetworkPolicy |
   | Kubernetes | v1.35.0 (in Talos 1.12.0) | Native NetworkPolicy + Cilium extensions |

3. **FRs Covered:**
   - FR22: Operator can configure network policies with default-deny and explicit allows
   - FR23: Operator can temporarily bypass network policies for debugging
   - FR24: Operator can audit network policy state against documented baseline

4. **NFR Requirements:**
   - NFR9: Network isolation - Default-deny network policies; explicit allow required
   - NFR14: RBAC enforcement - No cluster-admin bindings for applications

5. **App Location Rules:**
   - Network policies go in `kubernetes/apps/security/network-policies/` (shared apps)
   - Deployed to BOTH clusters via Flux reconciliation
   - App-specific policies go in the app's own directory

### Project Context Rules (Critical)

**From project-context.md:**

1. **CiliumNetworkPolicy vs CiliumClusterwideNetworkPolicy:**
   - Use `CiliumClusterwideNetworkPolicy` for cluster-wide rules (default-deny, DNS)
   - Use `CiliumNetworkPolicy` for namespace-scoped app-specific rules

2. **Namespace Security Labels:**
   - Tier 2 apps require their own CiliumNetworkPolicy in app directory
   - Include `networkpolicy.yaml` in app's `app/` directory

3. **Flux Kustomization Standards:**
   ```yaml
   apiVersion: kustomize.toolkit.fluxcd.io/v1
   kind: Kustomization
   metadata:
     name: &name network-policies
     namespace: flux-system
   spec:
     targetNamespace: security
     path: ./kubernetes/apps/security/network-policies/app
     prune: true
     sourceRef:
       kind: GitRepository
       name: k8s-ops
     interval: 30m
     dependsOn:
       - name: cluster-infrastructure
   ```

### Cilium v1.18.5 Network Policy Specifics

**From Cilium Documentation and Research (December 2025):**

1. **Policy Enforcement Modes:**
   - **Default:** All traffic allowed until an endpoint is selected by a policy, then traffic is denied unless explicitly permitted
   - **Always:** All traffic denied by default, only explicitly allowed connections permitted
   - **Never:** Policies disabled entirely for selected endpoints

2. **Bidirectional Control (CRITICAL):**
   - Ingress and egress rules operate independently
   - Both directions must be explicitly permitted for complete zero-trust
   - Example: Database needs ingress from app, AND app needs egress to database

3. **Default Deny Pattern:**
   ```yaml
   apiVersion: "cilium.io/v2"
   kind: CiliumClusterwideNetworkPolicy
   metadata:
     name: "default-deny"
   spec:
     description: "Empty ingress and egress policy to enforce default-deny on all endpoints"
     endpointSelector: {}
     ingress:
     - {}
     egress:
     - {}
   ```

4. **DNS Access Pattern (Two Policies Required):**

   **Ingress to kube-dns:**
   ```yaml
   apiVersion: "cilium.io/v2"
   kind: CiliumClusterwideNetworkPolicy
   metadata:
     name: "allow-to-kubedns-ingress"
   spec:
     endpointSelector:
       matchLabels:
         k8s:io.kubernetes.pod.namespace: kube-system
         k8s-app: kube-dns
     ingress:
     - fromEndpoints:
       - {}
       toPorts:
       - ports:
         - port: "53"
           protocol: UDP
   ```

   **Egress from all pods to kube-dns:**
   ```yaml
   apiVersion: "cilium.io/v2"
   kind: CiliumClusterwideNetworkPolicy
   metadata:
     name: "allow-to-kubedns-egress"
   spec:
     endpointSelector: {}
     egress:
     - toEndpoints:
       - matchLabels:
           k8s:io.kubernetes.pod.namespace: kube-system
           k8s-app: kube-dns
       toPorts:
       - ports:
         - port: "53"
           protocol: UDP
   ```

5. **enableDefaultDeny Option:**
   - When using CiliumClusterwideNetworkPolicy, use `enableDefaultDeny` option to avoid accidentally enabling default-deny for pods with no policies applied
   - Set to `false` on allow policies, `true` on deny policies

6. **Label Prefixes:**
   - Use `k8s:` prefix for Kubernetes labels in selectors
   - Example: `k8s:io.kubernetes.pod.namespace: kube-system`

### Directory Structure

```
kubernetes/apps/security/network-policies/
├── app/
│   ├── kustomization.yaml
│   ├── default-deny-all.yaml
│   ├── allow-dns-ingress.yaml
│   ├── allow-dns-egress.yaml
│   ├── allow-metrics-scraping.yaml
│   ├── tier1-observability.yaml
│   ├── tier1-cert-manager.yaml
│   └── tier1-external-secrets.yaml
└── ks.yaml
```

### CiliumClusterwideNetworkPolicy Templates

**default-deny-all.yaml:**
```yaml
---
apiVersion: "cilium.io/v2"
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: default-deny-all
spec:
  description: "Default deny all traffic except for Tier 0 system namespaces"
  endpointSelector:
    matchExpressions:
      - key: k8s:io.kubernetes.pod.namespace
        operator: NotIn
        values:
          - kube-system
          - flux-system
          - cilium
          - cilium-secrets
  ingress:
    - {}
  egress:
    - {}
```

**allow-dns-egress.yaml:**
```yaml
---
apiVersion: "cilium.io/v2"
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: allow-dns-egress
spec:
  description: "Allow all pods to query DNS"
  endpointSelector:
    matchExpressions:
      - key: k8s:io.kubernetes.pod.namespace
        operator: NotIn
        values:
          - kube-system
          - flux-system
          - cilium
  egress:
    - toEndpoints:
        - matchLabels:
            k8s:io.kubernetes.pod.namespace: kube-system
            k8s-app: kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: UDP
            - port: "53"
              protocol: TCP
```

**allow-dns-ingress.yaml:**
```yaml
---
apiVersion: "cilium.io/v2"
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: allow-dns-ingress
spec:
  description: "Allow DNS server to receive queries from all pods"
  endpointSelector:
    matchLabels:
      k8s:io.kubernetes.pod.namespace: kube-system
      k8s-app: kube-dns
  ingress:
    - fromEndpoints:
        - {}
      toPorts:
        - ports:
            - port: "53"
              protocol: UDP
            - port: "53"
              protocol: TCP
```

**allow-metrics-scraping.yaml:**
```yaml
---
apiVersion: "cilium.io/v2"
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: allow-metrics-scraping
spec:
  description: "Allow observability namespace to scrape metrics from all pods"
  endpointSelector: {}
  ingress:
    - fromEndpoints:
        - matchLabels:
            k8s:io.kubernetes.pod.namespace: observability
      toPorts:
        - ports:
            - port: "9090"
              protocol: TCP
            - port: "8080"
              protocol: TCP
            - port: "9100"
              protocol: TCP
            - port: "9115"
              protocol: TCP
            - port: "9153"
              protocol: TCP
```

**tier1-observability.yaml:**
```yaml
---
apiVersion: "cilium.io/v2"
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: tier1-observability-egress
spec:
  description: "Allow observability namespace full egress for scraping and remote-write"
  endpointSelector:
    matchLabels:
      k8s:io.kubernetes.pod.namespace: observability
  egress:
    - {}  # Full egress for VMAgent remote-write and scraping
```

**tier1-cert-manager.yaml:**
```yaml
---
apiVersion: "cilium.io/v2"
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: tier1-cert-manager-egress
spec:
  description: "Allow cert-manager egress to ACME providers"
  endpointSelector:
    matchLabels:
      k8s:io.kubernetes.pod.namespace: cert-manager
  egress:
    - toFQDNs:
        - matchPattern: "*.letsencrypt.org"
        - matchPattern: "*.cloudflare.com"
      toPorts:
        - ports:
            - port: "443"
              protocol: TCP
    - toEndpoints:
        - matchLabels:
            k8s:io.kubernetes.pod.namespace: kube-system
            k8s-app: kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: UDP
```

**tier1-external-secrets.yaml:**
```yaml
---
apiVersion: "cilium.io/v2"
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: tier1-external-secrets-egress
spec:
  description: "Allow external-secrets egress to 1Password Connect"
  endpointSelector:
    matchLabels:
      k8s:io.kubernetes.pod.namespace: external-secrets
  egress:
    - toEndpoints:
        - matchLabels:
            k8s:io.kubernetes.pod.namespace: external-secrets
            app.kubernetes.io/name: onepassword-connect
      toPorts:
        - ports:
            - port: "8080"
              protocol: TCP
    - toEndpoints:
        - matchLabels:
            k8s:io.kubernetes.pod.namespace: kube-system
            k8s-app: kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: UDP
```

### Flux Kustomization Template

```yaml
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name network-policies
  namespace: flux-system
spec:
  targetNamespace: security
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./kubernetes/apps/security/network-policies/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: true
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  dependsOn:
    - name: cluster-infrastructure
```

### Previous Story Intelligence

**From Story 2.2 (Configure OpenEBS Local Storage):**
- OpenEBS v4.4.0 LocalPV provisioner is operational
- StorageClass `openebs-hostpath` is available for CNPG
- Flux Kustomization dependency patterns established
- Privileged namespace pattern for storage operators

**From Story 2.1 (Deploy Rook-Ceph Storage Cluster):**
- Rook-Ceph v1.18.8 is operational
- StorageClass `ceph-block` is available for general apps
- Infrastructure base pattern established

**Key Learnings from Previous Stories:**
- Use `.yaml` extension consistently
- Flux Kustomization path uses relative format: `./kubernetes/apps/...`
- Use `wait: true` for infrastructure components
- Deploy Hubble BEFORE applying network policies for observability

### Latest Technical Information (December 2025)

**Cilium v1.18.5 Network Policy Key Information:**

1. **Policy Import Method:**
   - Direct CLI/API import is deprecated as of v1.18
   - Use Kubernetes CRDs exclusively (CiliumNetworkPolicy, CiliumClusterwideNetworkPolicy)
   - Policies automatically distributed to all agents

2. **Zero Trust Best Practices:**
   - Deploy Hubble before enabling policies for traffic visibility
   - Start with monitoring (policy-verdict) before enforcement
   - Use `hubble observe` to diagnose connectivity issues
   - Test policies incrementally, not all at once

3. **Important Caveats:**
   - Empty ingress `- {}` means "allow nothing" (not "allow all")
   - FQDN-based policies require DNS proxy to be enabled
   - Node traffic (host networking) requires separate policies

4. **Hubble Commands for Debugging:**
   ```bash
   # Watch policy verdicts
   hubble observe --verdict DROPPED

   # Watch traffic for specific namespace
   hubble observe -n business

   # Watch traffic to specific pod
   hubble observe --to-pod business/odoo-xxx
   ```

5. **Debug Bypass Annotation:**
   ```yaml
   metadata:
     annotations:
       policy.cilium.io/enforce: "false"
   ```
   This disables policy enforcement for the specific pod.

### Verification Commands

```bash
# Check CiliumClusterwideNetworkPolicy resources
kubectl get ccnp -A

# Describe specific policy
kubectl describe ccnp default-deny-all

# Check Cilium policy status
cilium policy get

# Run connectivity test
cilium connectivity test

# Watch policy verdicts in Hubble
kubectl exec -n cilium -it ds/cilium -- hubble observe --verdict DROPPED

# Check endpoint policy status
cilium endpoint list

# Verify DNS still works
kubectl run test-dns --image=busybox --rm -it --restart=Never -- nslookup kubernetes.default

# Test cross-namespace communication (should fail for Tier 2)
kubectl exec -n business deploy/odoo -- curl -v http://n8n.business:5678/health

# Verify Flux reconciliation
flux get kustomization network-policies
```

### Critical Implementation Rules

1. **Policy Order:**
   - Deploy Hubble FIRST for observability
   - Apply allow-dns policies BEFORE default-deny
   - Apply tier1 policies BEFORE default-deny
   - Apply default-deny LAST

2. **Bidirectional Rules (CRITICAL):**
   - For every allow, consider BOTH ingress AND egress
   - DNS requires both ingress to kube-dns AND egress from pods
   - Metrics scraping requires ingress to targets AND egress from scraper

3. **Tier 0 Exclusions:**
   - NEVER apply restrictive policies to kube-system, flux-system
   - Use `matchExpressions` with `NotIn` operator to exclude

4. **Testing Strategy:**
   - Use `hubble observe` before and after each policy change
   - Verify critical paths: DNS, metrics, external-secrets, cert-manager
   - Run `cilium connectivity test` as final validation

5. **Rollback Strategy:**
   - Keep policies in Git with version control
   - Use `flux suspend kustomization network-policies` to pause enforcement
   - Delete individual policies with `kubectl delete ccnp <name>` if needed

### Project Structure Notes

- **Alignment:** Network policies follow shared app pattern in `kubernetes/apps/`
- **Path:** `kubernetes/apps/security/network-policies/` for cluster-wide policies
- **Deployed to:** BOTH clusters (infra and apps) via Flux reconciliation
- **App-specific:** Tier 2 apps add their own CiliumNetworkPolicy in `app/networkpolicy.yaml`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.3: Implement Zero Trust Network Policies]
- [Source: _bmad-output/planning-artifacts/architecture.md#Decision 5: Network Policy Pattern]
- [Source: docs/project-context.md#Critical Don't-Miss Rules]
- [Cilium 1.18.5 Network Policy Documentation](https://docs.cilium.io/en/stable/security/policy/index.html)
- [Zero Trust K3s Network With Cilium](https://mmacleod.ca/2025/04/zero-trust-k3s-network-with-cilium/)
- [CNCF: Safely Managing Cilium Network Policies](https://www.cncf.io/blog/2025/11/06/safely-managing-cilium-network-policies-in-kubernetes-testing-and-simulation-techniques/)

### Validation Checklist

Before marking complete, verify:
- [ ] Hubble is deployed and observing traffic
- [ ] `kubernetes/apps/security/network-policies/` directory structure created
- [ ] CiliumClusterwideNetworkPolicy `default-deny-all` excludes Tier 0 namespaces
- [ ] CiliumClusterwideNetworkPolicy `allow-dns-ingress` and `allow-dns-egress` deployed
- [ ] CiliumClusterwideNetworkPolicy `allow-metrics-scraping` deployed
- [ ] Tier 1 policies for observability, cert-manager, external-secrets deployed
- [ ] DNS resolution works for all pods (`nslookup kubernetes.default`)
- [ ] VictoriaMetrics/VMAgent can scrape metrics from all namespaces
- [ ] cert-manager can reach Let's Encrypt ACME endpoints
- [ ] External Secrets Operator can reach 1Password Connect
- [ ] `cilium connectivity test` passes
- [ ] Debug bypass annotation works for troubleshooting
- [ ] Flux reconciliation successful on both clusters
- [ ] Runbook documentation updated with policy debugging

### Git Commit Message Format

```
feat(security): implement zero trust network policies with Cilium

- Deploy CiliumClusterwideNetworkPolicy for default-deny-all
- Configure Tier 0 namespace exemptions (kube-system, flux-system)
- Add allow-dns policies for cluster-wide DNS resolution
- Add allow-metrics-scraping for observability
- Configure Tier 1 policies for cert-manager, external-secrets
- FR22, FR23, FR24: Network isolation with debug bypass
- NFR9: Default-deny network policies
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

