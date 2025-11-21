#!/bin/bash
# Local Security Scanning Script
# Run this before committing code to catch security issues early

set -e

echo "=================================="
echo "AI Tester Security Scan"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if any scan failed
FAILED=0

# Function to run a scan
run_scan() {
    local name=$1
    local command=$2

    echo "Running $name..."
    if eval "$command"; then
        echo -e "${GREEN}✓${NC} $name passed"
    else
        echo -e "${RED}✗${NC} $name found issues"
        FAILED=1
    fi
    echo ""
}

# 1. Bandit - Python code security scanner
echo "1/5: Bandit (Python Code Security)"
if command -v bandit &> /dev/null; then
    run_scan "Bandit" "bandit -r src/ -ll"
else
    echo -e "${YELLOW}⚠${NC} Bandit not installed. Install with: pip install bandit"
    echo ""
fi

# 2. Safety - Python dependency vulnerability checker
echo "2/5: Safety (Python Dependencies)"
if command -v safety &> /dev/null; then
    run_scan "Safety" "safety check -r requirements.txt"
else
    echo -e "${YELLOW}⚠${NC} Safety not installed. Install with: pip install safety"
    echo ""
fi

# 3. Snyk - Multi-language vulnerability scanner
echo "3/5: Snyk (Python Dependencies)"
if command -v snyk &> /dev/null; then
    run_scan "Snyk Python" "snyk test --file=requirements.txt --severity-threshold=high"
else
    echo -e "${YELLOW}⚠${NC} Snyk not installed. Install with: npm install -g snyk"
    echo ""
fi

# 4. NPM Audit - Frontend dependencies
echo "4/5: NPM Audit (Frontend Dependencies)"
if [ -d "frontend" ]; then
    cd frontend
    run_scan "NPM Audit" "npm audit --audit-level=high"
    cd ..
else
    echo -e "${YELLOW}⚠${NC} Frontend directory not found"
    echo ""
fi

# 5. Snyk Frontend
echo "5/5: Snyk (Frontend Dependencies)"
if command -v snyk &> /dev/null && [ -d "frontend" ]; then
    cd frontend
    run_scan "Snyk Frontend" "snyk test --severity-threshold=high"
    cd ..
else
    echo -e "${YELLOW}⚠${NC} Snyk not installed or frontend directory not found"
    echo ""
fi

# Summary
echo "=================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All security scans passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some security scans found issues${NC}"
    echo "Review the output above and fix issues before committing"
    exit 1
fi
