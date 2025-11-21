# Security Scanning - Quick Start Guide

## TL;DR

Run local security scans before committing:

**Windows:**
```bash
scripts\security-scan.bat
```

**Linux/Mac:**
```bash
./scripts/security-scan.sh
```

---

## What Gets Scanned

### Automated (GitHub Actions - Every Push/PR)
- **Snyk**: Dependency vulnerabilities (Python + NPM) ✅ Configured
- **Trivy**: Filesystem vulnerabilities
- **Bandit**: Python code security issues
- **Safety**: Python dependency CVEs
- **NPM Audit**: Frontend dependency vulnerabilities
- **Dependency Review**: PR dependency changes (pull requests only)

### Manual (Run Locally)
```bash
# Python security scan
bandit -r src/
safety check -r requirements.txt

# Frontend security scan
cd frontend
npm audit
snyk test

# Full project scan
snyk test
```

---

## Setup (One-Time)

### 1. Install Tools

**Python Tools:**
```bash
pip install bandit safety
```

**Snyk (Global):**
```bash
npm install -g snyk
snyk auth  # Requires Snyk account (free)
```

### 2. GitHub Actions Setup

Add to GitHub repository secrets:
- `SNYK_TOKEN` - Get from https://snyk.io/account

Enable in Settings → Security:
- Dependency graph
- Dependabot alerts
- Dependabot security updates
- Code scanning

---

## Interpreting Results

### Severity Levels

| Level | Action Required | Timeline |
|-------|----------------|----------|
| **Critical** | Fix immediately | 24 hours |
| **High** | Fix soon | 1 week |
| **Medium** | Plan fix | 1 month |
| **Low** | Monitor | 3 months |

### Common Fixes

**Dependency Vulnerability:**
```bash
# Python
pip install --upgrade vulnerable-package

# NPM
npm update vulnerable-package
# or
npm audit fix
```

**Code Issue (Bandit):**
- Review flagged code
- Apply secure coding pattern
- Add `# nosec` comment if false positive (with justification)

---

## Security Checklist

Before every commit:
- [ ] Run `scripts/security-scan.bat` (Windows) or `./scripts/security-scan.sh` (Linux/Mac)
- [ ] Fix any HIGH or CRITICAL issues
- [ ] Document any ignored warnings

Before every release:
- [ ] Review all security scan results in GitHub Security tab
- [ ] Update dependencies to latest stable versions
- [ ] Run full security audit: `snyk test --all-projects`

---

## Need Help?

- **Documentation**: See `SECURITY_SCANNING.md` for detailed guide
- **Security Issue**: Create issue with `security` label
- **Questions**: Contact development team

---

## Quick Reference

| Tool | Purpose | Command |
|------|---------|---------|
| Snyk | Dependency vulnerabilities | `snyk test` |
| Trivy | Filesystem scan | `trivy fs .` |
| Bandit | Python code security | `bandit -r src/` |
| Safety | Python CVE check | `safety check` |
| NPM Audit | Frontend dependencies | `npm audit` |

**Full Docs**: `SECURITY_SCANNING.md`
