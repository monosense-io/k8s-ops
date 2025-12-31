# Story 1.4: Deploy External Secrets Operator with 1Password

Status: ready-for-dev

## Story

As a **platform operator**,
I want **External Secrets Operator syncing secrets from 1Password**,
So that **applications can access secrets without storing them in Git**.

## Acceptance Criteria

1. **Given** Flux is operational from Story 1.3
   **When** External Secrets Operator is deployed
   **Then** `kubernetes/apps/external-secrets/` contains:
   - Operator HelmRelease with ESO v1.0.0
   - ClusterSecretStore referencing 1Password Connect

2. **And** 1Password Connect is deployed with credentials from SOPS-encrypted secret

3. **And** a test ExternalSecret successfully syncs a secret from 1Password

4. **And** secret sync completes within 5 minutes (NFR5)

5. **And** operator uses < 500MB RAM (NFR32)

## Tasks / Subtasks

- [ ] Task 1: Create External Secrets Operator Directory Structure (AC: #1)
  - [ ] Create `kubernetes/apps/external-secrets/` directory
  - [ ] Create `kubernetes/apps/external-secrets/app/` subdirectory
  - [ ] Create `kubernetes/apps/external-secrets/stores/` subdirectory for ClusterSecretStore
  - [ ] Create `kubernetes/apps/external-secrets/ks.yaml` Flux Kustomization

- [ ] Task 2: Deploy External Secrets Operator (AC: #1)
  - [ ] Create `kubernetes/apps/external-secrets/app/helmrelease.yaml` with ESO v1.0.0
  - [ ] Configure HelmRelease with proper remediation (retries: 3, rollback strategy)
  - [ ] Set `installCRDs: true` (bootstrap-time deployment)
  - [ ] Configure resource limits: requests 100m CPU/128Mi RAM, limits 500m CPU/512Mi RAM
  - [ ] Set security context: runAsNonRoot, runAsUser 65534
  - [ ] Create `kubernetes/apps/external-secrets/app/kustomization.yaml`
  - [ ] Verify OCIRepository or HelmRepository reference exists in `infrastructure/base/repositories/`

- [ ] Task 3: Deploy 1Password Connect Server (AC: #2)
  - [ ] Create `kubernetes/apps/external-secrets/connect/` subdirectory
  - [ ] Create 1Password Connect Deployment with image `1password/connect:1.5.6`
  - [ ] Configure 2 replicas for high availability
  - [ ] Create ClusterIP Service for internal access (port 8080)
  - [ ] Create SOPS-encrypted secret for `1password-credentials.json`
  - [ ] Create SOPS-encrypted secret for Connect token
  - [ ] Mount credentials at `/home/opuser/.op/`
  - [ ] Create `kubernetes/apps/external-secrets/connect/kustomization.yaml`

- [ ] Task 4: Configure ClusterSecretStore (AC: #1)
  - [ ] Create `kubernetes/apps/external-secrets/stores/clustersecretstore.yaml`
  - [ ] Configure 1Password Connect provider with endpoint `http://onepassword-connect.external-secrets.svc.cluster.local:8080`
  - [ ] Reference 1Password token secret in auth configuration
  - [ ] Configure vault mappings for k8s-ops vault
  - [ ] Create `kubernetes/apps/external-secrets/stores/kustomization.yaml`

- [ ] Task 5: Create Test ExternalSecret (AC: #3)
  - [ ] Create test item in 1Password vault (e.g., `test-secret` with `username` and `password` fields)
  - [ ] Create `kubernetes/apps/external-secrets/test/externalsecret.yaml`
  - [ ] Configure ExternalSecret to sync from 1Password test item
  - [ ] Set refreshInterval to 1h (production default)
  - [ ] Use creationPolicy: Owner

- [ ] Task 6: Verify Secret Sync (AC: #3, #4)
  - [ ] Deploy all ExternalSecrets resources
  - [ ] Verify ClusterSecretStore shows Ready status
  - [ ] Verify test ExternalSecret syncs successfully
  - [ ] Measure sync latency (must be < 5 minutes per NFR5)
  - [ ] Verify synced Kubernetes Secret contains correct data

- [ ] Task 7: Verify Resource Usage (AC: #5)
  - [ ] Check ESO operator pod memory usage: `kubectl top pod -n external-secrets`
  - [ ] Verify operator uses < 500MB RAM (NFR32)
  - [ ] Check 1Password Connect pod resource usage
  - [ ] Document actual resource consumption

- [ ] Task 8: Configure Flux Dependencies
  - [ ] Update `kubernetes/apps/external-secrets/ks.yaml` with proper dependsOn
  - [ ] Ensure external-secrets depends on cluster infrastructure
  - [ ] Add to `kubernetes/apps/kustomization.yaml` resource list
  - [ ] Test Flux reconciliation

- [ ] Task 9: Clean Up and Document
  - [ ] Remove test ExternalSecret after verification (or keep as health check)
  - [ ] Update `docs/runbooks/` with external-secrets operations
  - [ ] Document token rotation procedure (90-day expiration)

## Dev Notes

### Architecture Patterns & Constraints

**From Architecture Document (architecture.md):**

1. **Secret Management Flow:**
   ```
   1Password Vault → External Secrets Operator → Kubernetes Secret → Pod
                           ↓
                 SOPS/AGE for Git-encrypted files
   ```

2. **Technology Stack Versions (December 2025):**
   | Component | Version | Notes |
   |-----------|---------|-------|
   | External Secrets Operator | v1.0.0 | Chart v1.0.0, 1Password integration |
   | 1Password Connect | v1.5.6 | Tested stable version |

3. **NFR Requirements:**
   - NFR5: External Secrets sync < 5 minutes (time from 1Password change to Secret update)
   - NFR32: Operator footprint < 500 MB RAM each

4. **ExternalSecret API Version:**
   - **Use `external-secrets.io/v1`** (ESO v1.0.0+)
   - Migrate any `v1beta1` to `v1`

5. **Post-Flux Bootstrap Sequence:**
   ```
   external-secrets → Rook-Ceph → VictoriaMetrics → Applications
   ```
   External Secrets is the FIRST component deployed after Flux becomes operational.

### Project Context Rules (Critical)

**From project-context.md:**

1. **ExternalSecret API Version:**
   - Always use `external-secrets.io/v1` (not v1beta1)

2. **Multi-Secret Naming:**
   | Pattern | Example |
   |---------|---------|
   | Database credentials | `{app}-pguser-secret` |
   | SMTP credentials | `{app}-smtp-secret` |
   | API keys | `{app}-api-secret` |
   | General app secrets | `{app}-secret` |

3. **SOPS AGE Key:**
   - `age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek`

4. **Reloader Integration:**
   - Apps with secrets/configmaps should include:
     ```yaml
     annotations:
       reloader.stakater.com/auto: "true"
     ```

### Directory Structure

```
kubernetes/apps/external-secrets/
├── app/                              # ESO operator
│   ├── helmrelease.yaml
│   └── kustomization.yaml
├── connect/                          # 1Password Connect Server
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── credentials.sops.yaml         # SOPS encrypted
│   ├── token.sops.yaml               # SOPS encrypted
│   └── kustomization.yaml
├── stores/                           # ClusterSecretStore
│   ├── clustersecretstore.yaml
│   └── kustomization.yaml
├── test/                             # Test ExternalSecret (optional)
│   ├── externalsecret.yaml
│   └── kustomization.yaml
└── ks.yaml                           # Flux Kustomization entry point
```

### HelmRelease Template

```yaml
---
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: external-secrets
spec:
  interval: 30m
  chart:
    spec:
      chart: external-secrets
      version: 1.0.0
      sourceRef:
        kind: HelmRepository
        name: external-secrets
        namespace: flux-system
  install:
    crds: Create
    remediation:
      retries: 3
  upgrade:
    cleanupOnFail: true
    crds: CreateReplace
    remediation:
      strategy: rollback
      retries: 3
  values:
    installCRDs: true
    securityContext:
      runAsNonRoot: true
      runAsUser: 65534
      fsGroup: 65534
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi
    serviceMonitor:
      enabled: true
      namespace: external-secrets
```

### ClusterSecretStore Template

```yaml
---
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: onepassword-connect
spec:
  provider:
    onepassword:
      connectHost: http://onepassword-connect.external-secrets.svc.cluster.local:8080
      vaults:
        k8s-ops: 1
      auth:
        secretRef:
          connectTokenSecretRef:
            name: onepassword-connect-token
            namespace: external-secrets
            key: token
```

### 1Password Connect Deployment Template

```yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: onepassword-connect
  namespace: external-secrets
  labels:
    app.kubernetes.io/name: onepassword-connect
spec:
  replicas: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: onepassword-connect
  template:
    metadata:
      labels:
        app.kubernetes.io/name: onepassword-connect
    spec:
      containers:
        - name: connect
          image: 1password/connect:1.5.6
          ports:
            - name: http
              containerPort: 8080
              protocol: TCP
          env:
            - name: OP_LOG_LEVEL
              value: info
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 256Mi
          livenessProbe:
            httpGet:
              path: /heartbeat
              port: http
            initialDelaySeconds: 15
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
          volumeMounts:
            - name: credentials
              mountPath: /home/opuser/.op
              readOnly: true
          securityContext:
            runAsNonRoot: true
            runAsUser: 999
            readOnlyRootFilesystem: true
      volumes:
        - name: credentials
          secret:
            secretName: onepassword-connect-credentials
---
apiVersion: v1
kind: Service
metadata:
  name: onepassword-connect
  namespace: external-secrets
spec:
  type: ClusterIP
  ports:
    - name: http
      port: 8080
      targetPort: http
      protocol: TCP
  selector:
    app.kubernetes.io/name: onepassword-connect
```

### ExternalSecret Template

```yaml
---
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: test-secret
  namespace: external-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword-connect
  target:
    name: test-secret
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: test-secret
```

### Flux Kustomization Template

```yaml
---
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: &name external-secrets
  namespace: flux-system
spec:
  targetNamespace: external-secrets
  commonMetadata:
    labels:
      app.kubernetes.io/name: *name
  path: ./kubernetes/apps/external-secrets/app
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

### 1Password Vault Structure

**Required 1Password Items in `k8s-ops` vault:**

1. **onepassword-connect-credentials**
   - Type: Document or Secure Note
   - Contains: `1password-credentials.json` (minified with `jq -c '.'`)

2. **onepassword-connect-token**
   - Type: Password or Secure Note
   - Contains: Access token (90-day expiration)

3. **test-secret** (for verification)
   - Type: Login or Password
   - Fields: username, password

### SOPS Encryption Commands

```bash
# Create encrypted credentials file
sops -e -i kubernetes/apps/external-secrets/connect/credentials.sops.yaml

# Create encrypted token file
sops -e -i kubernetes/apps/external-secrets/connect/token.sops.yaml

# Verify decryption works
sops -d kubernetes/apps/external-secrets/connect/credentials.sops.yaml
```

### Previous Story Intelligence

**From Story 1.3 (Bootstrap Infra Cluster):**
- Flux is operational and connected to k8s-ops repository
- `flux check` passes with all components healthy
- GitRepository shows Ready status pointing to main branch
- Bootstrap phase completed: CRDs → Cilium → CoreDNS → Spegel → cert-manager → Flux
- **External Secrets is the FIRST component in Phase 3 (Post-Flux)**

**Key Learnings:**
- Always install CRDs before applications that use them
- Use `.yaml` extension consistently (not `.yml`)
- All secrets must be SOPS encrypted before commit
- Flux Kustomization path uses relative format: `./kubernetes/apps/...`
- Use `wait: true` for infrastructure components to ensure ordering

### Latest Technical Information (December 2025)

**External Secrets Operator:**
- Current stable version: v1.0.0 (released November 7, 2025)
- Latest version available: v1.2.0 (but v1.0.0 is stable for production)
- API Version: `external-secrets.io/v1` (promoted from v1beta1)
- 1Password provider status: ALPHA (use with awareness)

**1Password Connect:**
- Recommended version: 1.5.6
- Tested compatible versions: 1.3.0, 1.5.0, 1.5.6
- Token expiration: Maximum 90 days (cannot be extended, must rotate)

**Breaking Changes in ESO v1.0.0:**
- CreationPolicy: Owner now DELETES keys removed from template/data
- API promoted from v1beta1 to v1 (since v0.17.0)
- All CRDs now have proper kubebuilder validation markers

**Token Rotation Procedure:**
1. Set calendar reminder 2 weeks before 90-day expiration
2. Generate new token in 1Password
3. Update SOPS-encrypted secret with new token
4. Commit and push to trigger Flux reconciliation
5. ESO automatically uses new token on next sync
6. Revoke old token in 1Password after confirmation

### Verification Commands

```bash
# Check ESO operator status
kubectl get pods -n external-secrets

# Check ClusterSecretStore status
kubectl get clustersecretstores

# Check ExternalSecret status
kubectl get externalsecrets -A

# Check synced secret
kubectl get secret test-secret -n external-secrets -o yaml

# Check sync timing
kubectl get externalsecret test-secret -n external-secrets -o jsonpath='{.status.syncedResourceVersion}'

# Check operator memory usage (NFR32: < 500MB)
kubectl top pod -n external-secrets -l app.kubernetes.io/name=external-secrets

# Check 1Password Connect health
kubectl logs -n external-secrets -l app.kubernetes.io/name=onepassword-connect
```

### Critical Implementation Rules

1. **API Version:**
   - Use `external-secrets.io/v1` for all ESO resources
   - Do NOT use v1beta1 (deprecated)

2. **SOPS Encryption:**
   - All 1Password credentials MUST be SOPS encrypted
   - Never commit unencrypted credentials to Git

3. **Connect Server:**
   - Always minify `1password-credentials.json` with `jq -c '.'`
   - Use ClusterIP service (not NodePort or LoadBalancer)
   - Deploy 2 replicas for HA

4. **Token Management:**
   - Maximum 90-day token lifetime
   - Plan rotation before expiration
   - Document expiration date

5. **Resource Limits:**
   - ESO operator: max 512Mi RAM (NFR32: < 500MB)
   - 1Password Connect: max 256Mi RAM

6. **Flux Dependencies:**
   - external-secrets depends on cluster-infrastructure
   - Other apps will depend on external-secrets (stores)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4: Deploy External Secrets Operator with 1Password]
- [Source: _bmad-output/planning-artifacts/architecture.md#Secret Management Flow]
- [Source: docs/project-context.md#ExternalSecret API Version]
- [External Secrets Operator Docs](https://external-secrets.io/)
- [1Password Connect Provider](https://external-secrets.io/latest/provider/1password-automation/)
- [ESO v1.0.0 Release Notes](https://github.com/external-secrets/external-secrets/releases/tag/v1.0.0)

### Validation Checklist

Before marking complete, verify:
- [ ] `kubernetes/apps/external-secrets/` directory structure created
- [ ] ESO HelmRelease v1.0.0 deployed with correct remediation settings
- [ ] 1Password Connect Server deployed with 2 replicas
- [ ] Connect credentials SOPS encrypted in Git
- [ ] ClusterSecretStore shows Ready status
- [ ] Test ExternalSecret syncs successfully
- [ ] Sync latency < 5 minutes (NFR5)
- [ ] ESO operator memory < 500MB (NFR32)
- [ ] All resources use `external-secrets.io/v1` API version
- [ ] Flux reconciliation successful
- [ ] Token expiration date documented

### Git Commit Message Format

```
feat(external-secrets): deploy ESO v1.0.0 with 1Password Connect

- Deploy External Secrets Operator v1.0.0 via HelmRelease
- Deploy 1Password Connect Server with HA (2 replicas)
- Configure ClusterSecretStore for 1Password vault
- Add SOPS-encrypted credentials
- Verify secret sync < 5 minutes (NFR5)
- Operator memory < 500MB (NFR32)
```

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
