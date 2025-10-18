#!/bin/bash

# Security Scanning Script for OpenLearn Colombia
# Runs comprehensive security scans using multiple tools

set -e  # Exit on error

echo "========================================="
echo "OpenLearn Security Scan"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create reports directory
REPORT_DIR="backend/security_reports"
mkdir -p "$REPORT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Reports will be saved to: $REPORT_DIR"
echo ""

# ============================================================================
# 1. Bandit - Python Security Linter
# ============================================================================
echo -e "${YELLOW}[1/5] Running Bandit (Python Security Linter)...${NC}"
if command -v bandit &> /dev/null; then
    bandit -r backend/app/ \
        -f json \
        -o "$REPORT_DIR/bandit_report_$TIMESTAMP.json" \
        --severity-level medium \
        --confidence-level medium \
        || echo -e "${RED}Bandit found security issues${NC}"

    # Also generate human-readable report
    bandit -r backend/app/ \
        -f txt \
        -o "$REPORT_DIR/bandit_report_$TIMESTAMP.txt" \
        --severity-level medium \
        --confidence-level medium \
        || echo -e "${RED}Bandit found security issues${NC}"

    echo -e "${GREEN}Bandit scan complete${NC}"
else
    echo -e "${RED}Bandit not installed. Install with: pip install bandit${NC}"
fi
echo ""

# ============================================================================
# 2. Safety - Dependency Vulnerability Scanner
# ============================================================================
echo -e "${YELLOW}[2/5] Running Safety (Dependency Scanner)...${NC}"
if command -v safety &> /dev/null; then
    safety check \
        --file backend/requirements.txt \
        --json \
        --output "$REPORT_DIR/safety_report_$TIMESTAMP.json" \
        || echo -e "${RED}Safety found vulnerable dependencies${NC}"

    # Human-readable report
    safety check \
        --file backend/requirements.txt \
        --output "$REPORT_DIR/safety_report_$TIMESTAMP.txt" \
        || echo -e "${RED}Safety found vulnerable dependencies${NC}"

    echo -e "${GREEN}Safety scan complete${NC}"
else
    echo -e "${RED}Safety not installed. Install with: pip install safety${NC}"
fi
echo ""

# ============================================================================
# 3. Semgrep - Semantic Code Analysis
# ============================================================================
echo -e "${YELLOW}[3/5] Running Semgrep (Semantic Analysis)...${NC}"
if command -v semgrep &> /dev/null; then
    semgrep \
        --config=auto \
        --config=p/owasp-top-ten \
        --config=p/security-audit \
        --config=p/python \
        --json \
        --output="$REPORT_DIR/semgrep_report_$TIMESTAMP.json" \
        backend/app/ \
        || echo -e "${RED}Semgrep found security issues${NC}"

    # Human-readable report
    semgrep \
        --config=auto \
        --config=p/owasp-top-ten \
        --config=p/security-audit \
        --config=p/python \
        --text \
        --output="$REPORT_DIR/semgrep_report_$TIMESTAMP.txt" \
        backend/app/ \
        || echo -e "${RED}Semgrep found security issues${NC}"

    echo -e "${GREEN}Semgrep scan complete${NC}"
else
    echo -e "${RED}Semgrep not installed. Install with: pip install semgrep${NC}"
fi
echo ""

# ============================================================================
# 4. Pip-audit - Python Package Vulnerability Scanner
# ============================================================================
echo -e "${YELLOW}[4/5] Running pip-audit (Package Scanner)...${NC}"
if command -v pip-audit &> /dev/null; then
    pip-audit \
        --requirement backend/requirements.txt \
        --format json \
        --output "$REPORT_DIR/pip_audit_report_$TIMESTAMP.json" \
        || echo -e "${RED}pip-audit found vulnerable packages${NC}"

    # Cyclone DX SBOM format
    pip-audit \
        --requirement backend/requirements.txt \
        --format cyclonedx-json \
        --output "$REPORT_DIR/sbom_$TIMESTAMP.json" \
        || echo -e "${RED}pip-audit found vulnerable packages${NC}"

    echo -e "${GREEN}pip-audit scan complete${NC}"
else
    echo -e "${RED}pip-audit not installed. Install with: pip install pip-audit${NC}"
fi
echo ""

# ============================================================================
# 5. Trivy - Comprehensive Vulnerability Scanner
# ============================================================================
echo -e "${YELLOW}[5/5] Running Trivy (Container/FS Scanner)...${NC}"
if command -v trivy &> /dev/null; then
    trivy fs \
        --severity HIGH,CRITICAL \
        --format json \
        --output "$REPORT_DIR/trivy_report_$TIMESTAMP.json" \
        backend/ \
        || echo -e "${RED}Trivy found vulnerabilities${NC}"

    # Human-readable report
    trivy fs \
        --severity HIGH,CRITICAL \
        --format table \
        --output "$REPORT_DIR/trivy_report_$TIMESTAMP.txt" \
        backend/ \
        || echo -e "${RED}Trivy found vulnerabilities${NC}"

    echo -e "${GREEN}Trivy scan complete${NC}"
else
    echo -e "${YELLOW}Trivy not installed (optional). Install: https://aquasecurity.github.io/trivy${NC}"
fi
echo ""

# ============================================================================
# Generate Summary Report
# ============================================================================
echo -e "${YELLOW}Generating summary report...${NC}"

SUMMARY_FILE="$REPORT_DIR/security_summary_$TIMESTAMP.txt"

cat > "$SUMMARY_FILE" <<EOF
========================================
OpenLearn Security Scan Summary
========================================
Date: $(date)
Scan ID: $TIMESTAMP

REPORTS GENERATED:
------------------
EOF

# List all generated reports
ls -lh "$REPORT_DIR"/*_$TIMESTAMP.* | awk '{print $9, "(" $5 ")"}' >> "$SUMMARY_FILE"

echo "" >> "$SUMMARY_FILE"
echo "CRITICAL FINDINGS:" >> "$SUMMARY_FILE"
echo "------------------" >> "$SUMMARY_FILE"

# Extract critical findings from each tool
if [ -f "$REPORT_DIR/bandit_report_$TIMESTAMP.json" ]; then
    HIGH_COUNT=$(grep -o '"issue_severity": "HIGH"' "$REPORT_DIR/bandit_report_$TIMESTAMP.json" | wc -l || echo "0")
    echo "Bandit: $HIGH_COUNT high-severity issues" >> "$SUMMARY_FILE"
fi

if [ -f "$REPORT_DIR/safety_report_$TIMESTAMP.json" ]; then
    VULN_COUNT=$(grep -o '"vulnerability"' "$REPORT_DIR/safety_report_$TIMESTAMP.json" | wc -l || echo "0")
    echo "Safety: $VULN_COUNT vulnerable dependencies" >> "$SUMMARY_FILE"
fi

if [ -f "$REPORT_DIR/semgrep_report_$TIMESTAMP.json" ]; then
    CRITICAL_COUNT=$(grep -o '"severity": "ERROR"' "$REPORT_DIR/semgrep_report_$TIMESTAMP.json" | wc -l || echo "0")
    echo "Semgrep: $CRITICAL_COUNT critical findings" >> "$SUMMARY_FILE"
fi

echo "" >> "$SUMMARY_FILE"
echo "RECOMMENDATIONS:" >> "$SUMMARY_FILE"
echo "----------------" >> "$SUMMARY_FILE"
echo "1. Review all HIGH/CRITICAL severity findings immediately" >> "$SUMMARY_FILE"
echo "2. Update vulnerable dependencies to patched versions" >> "$SUMMARY_FILE"
echo "3. Fix code-level security issues identified by Bandit/Semgrep" >> "$SUMMARY_FILE"
echo "4. Run OWASP Top 10 test suite: pytest backend/tests/security/" >> "$SUMMARY_FILE"
echo "5. Generate SBOM for supply chain security tracking" >> "$SUMMARY_FILE"

cat "$SUMMARY_FILE"

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Security scan complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Review reports in: $REPORT_DIR"
echo "Summary: $SUMMARY_FILE"
echo ""
echo "Next steps:"
echo "1. Review $SUMMARY_FILE"
echo "2. Address critical/high severity issues"
echo "3. Run: pytest backend/tests/security/ --verbose"
echo ""
