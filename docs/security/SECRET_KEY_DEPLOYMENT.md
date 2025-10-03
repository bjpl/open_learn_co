# SECRET_KEY Deployment Guide

## Critical Security Notice

The `SECRET_KEY` is the most important security configuration in your FastAPI application. It is used for:
- JWT token signing and verification
- Session management
- Cryptographic operations
- API authentication

**NEVER commit the actual SECRET_KEY to version control!**

## Quick Start

### 1. Generate a Production SECRET_KEY

```bash
# Recommended: Use the provided script (64 bytes)
python backend/scripts/generate_secret_key.py

# Alternative: Quick generation (64 bytes)
python -c "import secrets; print(secrets.token_urlsafe(64))"

# For maximum security (128 bytes)
python backend/scripts/generate_secret_key.py --bytes 128
```

### 2. Set the Environment Variable

#### Linux/macOS (Development)
```bash
# Add to ~/.bashrc or ~/.zshrc
export SECRET_KEY="your-generated-key-here"

# Or add to .env file (DO NOT commit!)
echo "SECRET_KEY=your-generated-key-here" >> backend/.env
```

#### Windows (Development)
```powershell
# PowerShell
$env:SECRET_KEY="your-generated-key-here"

# Or add to .env file
"SECRET_KEY=your-generated-key-here" | Out-File -Append backend/.env
```

#### Docker (Production)
```dockerfile
# docker-compose.yml
services:
  backend:
    environment:
      - SECRET_KEY=${SECRET_KEY}
```

```bash
# Set in host environment before running docker-compose
export SECRET_KEY="your-generated-key-here"
docker-compose up -d
```

## Production Deployment

### AWS Secrets Manager

```bash
# Store the secret
aws secretsmanager create-secret \
    --name openlearn/production/secret-key \
    --secret-string "your-generated-key-here"

# Retrieve in application
aws secretsmanager get-secret-value \
    --secret-id openlearn/production/secret-key \
    --query SecretString --output text
```

### Docker Secrets

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    secrets:
      - secret_key
    environment:
      - SECRET_KEY_FILE=/run/secrets/secret_key

secrets:
  secret_key:
    external: true
```

```bash
# Create the secret
echo "your-generated-key-here" | docker secret create secret_key -
```

### Kubernetes Secrets

```bash
# Create secret
kubectl create secret generic openlearn-secret-key \
    --from-literal=secret-key="your-generated-key-here"

# Reference in deployment
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: backend
    env:
    - name: SECRET_KEY
      valueFrom:
        secretKeyRef:
          name: openlearn-secret-key
          key: secret-key
```

### HashiCorp Vault

```bash
# Store secret
vault kv put secret/openlearn/production \
    secret_key="your-generated-key-here"

# Retrieve in application
vault kv get -field=secret_key secret/openlearn/production
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Validate Security
        env:
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
          ENVIRONMENT: production
          DEBUG: false
        run: |
          python backend/scripts/validate_security.py --strict

      - name: Deploy
        env:
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
        run: |
          # Your deployment commands
```

**GitHub Repository Settings:**
1. Go to Settings → Secrets and variables → Actions
2. Add new repository secret: `SECRET_KEY`
3. Paste your generated key
4. Never log or echo this value in CI/CD

### GitLab CI/CD

```yaml
# .gitlab-ci.yml
deploy:
  stage: deploy
  script:
    - python backend/scripts/validate_security.py --strict
    - # Your deployment commands
  variables:
    ENVIRONMENT: production
    DEBUG: "false"
  only:
    - main
```

**GitLab Settings:**
1. Go to Settings → CI/CD → Variables
2. Add variable: `SECRET_KEY`
3. Check "Masked" and "Protected"
4. Paste your generated key

## Environment-Specific Keys

**CRITICAL: Use different SECRET_KEYs for each environment!**

```bash
# Development
python backend/scripts/generate_secret_key.py > .env.development

# Staging
python backend/scripts/generate_secret_key.py > .env.staging

# Production
python backend/scripts/generate_secret_key.py > .env.production
```

## Key Rotation

### Why Rotate Keys?

- Compliance requirements (PCI-DSS, HIPAA, etc.)
- Security best practice (every 90 days recommended)
- After security incidents
- Employee turnover

### Rotation Process

1. **Generate new key:**
   ```bash
   python backend/scripts/generate_secret_key.py > new_key.txt
   ```

2. **Update environment variable:**
   ```bash
   # Update in your secrets manager
   aws secretsmanager update-secret \
       --secret-id openlearn/production/secret-key \
       --secret-string "$(cat new_key.txt)"
   ```

3. **Rolling update (zero downtime):**
   ```bash
   # Deploy with both old and new keys
   # Allow grace period for existing tokens
   # Remove old key after grace period (7 days recommended)
   ```

4. **Invalidate old tokens (if needed):**
   ```bash
   # Implement token versioning in your application
   # Or force re-authentication of all users
   ```

## Security Validation

### Pre-Deployment Check

```bash
# Run security validation before every deployment
cd backend
SECRET_KEY="your-key-here" \
ENVIRONMENT=production \
DEBUG=false \
python scripts/validate_security.py --strict
```

### Automated Checks

Add to your CI/CD pipeline:

```yaml
# Prevent deployment with insecure keys
- name: Security Validation
  run: |
    if [[ "$SECRET_KEY" == *"INSECURE"* ]] || [[ "$SECRET_KEY" == *"REPLACE"* ]]; then
      echo "ERROR: Insecure SECRET_KEY detected!"
      exit 1
    fi
    python backend/scripts/validate_security.py --strict
```

## Troubleshooting

### Key Not Working

1. **Verify key is set:**
   ```bash
   echo $SECRET_KEY | wc -c  # Should be > 32
   ```

2. **Check for special characters:**
   ```bash
   # URL-safe base64 should only contain: A-Za-z0-9_-
   ```

3. **Verify no quotes or spaces:**
   ```bash
   # Bad: SECRET_KEY="key with spaces"
   # Good: SECRET_KEY=key_without_spaces
   ```

### Key Too Short Error

```bash
# Minimum 32 bytes required
python backend/scripts/generate_secret_key.py --bytes 64
```

### Key Contains Default Value

```bash
# Never use these values:
# - INSECURE_DEFAULT_KEY_REPLACE_IN_PRODUCTION
# - your-secret-key-here-change-in-production
# - REPLACE_THIS_IN_PRODUCTION_USE_generate_secret_key_script

# Always generate a new key:
python backend/scripts/generate_secret_key.py
```

## Security Best Practices

### DO ✓

- Generate unique keys for each environment
- Use 64+ bytes for production
- Store in secure vaults (AWS Secrets Manager, HashiCorp Vault)
- Rotate keys every 90 days
- Validate keys in CI/CD pipeline
- Use environment variables, never hardcode
- Restrict access to production keys
- Log key rotation events
- Monitor for unauthorized access

### DON'T ✗

- Commit keys to version control
- Share keys via email/Slack/chat
- Use the same key across environments
- Use default or example keys
- Store keys in plaintext files
- Log or print keys in application
- Use keys shorter than 32 bytes
- Share production keys with developers
- Store keys in application code

## Compliance

### PCI-DSS
- Rotate keys every 90 days
- Restrict access to keys
- Log all key access
- Encrypt keys at rest

### HIPAA
- Use FIPS 140-2 validated cryptography
- Implement key rotation
- Maintain audit logs
- Encrypt keys in transit and at rest

### SOC 2
- Document key management procedures
- Implement access controls
- Monitor key usage
- Regular security audits

## Support

For security issues or questions:
- **DO NOT** post SECRET_KEYs in issue trackers
- Contact security team privately
- Use encrypted communication for sensitive information

## References

- [Python secrets module documentation](https://docs.python.org/3/library/secrets.html)
- [OWASP Key Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
- [NIST Cryptographic Key Management](https://csrc.nist.gov/projects/key-management)
