# Story 0.4: Configure SOPS/AGE Encryption

Status: ready-for-dev

## Story

As a **platform operator**,
I want **SOPS encryption configured with my existing AGE key**,
So that **I can encrypt sensitive files in Git while Flux can decrypt them during reconciliation**.

## Acceptance Criteria

1. **Given** the repository structure with cluster directories
   **When** SOPS/AGE encryption is configured
   **Then** `.sops.yaml` exists at repository root with:
   - Creation rules for `*.sops.yaml` and `*.sops.yml` files
   - AGE public key: `age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek`
   - Path-specific rules for cluster secrets

2. **And** a test secret file can be encrypted with `sops -e`

3. **And** the encrypted file can be decrypted with `sops -d` using the private key from 1Password

4. **And** `bootstrap/infra/github-deploy-key.sops.yaml` template exists for GitHub deploy key

## Tasks / Subtasks

- [ ] Task 1: Create root `.sops.yaml` configuration file (AC: #1)
  - [ ] Create `.sops.yaml` at repository root
  - [ ] Configure creation rules for `*.sops.yaml` and `*.sops.yml` patterns
  - [ ] Set AGE public key: `age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek`
  - [ ] Add `encrypted_regex` to only encrypt `data` and `stringData` fields
  - [ ] Add path-specific rules for cluster-specific secrets

- [ ] Task 2: Create cluster-specific SOPS rules (AC: #1)
  - [ ] Add path rule for `clusters/infra/**/*.sops.yaml`
  - [ ] Add path rule for `clusters/apps/**/*.sops.yaml`
  - [ ] Add path rule for `bootstrap/**/*.sops.yaml`
  - [ ] Ensure rules apply recursively to all subdirectories

- [ ] Task 3: Create test secret for encryption validation (AC: #2, #3)
  - [ ] Create `tests/sops/test-secret.yaml` as unencrypted Kubernetes Secret
  - [ ] Encrypt using `sops -e tests/sops/test-secret.yaml > tests/sops/test-secret.sops.yaml`
  - [ ] Verify encrypted file contains unreadable data section
  - [ ] Verify metadata, kind, apiVersion remain unencrypted
  - [ ] Remove unencrypted test file (only keep encrypted version)

- [ ] Task 4: Validate decryption with private key (AC: #3)
  - [ ] Retrieve AGE private key from 1Password vault
  - [ ] Set `SOPS_AGE_KEY` environment variable with private key
  - [ ] Run `sops -d tests/sops/test-secret.sops.yaml`
  - [ ] Verify decrypted output matches original content
  - [ ] Document the decryption verification in completion notes

- [ ] Task 5: Create GitHub deploy key template (AC: #4)
  - [ ] Create `bootstrap/infra/github-deploy-key.sops.yaml` as template
  - [ ] Include placeholder structure for SSH deploy key
  - [ ] Include placeholder for known_hosts
  - [ ] Add comments explaining how to populate and encrypt
  - [ ] Create equivalent `bootstrap/apps/github-deploy-key.sops.yaml`

- [ ] Task 6: Document SOPS usage (AC: #1-4)
  - [ ] Add comments to `.sops.yaml` explaining the configuration
  - [ ] Document encryption workflow in README or docs
  - [ ] Include example commands for common operations

## Dev Notes

### Architecture Patterns & Constraints

**AGE Key Information (from Architecture doc):**
- **Public Key:** `age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek`
- **Private Key Location:** 1Password vault (never in Git or filesystem)
- This key is the SOPS AGE key constraint defined in the Architecture document

**SOPS Configuration Pattern (from FluxCD best practices):**
```yaml
# .sops.yaml - Root configuration
creation_rules:
  # Cluster-specific secrets
  - path_regex: clusters/infra/.*\.sops\.ya?ml$
    encrypted_regex: '^(data|stringData)$'
    age: age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek
  - path_regex: clusters/apps/.*\.sops\.ya?ml$
    encrypted_regex: '^(data|stringData)$'
    age: age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek
  # Bootstrap secrets
  - path_regex: bootstrap/.*\.sops\.ya?ml$
    encrypted_regex: '^(data|stringData)$'
    age: age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek
  # Default rule for any other sops files
  - path_regex: .*\.sops\.ya?ml$
    encrypted_regex: '^(data|stringData)$'
    age: age1j3hsfptdfsfwvkf504etjkrtmajny9csrfh5s24uqh6fchmg5dgqg087ek
```

**Critical Implementation Rules:**

1. **Only encrypt `data` and `stringData` fields** - Flux kustomize-controller does NOT support encrypted metadata, kind, or apiVersion
2. **File naming convention:** Use `*.sops.yaml` or `*.sops.yml` suffix for encrypted files
3. **Path regex patterns:** Use `\.ya?ml$` to match both `.yaml` and `.yml` extensions
4. **Never commit private key:** AGE private key must only exist in 1Password

### Why AGE over GPG?

From SOPS documentation and FluxCD recommendations:
- AGE is simpler to use than GPG keyrings
- Smaller keys that solve copy/paste issues
- More opinionated on encryption algorithms (follows best practices)
- Designed specifically for file encryption
- No legacy use cases to support

### SOPS Latest Features (v3.9+)

Recent SOPS improvements relevant to this implementation:
- SSH support for AGE keys
- AGE identities with passphrases support
- AGE plugin support
- `SOPS_AGE_KEY_CMD` environment variable for executable key retrieval
- Improved age identity loading error collection

**Source:** [SOPS GitHub Releases](https://github.com/getsops/sops/releases)

### Flux Kustomization Decryption Configuration

After SOPS is configured, Flux Kustomizations that need to decrypt secrets must include:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: cluster-secrets
  namespace: flux-system
spec:
  # ... other spec fields ...
  decryption:
    provider: sops
    secretRef:
      name: sops-age
```

The `sops-age` secret must be created in the flux-system namespace during bootstrap:
```bash
cat age.agekey | kubectl create secret generic sops-age \
  --namespace=flux-system \
  --from-file=age.agekey=/dev/stdin
```

**Note:** This secret creation is handled during bootstrap (Story 1.3), not in this story.

### GitHub Deploy Key Template Structure

```yaml
# bootstrap/infra/github-deploy-key.sops.yaml
# Template - encrypt after populating with actual values
apiVersion: v1
kind: Secret
metadata:
  name: github-deploy-key
  namespace: flux-system
type: Opaque
stringData:
  identity: |
    -----BEGIN OPENSSH PRIVATE KEY-----
    # Replace with actual deploy key from GitHub
    -----END OPENSSH PRIVATE KEY-----
  known_hosts: |
    github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl
```

### Encryption/Decryption Commands

**Encrypt a file:**
```bash
# Using .sops.yaml configuration (recommended)
sops -e path/to/secret.yaml > path/to/secret.sops.yaml

# Or encrypt in-place
sops -e -i path/to/secret.sops.yaml
```

**Decrypt a file:**
```bash
# Requires SOPS_AGE_KEY or SOPS_AGE_KEY_FILE environment variable
export SOPS_AGE_KEY="AGE-SECRET-KEY-..."  # From 1Password
sops -d path/to/secret.sops.yaml

# Or decrypt to stdout
sops -d path/to/secret.sops.yaml > path/to/secret.yaml
```

**Edit encrypted file:**
```bash
export SOPS_AGE_KEY="AGE-SECRET-KEY-..."
sops path/to/secret.sops.yaml  # Opens in $EDITOR, auto-decrypts/re-encrypts
```

### Security Considerations

1. **Never commit unencrypted secrets** - Use git pre-commit hooks if needed
2. **Verify encryption before push** - Check that `data`/`stringData` is encrypted
3. **Test decryption locally** - Before bootstrap, verify keys work
4. **Rotate keys periodically** - Re-encrypt all secrets with new key if compromised

### Project Structure Notes

**Files to create:**
```
k8s-ops/
├── .sops.yaml                              # Root SOPS configuration
├── bootstrap/
│   ├── infra/
│   │   └── github-deploy-key.sops.yaml     # Template for infra cluster
│   └── apps/
│       └── github-deploy-key.sops.yaml     # Template for apps cluster
└── tests/
    └── sops/
        └── test-secret.sops.yaml           # Encrypted test secret
```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Technical Constraints & Dependencies - SOPS AGE Key]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 0.4: Configure SOPS/AGE Encryption]
- [Source: docs/project-context.md#Critical Don't-Miss Rules - NEVER skip SOPS encryption]
- [FluxCD SOPS Guide](https://fluxcd.io/flux/guides/mozilla-sops/)
- [SOPS GitHub](https://github.com/getsops/sops)
- [AGE Encryption](https://github.com/FiloSottile/age)

### Previous Story Intelligence

**From Story 0.1 - Initialize Repository Structure:**
- Repository structure established with `bootstrap/infra/` and `bootstrap/apps/` directories
- `.gitignore` should be configured to exclude sensitive unencrypted files

**From Story 0.2 - Create Shared Infrastructure Base:**
- Infrastructure base structure is in place for shared components

**From Story 0.3 - Configure Cluster-Specific Flux Entry Points:**
- Cluster directories (`clusters/infra/`, `clusters/apps/`) are configured
- These directories will contain cluster-specific encrypted secrets

**Key Learnings from Previous Stories:**
- Strict adherence to `.yaml` extension for all YAML files
- Use relative paths from repository root for all configurations
- Validate configurations before considering complete

### Validation Commands

```bash
# Verify SOPS configuration exists and is valid
cat .sops.yaml

# Test encryption (requires sops CLI installed)
echo 'apiVersion: v1
kind: Secret
metadata:
  name: test-secret
  namespace: default
type: Opaque
stringData:
  password: "test123"' > /tmp/test.yaml

sops -e /tmp/test.yaml > tests/sops/test-secret.sops.yaml

# Verify only data is encrypted (metadata should be readable)
cat tests/sops/test-secret.sops.yaml | head -20

# Test decryption (requires AGE private key)
export SOPS_AGE_KEY="<private-key-from-1password>"
sops -d tests/sops/test-secret.sops.yaml

# Clean up temp file
rm /tmp/test.yaml
```

### Git Commit Message Format

```
feat(security): configure SOPS/AGE encryption for secrets management

- Add .sops.yaml with AGE public key and path-specific rules
- Create GitHub deploy key templates for both clusters
- Add test secret for encryption validation
- Configure encrypted_regex to only encrypt data/stringData fields
```

### Common Gotchas

1. **Path regex specificity** - More specific paths should come before general patterns in `.sops.yaml`
2. **encrypted_regex syntax** - Use `'^(data|stringData)$'` with anchors for exact matching
3. **File extension matching** - Use `\.ya?ml$` to match both `.yaml` and `.yml`
4. **Private key format** - AGE private keys start with `AGE-SECRET-KEY-`, not `-----BEGIN`
5. **Flux namespace** - Deploy key secrets must be in `flux-system` namespace
6. **known_hosts format** - Use GitHub's current SSH key fingerprint (verify at github.com/meta)

### Integration with External Secrets

Note: SOPS is used for **Git-stored secrets** (deploy keys, initial bootstrap secrets). For application secrets, use **External Secrets Operator with 1Password** as the source of truth.

| Secret Type | Management Method |
|-------------|-------------------|
| Git deploy keys | SOPS/AGE encrypted in repo |
| Bootstrap secrets | SOPS/AGE encrypted in repo |
| Application secrets | External Secrets from 1Password |
| Database credentials | External Secrets from 1Password |
| API keys | External Secrets from 1Password |

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

