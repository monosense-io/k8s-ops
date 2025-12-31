# Story 2.4: Deploy cert-manager with DNS-01 Validation

Status: ready-for-dev

## Story

As a **platform operator**,
I want **cert-manager automatically issuing Let's Encrypt certificates via DNS-01**,
So that **all ingress endpoints have valid TLS without manual intervention and I can issue wildcard certificates for cluster domains**.

## Acceptance Criteria

1. **Given** External Secrets is syncing Cloudflare API credentials
   **When** cert-manager is deployed
   **Then** `kubernetes/apps/cert-manager/` contains:
   - Operator installed via bootstrap (Story 1.2)
   - `issuers/` directory with ClusterIssuer for Let's Encrypt (staging and production)
   - Cloudflare DNS-01 solver configuration

2. **And** ClusterIssuer `letsencrypt-production` is Ready

3. **And** wildcard Certificate for `*.monosense.dev` is issued successfully

4. **And** Certificate renewal triggers automatically 30+ days before expiry (NFR6)

5. **And** certificate issuance completes within 5 minutes

## Tasks / Subtasks

- [ ] Task 1: Create cert-manager Issuers Directory Structure (AC: #1)
  - [ ] Create `kubernetes/apps/cert-manager/issuers/` directory
  - [ ] Create `kubernetes/apps/cert-manager/issuers/app/` subdirectory for resources
  - [ ] Create `kubernetes/apps/cert-manager/issuers/ks.yaml` Flux Kustomization entry point
  - [ ] Create `kubernetes/apps/cert-manager/issuers/app/kustomization.yaml`
  - [ ] Add to `kubernetes/apps/cert-manager/kustomization.yaml` resource list

- [ ] Task 2: Create Cloudflare API Token ExternalSecret (AC: #1)
  - [ ] Create `kubernetes/apps/cert-manager/issuers/app/externalsecret.yaml`
  - [ ] Configure ExternalSecret to sync Cloudflare API token from 1Password
  - [ ] Secret should be created in `cert-manager` namespace
  - [ ] Secret name: `cloudflare-api-token-secret`
  - [ ] Key: `api-token` containing the Cloudflare DNS Zone Edit token
  - [ ] Verify ExternalSecret uses `external-secrets.io/v1` API version

- [ ] Task 3: Create Let's Encrypt Staging ClusterIssuer (AC: #1)
  - [ ] Create `kubernetes/apps/cert-manager/issuers/app/clusterissuer-staging.yaml`
  - [ ] Configure ACME server: `https://acme-staging-v02.api.letsencrypt.org/directory`
  - [ ] Configure email for Let's Encrypt notifications
  - [ ] Configure Cloudflare DNS-01 solver with apiTokenSecretRef
  - [ ] Add selector for monosense.dev and monosense.io domains

- [ ] Task 4: Create Let's Encrypt Production ClusterIssuer (AC: #1, #2)
  - [ ] Create `kubernetes/apps/cert-manager/issuers/app/clusterissuer-production.yaml`
  - [ ] Configure ACME server: `https://acme-v02.api.letsencrypt.org/directory`
  - [ ] Configure email for Let's Encrypt notifications
  - [ ] Configure Cloudflare DNS-01 solver with apiTokenSecretRef
  - [ ] Name: `letsencrypt-production`

- [ ] Task 5: Create Wildcard Certificate for monosense.dev (AC: #3, #4, #5)
  - [ ] Create `kubernetes/apps/cert-manager/issuers/app/certificate-wildcard-monosense-dev.yaml`
  - [ ] Configure wildcard: `*.monosense.dev` and base domain `monosense.dev`
  - [ ] Reference ClusterIssuer `letsencrypt-production`
  - [ ] Set `renewBefore: 720h` (30 days) for automatic renewal before expiry
  - [ ] Configure secret name: `monosense-dev-tls`
  - [ ] Target namespace: `networking` (for Envoy Gateway)

- [ ] Task 6: Create Wildcard Certificate for monosense.io (AC: #3, #4, #5)
  - [ ] Create `kubernetes/apps/cert-manager/issuers/app/certificate-wildcard-monosense-io.yaml`
  - [ ] Configure wildcard: `*.monosense.io` and base domain `monosense.io`
  - [ ] Reference ClusterIssuer `letsencrypt-production`
  - [ ] Set `renewBefore: 720h` (30 days) for automatic renewal before expiry
  - [ ] Configure secret name: `monosense-io-tls`
  - [ ] Target namespace: `networking` (for Envoy Gateway)

- [ ] Task 7: Configure Flux Dependencies and Kustomization (AC: #1)
  - [ ] Update `kubernetes/apps/cert-manager/issuers/ks.yaml` with proper dependsOn
  - [ ] Depend on: `external-secrets-stores` (ClusterSecretStore must be ready)
  - [ ] Depend on: `cluster-infrastructure` (cert-manager operator must be running)
  - [ ] Set `prune: true` for cleanup on removal
  - [ ] Set `wait: true` to wait for Certificate resources

- [ ] Task 8: Verify ClusterIssuer Readiness (AC: #2)
  - [ ] Apply configuration to infra cluster
  - [ ] Run `kubectl get clusterissuer letsencrypt-production -o yaml`
  - [ ] Verify status shows `Ready: True`
  - [ ] Check for any ACME registration errors in cert-manager logs

- [ ] Task 9: Verify Wildcard Certificate Issuance (AC: #3, #5)
  - [ ] Trigger Flux reconciliation
  - [ ] Monitor Certificate resources: `kubectl get certificate -n networking`
  - [ ] Verify certificates reach `Ready: True` state within 5 minutes
  - [ ] Check CertificateRequest and Order resources for any errors
  - [ ] Verify TLS secrets are created in networking namespace

- [ ] Task 10: Verify Automatic Renewal Configuration (AC: #4)
  - [ ] Confirm `renewBefore: 720h` is set in Certificate specs
  - [ ] Document how cert-manager monitors and triggers renewal
  - [ ] Verify cert-manager controller logs show no renewal errors

- [ ] Task 11: Document and Finalize
  - [ ] Update `docs/runbooks/cert-manager.md` with troubleshooting section
  - [ ] Document ClusterIssuer status verification commands
  - [ ] Document manual certificate renewal procedure if needed
  - [ ] Add DNS-01 challenge debugging steps

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document (architecture.md):**

1. **Technology Stack Versions (December 2025):**
   | Component | Version | Notes |
   |-----------|---------|-------|
   | cert-manager | v1.19.2 | Installed via bootstrap helmfile |
   | Let's Encrypt | ACME v2 | Production and staging endpoints |

2. **FRs Covered:**
   - FR32: Operator can deploy cert-manager with Let's Encrypt DNS-01 validation
   - FR33: Operator can configure wildcard certificates for cluster domains
   - FR57: Operator can issue and renew TLS certificates automatically

3. **NFR Requirements:**
   - NFR6: Certificate renewal automatic (30+ days before expiry)
   - NFR12: External TLS - All public endpoints use valid Let's Encrypt certificates

4. **Secret Management Flow:**
   ```
   1Password Vault → External Secrets Operator → Kubernetes Secret → cert-manager
   ```

5. **Domain Architecture:**
   | Cluster | Domain | Wildcard Certificate |
   |---------|--------|---------------------|
   | infra | `monosense.dev` | `*.monosense.dev` |
   | apps | `monosense.io` | `*.monosense.io` |

6. **App Location Rules:**
   - cert-manager issuers go in `kubernetes/apps/cert-manager/issuers/` (shared apps)
   - Deployed to BOTH clusters via Flux reconciliation
   - Operator is installed via bootstrap (not in kubernetes/apps)

### Project Context Rules (Critical)

**From project-context.md:**

1. **ExternalSecret API Version:**
   - **Use `external-secrets.io/v1`** (ESO v1.0.0+)
   - NOT v1beta1

2. **Flux Kustomization Standards:**
   ```yaml
   apiVersion: kustomize.toolkit.fluxcd.io/v1
   kind: Kustomization
   metadata:
     name: &name cert-manager-issuers
     namespace: flux-system
   spec:
     targetNamespace: cert-manager
     path: ./kubernetes/apps/cert-manager/issuers/app
     prune: true
     sourceRef:
       kind: GitRepository
       name: k8s-ops
     interval: 30m
     dependsOn:
       - name: external-secrets-stores
       - name: cluster-infrastructure
   ```

3. **Naming Conventions:**
   - kebab-case for all Kubernetes resource names
   - `.yaml` extension (not `.yml`)

4. **YAML Anchor Pattern:**
   ```yaml
   metadata:
     name: &name cert-manager-issuers
   spec:
     commonMetadata:
       labels:
         app.kubernetes.io/name: *name
   ```

### cert-manager v1.19 DNS-01 with Cloudflare

**From Web Research (December 2025):**

1. **Cloudflare API Token Requirements:**
   - Create token with Zone:DNS:Edit permission
   - Limit to specific zone (monosense.dev, monosense.io) for security
   - Token stored in 1Password, synced via External Secrets

2. **ClusterIssuer Configuration:**
   ```yaml
   apiVersion: cert-manager.io/v1
   kind: ClusterIssuer
   metadata:
     name: letsencrypt-production
   spec:
     acme:
       server: https://acme-v02.api.letsencrypt.org/directory
       email: admin@monosense.dev
       privateKeySecretRef:
         name: letsencrypt-production-account-key
       solvers:
       - dns01:
           cloudflare:
             apiTokenSecretRef:
               name: cloudflare-api-token-secret
               key: api-token
   ```

3. **Wildcard Certificate Configuration:**
   ```yaml
   apiVersion: cert-manager.io/v1
   kind: Certificate
   metadata:
     name: monosense-dev-wildcard
     namespace: networking
   spec:
     secretName: monosense-dev-tls
     issuerRef:
       name: letsencrypt-production
       kind: ClusterIssuer
     dnsNames:
       - "monosense.dev"
       - "*.monosense.dev"
     renewBefore: 720h  # 30 days
   ```

4. **DNS-01 Challenge Process:**
   - cert-manager creates TXT record `_acme-challenge.monosense.dev`
   - Let's Encrypt queries DNS to verify domain ownership
   - TXT record is cleaned up after verification
   - Certificate is issued and stored in Secret

5. **Recommended Helm Values for DNS Resolution:**
   ```yaml
   extraArgs:
     - --dns01-recursive-nameservers=1.1.1.1:53,9.9.9.9:53
     - --dns01-recursive-nameservers-only=true
   ```

### Directory Structure

```
kubernetes/apps/cert-manager/
├── issuers/
│   ├── app/
│   │   ├── kustomization.yaml
│   │   ├── externalsecret.yaml
│   │   ├── clusterissuer-staging.yaml
│   │   ├── clusterissuer-production.yaml
│   │   ├── certificate-wildcard-monosense-dev.yaml
│   │   └── certificate-wildcard-monosense-io.yaml
│   └── ks.yaml
└── kustomization.yaml  (lists issuers/ks.yaml)
```

### Resource Templates

**externalsecret.yaml:**
```yaml
---
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: cloudflare-api-token
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword-connect
  target:
    name: cloudflare-api-token-secret
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: cloudflare-api-token
```

**clusterissuer-staging.yaml:**
```yaml
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: admin@monosense.dev
    privateKeySecretRef:
      name: letsencrypt-staging-account-key
    solvers:
    - dns01:
        cloudflare:
          apiTokenSecretRef:
            name: cloudflare-api-token-secret
            key: api-token
      selector:
        dnsZones:
          - "monosense.dev"
          - "monosense.io"
```

**clusterissuer-production.yaml:**
```yaml
---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-production
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@monosense.dev
    privateKeySecretRef:
      name: letsencrypt-production-account-key
    solvers:
    - dns01:
        cloudflare:
          apiTokenSecretRef:
            name: cloudflare-api-token-secret
            key: api-token
      selector:
        dnsZones:
          - "monosense.dev"
          - "monosense.io"
```

**certificate-wildcard-monosense-dev.yaml:**
```yaml
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: monosense-dev-wildcard
  namespace: networking
spec:
  secretName: monosense-dev-tls
  issuerRef:
    name: letsencrypt-production
    kind: ClusterIssuer
  dnsNames:
    - "monosense.dev"
    - "*.monosense.dev"
  renewBefore: 720h
```

**certificate-wildcard-monosense-io.yaml:**
```yaml
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: monosense-io-wildcard
  namespace: networking
spec:
  secretName: monosense-io-tls
  issuerRef:
    name: letsencrypt-production
    kind: ClusterIssuer
  dnsNames:
    - "monosense.io"
    - "*.monosense.io"
  renewBefore: 720h
```

**ks.yaml:**
```yaml
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name cert-manager-issuers
  namespace: flux-system
spec:
  targetNamespace: cert-manager
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./kubernetes/apps/cert-manager/issuers/app
  prune: true
  sourceRef:
    kind: GitRepository
    name: k8s-ops
  wait: true
  interval: 30m
  retryInterval: 1m
  timeout: 5m
  dependsOn:
    - name: external-secrets-stores
    - name: cluster-infrastructure
  postBuild:
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

**app/kustomization.yaml:**
```yaml
---
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - externalsecret.yaml
  - clusterissuer-staging.yaml
  - clusterissuer-production.yaml
  - certificate-wildcard-monosense-dev.yaml
  - certificate-wildcard-monosense-io.yaml
```

### Previous Story Intelligence

**From Story 2.3 (Implement Zero Trust Network Policies):**
- Network policies allow cert-manager egress to ACME providers via `tier1-cert-manager.yaml`
- Policy allows egress to `*.letsencrypt.org` and `*.cloudflare.com` on port 443
- DNS egress is allowed for cert-manager namespace
- Tier 1 namespace classification for cert-manager established

**Key Learnings from Previous Stories:**
- Use `.yaml` extension consistently
- Flux Kustomization path uses relative format: `./kubernetes/apps/...`
- Use `wait: true` for infrastructure components
- Tier 1 namespaces (cert-manager) have controlled egress access

### Latest Technical Information (December 2025)

**cert-manager v1.19.2 Key Information:**

1. **API Version:**
   - Use `cert-manager.io/v1` for all resources
   - ClusterIssuer, Certificate, CertificateRequest all use v1

2. **DNS-01 Challenge Best Practices:**
   - Use API token (not global API key) for Cloudflare
   - Token should have Zone:DNS:Edit permission only
   - Limit token to specific zones for security
   - Use staging issuer first to test configuration

3. **Wildcard Certificate Notes:**
   - Include both base domain and wildcard in dnsNames
   - Example: `monosense.dev` AND `*.monosense.dev`
   - Single certificate covers all subdomains

4. **Renewal Configuration:**
   - `renewBefore: 720h` = 30 days before expiry
   - Let's Encrypt certificates valid for 90 days
   - cert-manager automatically triggers renewal

5. **Troubleshooting Commands:**
   ```bash
   # Check ClusterIssuer status
   kubectl get clusterissuer letsencrypt-production -o yaml

   # Check Certificate status
   kubectl get certificate -n networking

   # Check CertificateRequest for errors
   kubectl get certificaterequest -n networking

   # Check Order for ACME status
   kubectl get order -n networking

   # Check Challenge for DNS-01 status
   kubectl get challenge -n networking

   # View cert-manager logs
   kubectl logs -n cert-manager -l app=cert-manager --tail=100
   ```

### Verification Commands

```bash
# Check ClusterIssuer is Ready
kubectl get clusterissuer letsencrypt-production
kubectl get clusterissuer letsencrypt-staging

# Check ExternalSecret synced
kubectl get externalsecret -n cert-manager cloudflare-api-token
kubectl get secret -n cert-manager cloudflare-api-token-secret

# Check Certificate status
kubectl get certificate -n networking monosense-dev-wildcard
kubectl get certificate -n networking monosense-io-wildcard

# Check Certificate details
kubectl describe certificate -n networking monosense-dev-wildcard

# Check TLS secrets created
kubectl get secret -n networking monosense-dev-tls
kubectl get secret -n networking monosense-io-tls

# Verify certificate content
kubectl get secret -n networking monosense-dev-tls -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -text -noout | head -20

# Check Flux reconciliation
flux get kustomization cert-manager-issuers

# Check cert-manager logs for errors
kubectl logs -n cert-manager -l app=cert-manager --tail=50

# Monitor ACME orders
kubectl get orders -n networking
kubectl get challenges -n networking
```

### Critical Implementation Rules

1. **Order of Operations:**
   - External Secrets must sync Cloudflare token FIRST
   - ClusterIssuers depend on the secret existing
   - Certificates depend on ClusterIssuers being Ready

2. **Staging First:**
   - Test with `letsencrypt-staging` issuer initially
   - Staging has higher rate limits, won't lock you out
   - Switch to production after verification

3. **Certificate Namespace:**
   - Certificates in `networking` namespace for Envoy Gateway
   - TLS secrets must be in same namespace as Gateway

4. **ExternalSecret Refresh:**
   - Set `refreshInterval: 1h` for API token
   - Token rotation in 1Password auto-syncs within 1 hour

5. **Wildcard + Base Domain:**
   - Always include BOTH in dnsNames list
   - `*.monosense.dev` does NOT cover `monosense.dev` itself

### Project Structure Notes

- **Alignment:** cert-manager issuers follow shared app pattern in `kubernetes/apps/`
- **Path:** `kubernetes/apps/cert-manager/issuers/` for cluster-wide issuers
- **Deployed to:** BOTH clusters (infra and apps) via Flux reconciliation
- **Operator Location:** Installed via bootstrap helmfile (Story 1.2), NOT in kubernetes/apps/

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 2.4: Deploy cert-manager with DNS-01 Validation]
- [Source: _bmad-output/planning-artifacts/architecture.md#Technology Stack]
- [Source: docs/project-context.md#Technology Stack & Versions]
- [cert-manager Cloudflare DNS-01 Documentation](https://cert-manager.io/docs/configuration/acme/dns01/cloudflare/)
- [cert-manager DNS Validation Tutorial](https://cert-manager.io/docs/tutorials/acme/dns-validation/)
- [cert-manager ACME Configuration](https://cert-manager.io/docs/configuration/acme/)

### Validation Checklist

Before marking complete, verify:
- [ ] `kubernetes/apps/cert-manager/issuers/` directory structure created
- [ ] ExternalSecret syncs Cloudflare API token from 1Password
- [ ] ClusterIssuer `letsencrypt-staging` is Ready
- [ ] ClusterIssuer `letsencrypt-production` is Ready
- [ ] Certificate `monosense-dev-wildcard` is Ready in networking namespace
- [ ] Certificate `monosense-io-wildcard` is Ready in networking namespace
- [ ] TLS secrets created: `monosense-dev-tls`, `monosense-io-tls`
- [ ] Certificate issuance completed within 5 minutes
- [ ] `renewBefore: 720h` configured for automatic renewal
- [ ] Flux reconciliation successful on both clusters
- [ ] Runbook documentation updated

### Git Commit Message Format

```
feat(cert-manager): deploy DNS-01 ClusterIssuers with Cloudflare

- Add ExternalSecret for Cloudflare API token from 1Password
- Create Let's Encrypt staging and production ClusterIssuers
- Deploy wildcard certificates for monosense.dev and monosense.io
- Configure automatic renewal 30 days before expiry
- FR32, FR33, FR57: cert-manager DNS-01 validation
- NFR6, NFR12: Automatic certificate renewal and TLS
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

