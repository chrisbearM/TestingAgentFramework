# Security Scanning Guide

## Overview

This document describes the security scanning tools integrated into the AI Tester Framework to detect vulnerabilities, insecure dependencies, and security issues in both Python backend and React frontend code.

**Status**: ✅ Multi-tool security scanning configured
- **Snyk**: Dependency vulnerability scanning (Python + NPM)
- **Trivy**: Filesystem and container vulnerability scanning
- **Bandit**: Python code security linter
- **Safety**: Python dependency vulnerability checker
- **NPM Audit**: Node.js dependency vulnerability checker
- **GitHub Dependency Review**: PR-based dependency analysis

---

## Quick Start

### Local Scanning (Manual)

**1. Install Snyk CLI:**
```bash
# Install globally
npm install -g snyk

# Authenticate (requires Snyk account)
snyk auth
```

**2. Run Python Security Scan:**
```bash
# Snyk Python scan
snyk test --file=requirements.txt

# Bandit Python linter
pip install bandit
bandit -r src/

# Safety dependency check
pip install safety
safety check -r requirements.txt
```

**3. Run Frontend Security Scan:**
```bash
cd frontend

# Snyk NPM scan
snyk test

# NPM audit
npm audit

# NPM audit fix (auto-fix vulnerabilities)
npm audit fix
```

---

## Automated Scanning (CI/CD)

### GitHub Actions Workflow

**File**: `.github/workflows/security-scan.yml`

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Daily scheduled scan at 2 AM UTC
- Manual workflow dispatch

**Scans Performed:**

1. **Snyk Python** - Scans `requirements.txt` for vulnerable dependencies
2. **Snyk Frontend** - Scans `frontend/package.json` for vulnerable NPM packages
3. **Dependency Review** - GitHub native PR dependency analysis
4. **Trivy** - Filesystem vulnerability scanner
5. **Bandit** - Python code security linter (detects hardcoded secrets, SQL injection, etc.)
6. **Safety** - Python dependency vulnerability database check
7. **NPM Audit** - Node.js dependency vulnerability check

**Results:**
- Uploaded to GitHub Security tab (SARIF format)
- Build fails on HIGH or CRITICAL vulnerabilities (configurable)
- Artifacts available for download

---

## Security Scanning Tools

### 1. Snyk

**What it scans:**
- Python dependencies (`requirements.txt`)
- NPM dependencies (`package.json`)
- Known CVEs in dependencies
- License compliance issues

**Configuration**: `.snyk` file

**Severity Levels:**
- **Critical**: Immediate action required
- **High**: Action required soon
- **Medium**: Review and plan fix
- **Low**: Monitor

**Features:**
- Auto-fix pull requests
- License compliance scanning
- Container scanning
- Infrastructure as Code scanning

**Setup:**
1. Sign up at https://snyk.io
2. Add repository to Snyk dashboard
3. Add `SNYK_TOKEN` to GitHub Secrets
4. Configure `.snyk` policy file

---

### 2. Trivy

**What it scans:**
- Filesystem vulnerabilities
- OS packages
- Application dependencies (Python, Node.js)
- Misconfigurations

**Features:**
- Fast scanning (local database)
- No external API calls (can run offline)
- Detects vulnerabilities in:
  - Python packages
  - NPM packages
  - OS dependencies

**Configuration:**
- Scans entire project directory
- Focuses on HIGH and CRITICAL severities
- Results uploaded to GitHub Security

---

### 3. Bandit

**What it scans:**
- Python code security issues
- Common vulnerability patterns:
  - Hardcoded passwords
  - SQL injection
  - Command injection
  - Insecure deserialization
  - Weak cryptography
  - Path traversal

**Example Detections:**
```python
# BAD - Bandit will flag this
password = "hardcoded_password"  # B105: Hardcoded password
exec(user_input)  # B102: exec used
eval(user_input)  # B307: eval used

# GOOD - Safe alternatives
password = os.environ["PASSWORD"]
# Use ast.literal_eval() instead of eval()
```

**Configuration:**
- Scans `src/` directory recursively
- Excludes test files
- Reports in SARIF format

---

### 4. Safety

**What it scans:**
- Python dependencies against Safety DB
- Known security vulnerabilities
- CVE database for Python packages

**Database:**
- Curated vulnerability database
- Regularly updated
- Free and open source

**Usage:**
```bash
# Check installed packages
safety check

# Check requirements file
safety check -r requirements.txt

# Generate JSON report
safety check --json --output safety-report.json
```

---

### 5. NPM Audit

**What it scans:**
- NPM package vulnerabilities
- Direct and transitive dependencies
- Known CVEs in Node.js ecosystem

**Severity Levels:**
- **Critical**: 0-day or actively exploited
- **High**: Exploitable in common use cases
- **Moderate**: Exploitable in specific scenarios
- **Low**: Minimal risk

**Auto-Fix:**
```bash
# Automatically fix vulnerabilities (may update packages)
npm audit fix

# Fix including breaking changes
npm audit fix --force
```

---

### 6. GitHub Dependency Review

**What it scans:**
- New dependencies added in PRs
- Dependency version changes
- Known vulnerabilities in changed dependencies
- License changes

**Features:**
- Native GitHub integration
- No external service required
- Automatic PR comments
- Configurable fail thresholds

---

## Configuration Files

### `.snyk` Policy File

```yaml
# Snyk policy file
version: v1.25.0

# Ignore specific vulnerabilities (with justification)
ignore:
  'SNYK-PYTHON-PACKAGE-ID':
    - '*':
        reason: 'Not exploitable in our use case'
        expires: '2025-12-31T00:00:00.000Z'

# Severity threshold
failThreshold: high

# Exclude paths
exclude:
  - tests/**
  - venv/**
  - frontend/node_modules/**
```

### `.banditrc` (Optional)

```yaml
# Bandit configuration
exclude_dirs:
  - /tests
  - /venv
  - /.venv

tests:
  - B201  # flask_debug_true
  - B301  # pickle
  - B302  # marshal
  - B303  # md5
  - B304  # md5_insecure
  - B305  # sha1_insecure
  - B306  # tempfile
  - B308  # mark_safe
  - B309  # HTTPSConnection
  - B310  # urllib
  - B311  # random
  - B312  # telnetlib
  - B315  # xml
  - B316  # xml
  - B317  # xml
  - B318  # xml
  - B319  # xml
  - B320  # xml
  - B321  # ftplib
  - B322  # input
  - B323  # unverified_context
  - B324  # hashlib
  - B325  # tempnam
  - B401  # import_telnetlib
  - B402  # import_ftplib
  - B403  # import_pickle
  - B404  # import_subprocess
  - B405  # import_xml_etree
  - B406  # import_xml_sax
  - B407  # import_xml_expat
  - B408  # import_xml_minidom
  - B409  - import_xml_pulldom
  - B410  # import_lxml
  - B411  # import_xmlrpclib
  - B412  # import_httpoxy
  - B501  # request_with_no_cert_validation
  - B502  # ssl_with_bad_version
  - B503  # ssl_with_bad_defaults
  - B504  # ssl_with_no_version
  - B505  # weak_cryptographic_key
  - B506  # yaml_load
  - B507  # ssh_no_host_key_verification
  - B601  # paramiko_calls
  - B602  # shell_without_shellfalse
  - B603  # subprocess_without_shell_equals_true
  - B604  # any_other_function_with_shell_equals_true
  - B605  # start_process_with_a_shell
  - B606  # start_process_with_no_shell
  - B607  # start_process_with_partial_path
  - B608  # hardcoded_sql_expressions
  - B609  # linux_commands_wildcard_injection
  - B610  # django_rawsql
  - B611  # django_extra_used
  - B701  # jinja2_autoescape_false
  - B702  # use_of_mako_templates
  - B703  # django_mark_safe
```

---

## Security Scan Results

### Interpreting Results

**Example Snyk Output:**
```
Testing /path/to/ai-tester-framework...

Tested 45 dependencies for known issues, found 3 issues:

✗ High severity vulnerability found in fastapi
  Description: Denial of Service
  Info: https://snyk.io/vuln/SNYK-PYTHON-FASTAPI-123456
  Introduced through: fastapi@0.100.0
  Fixed in: fastapi@0.110.0

✗ Medium severity vulnerability found in pillow
  Description: Out-of-bounds Read
  Info: https://snyk.io/vuln/SNYK-PYTHON-PILLOW-234567
  Introduced through: pillow@9.5.0
  Fixed in: pillow@10.0.0
```

**Action Steps:**
1. **Critical/High**: Upgrade immediately or apply workaround
2. **Medium**: Schedule upgrade in next sprint
3. **Low**: Monitor and review quarterly

---

## Common Vulnerabilities to Watch For

### Python Backend

**1. Dependency Vulnerabilities**
- Outdated packages with known CVEs
- **Action**: Keep dependencies updated

**2. Code Injection**
```python
# Vulnerable
exec(user_input)
eval(user_input)

# Safe
import ast
ast.literal_eval(user_input)
```

**3. SQL Injection**
```python
# Vulnerable
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# Safe
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

**4. Path Traversal**
```python
# Vulnerable
with open(f"./files/{filename}") as f:

# Safe
import os
safe_path = os.path.abspath(os.path.join("./files", filename))
if safe_path.startswith(os.path.abspath("./files")):
    with open(safe_path) as f:
```

### Frontend

**1. Dependency Vulnerabilities**
- React, React-DOM, Vite, etc.
- **Action**: Run `npm audit fix` regularly

**2. XSS (Cross-Site Scripting)**
```jsx
// Vulnerable
<div dangerouslySetInnerHTML={{__html: userInput}} />

// Safe
<div>{userInput}</div>  // React auto-escapes
```

**3. Sensitive Data Exposure**
```javascript
// Vulnerable - API keys in frontend
const API_KEY = "sk-abc123";

// Safe - Use environment variables and proxy through backend
const API_URL = import.meta.env.VITE_API_URL;
```

---

## Integration with CI/CD

### GitHub Actions Setup

**1. Add Snyk Token:**
- Go to GitHub repo → Settings → Secrets → Actions
- Add secret: `SNYK_TOKEN` (get from https://snyk.io)

**2. Enable Security Tab:**
- Go to repo → Settings → Code security and analysis
- Enable "Dependency graph"
- Enable "Dependabot alerts"
- Enable "Dependabot security updates"
- Enable "Code scanning" (for SARIF uploads)

**3. Review Results:**
- Check "Security" tab in GitHub repo
- View alerts by severity
- Track remediation progress

---

## Best Practices

### Development Workflow

1. **Before Committing:**
   ```bash
   # Run local security checks
   bandit -r src/
   safety check -r requirements.txt
   npm audit (in frontend/)
   ```

2. **Pull Requests:**
   - Automated scans run on every PR
   - Review security tab for new vulnerabilities
   - Fix HIGH/CRITICAL before merging

3. **Regular Maintenance:**
   - Review security alerts weekly
   - Update dependencies monthly
   - Run full security audit quarterly

### Dependency Updates

**Python:**
```bash
# Check outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update requirements.txt
pip freeze > requirements.txt
```

**NPM:**
```bash
# Check outdated packages
npm outdated

# Update specific package
npm update package-name

# Update all packages (carefully!)
npm update
```

---

## Vulnerability Response Process

### Priority Levels

**Critical (P0):**
- **Timeline**: Fix within 24 hours
- **Action**: Hotfix and deploy immediately
- **Examples**: RCE, authentication bypass, data breach

**High (P1):**
- **Timeline**: Fix within 1 week
- **Action**: Schedule in current sprint
- **Examples**: XSS, CSRF, privilege escalation

**Medium (P2):**
- **Timeline**: Fix within 1 month
- **Action**: Add to backlog, schedule next sprint
- **Examples**: Information disclosure, DoS

**Low (P3):**
- **Timeline**: Fix within 3 months
- **Action**: Monitor, fix with regular maintenance
- **Examples**: Minor information leaks, low-impact DoS

### Remediation Steps

1. **Verify**: Confirm vulnerability applies to your use case
2. **Assess Impact**: Determine actual risk in production
3. **Plan Fix**: Upgrade, patch, or implement workaround
4. **Test**: Ensure fix doesn't break functionality
5. **Deploy**: Roll out fix to production
6. **Verify**: Re-scan to confirm vulnerability resolved

---

## False Positives

### Handling False Positives

If a vulnerability is flagged but doesn't apply:

**Snyk:**
```yaml
# Add to .snyk file
ignore:
  'SNYK-PYTHON-PACKAGE-12345':
    - '*':
        reason: 'Not exploitable - we only use safe subset of functionality'
        expires: '2025-12-31T00:00:00.000Z'
```

**Bandit:**
```python
# Add comment to ignore specific line
password = get_password_from_env()  # nosec B105
```

**Document reasoning** for all ignored vulnerabilities for audit purposes.

---

## Resources

### Documentation
- [Snyk Documentation](https://docs.snyk.io/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Safety Documentation](https://pyup.io/safety/)
- [NPM Audit](https://docs.npmjs.com/cli/v8/commands/npm-audit)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

### Security Databases
- [National Vulnerability Database (NVD)](https://nvd.nist.gov/)
- [CVE Details](https://www.cvedetails.com/)
- [Snyk Vulnerability DB](https://snyk.io/vuln/)
- [GitHub Advisory Database](https://github.com/advisories)

### Tools
- [Snyk CLI](https://github.com/snyk/cli)
- [Trivy](https://github.com/aquasecurity/trivy)
- [Bandit](https://github.com/PyCQA/bandit)
- [Safety](https://github.com/pyupio/safety)

---

## Current Security Status

**Last Full Scan**: Not yet run (awaiting Snyk token configuration)

**Known Issues**: None

**Upcoming Reviews**:
- Initial security scan after Snyk configuration
- Dependency update review: Quarterly

---

## Next Steps

1. ✅ Configure Snyk account and add `SNYK_TOKEN` to GitHub Secrets
2. ✅ Enable GitHub Security features (Dependabot, Code Scanning)
3. ⏳ Run initial security scan baseline
4. ⏳ Review and remediate any HIGH/CRITICAL vulnerabilities found
5. ⏳ Schedule regular security review cadence
6. ⏳ Train team on security scanning tools and processes

---

## Contact

For security concerns or questions:
- Create issue in GitHub repo with `security` label
- For private security disclosures, contact: [security contact email]

**Last Updated**: January 2025
**Document Owner**: Development Team
