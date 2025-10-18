#!/bin/bash
set -e

##############################################################################
# OpenLearn Colombia - Load Testing Script
#
# This script runs comprehensive load tests against the deployment and
# generates detailed performance reports.
#
# Usage:
#   ./run-load-tests.sh [environment] [users] [duration]
#
# Examples:
#   ./run-load-tests.sh staging 500 5m
#   ./run-load-tests.sh production 1000 10m
##############################################################################

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
ENVIRONMENT=${1:-staging}
USERS=${2:-1000}
DURATION=${3:-5m}
SPAWN_RATE=10

# Environment URLs
case $ENVIRONMENT in
    staging)
        HOST_URL="https://staging.openlearn.colombia"
        ;;
    production)
        HOST_URL="https://openlearn.colombia"
        ;;
    local)
        HOST_URL="http://localhost:8000"
        ;;
    *)
        echo -e "${RED}Error: Environment must be 'local', 'staging', or 'production'${NC}"
        exit 1
        ;;
esac

# Output files
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="load-test-reports/${ENVIRONMENT}/${TIMESTAMP}"
HTML_REPORT="${REPORT_DIR}/report.html"
CSV_PREFIX="${REPORT_DIR}/results"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     OpenLearn Colombia - Load Testing Suite              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Environment: $ENVIRONMENT"
echo "  Target URL: $HOST_URL"
echo "  Users: $USERS"
echo "  Duration: $DURATION"
echo "  Spawn Rate: $SPAWN_RATE/sec"
echo "  Report Directory: $REPORT_DIR"
echo ""

# Create report directory
mkdir -p "$REPORT_DIR"

# Confirm for production
if [ "$ENVIRONMENT" == "production" ]; then
    echo -e "${YELLOW}⚠️  WARNING: Running load tests against PRODUCTION${NC}"
    read -p "Are you sure? (yes/no): " confirmation
    if [ "$confirmation" != "yes" ]; then
        echo "Load test cancelled"
        exit 0
    fi
fi

# Check if locust is installed
if ! command -v locust &> /dev/null; then
    echo -e "${RED}Error: Locust is not installed${NC}"
    echo "Install with: pip install locust"
    exit 1
fi

# Pre-test health check
echo -e "${GREEN}Running pre-test health check...${NC}"
if curl -f -s "${HOST_URL}/health/" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Target is healthy${NC}"
else
    echo -e "${RED}❌ Target health check failed${NC}"
    echo "URL: ${HOST_URL}/health/"
    read -p "Continue anyway? (yes/no): " continue_confirmation
    if [ "$continue_confirmation" != "yes" ]; then
        exit 1
    fi
fi

# Run load tests
echo ""
echo -e "${GREEN}Starting load tests...${NC}"
echo ""

cd "$(dirname "$0")/../../tests/load"

locust -f locustfile.py \
    --host "$HOST_URL" \
    --users "$USERS" \
    --spawn-rate "$SPAWN_RATE" \
    --run-time "$DURATION" \
    --headless \
    --html "$HTML_REPORT" \
    --csv "$CSV_PREFIX" \
    2>&1 | tee "${REPORT_DIR}/console.log"

EXIT_CODE=$?

# Analyze results
echo ""
echo -e "${GREEN}Analyzing results...${NC}"

# Extract key metrics from CSV
if [ -f "${CSV_PREFIX}_stats.csv" ]; then
    # Get p95 response time
    P95=$(awk -F',' 'NR>1 && $1=="Aggregated" {print $9}' "${CSV_PREFIX}_stats.csv")
    P99=$(awk -F',' 'NR>1 && $1=="Aggregated" {print $10}' "${CSV_PREFIX}_stats.csv")
    AVG=$(awk -F',' 'NR>1 && $1=="Aggregated" {print $6}' "${CSV_PREFIX}_stats.csv")
    FAILURE_RATE=$(awk -F',' 'NR>1 && $1=="Aggregated" {print $4}' "${CSV_PREFIX}_stats.csv")
    RPS=$(awk -F',' 'NR>1 && $1=="Aggregated" {print $11}' "${CSV_PREFIX}_stats.csv")

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                  Performance Summary                      ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  Average Response Time: ${AVG}ms"
    echo "  p95 Response Time: ${P95}ms"
    echo "  p99 Response Time: ${P99}ms"
    echo "  Failure Rate: ${FAILURE_RATE}%"
    echo "  Requests/sec: ${RPS}"
    echo ""

    # Check against targets
    SUCCESS=true

    if (( $(echo "$P95 > 500" | bc -l) )); then
        echo -e "${RED}❌ p95 response time exceeds target (500ms)${NC}"
        SUCCESS=false
    else
        echo -e "${GREEN}✅ p95 response time meets target (<500ms)${NC}"
    fi

    if (( $(echo "$FAILURE_RATE > 1.0" | bc -l) )); then
        echo -e "${RED}❌ Failure rate exceeds target (1%)${NC}"
        SUCCESS=false
    else
        echo -e "${GREEN}✅ Failure rate meets target (<1%)${NC}"
    fi

    if (( $(echo "$RPS < 100" | bc -l) )); then
        echo -e "${YELLOW}⚠️  Throughput below minimum target (100 req/s)${NC}"
    else
        echo -e "${GREEN}✅ Throughput meets target (>100 req/s)${NC}"
    fi

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"

    if [ "$SUCCESS" = true ]; then
        echo "║              ✅ LOAD TEST PASSED ✅                        ║"
    else
        echo "║              ❌ LOAD TEST FAILED ❌                        ║"
    fi

    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
fi

# Generate summary report
cat > "${REPORT_DIR}/summary.txt" << EOF
OpenLearn Colombia - Load Test Summary
========================================

Test Configuration:
------------------
Environment: $ENVIRONMENT
Target: $HOST_URL
Users: $USERS
Duration: $DURATION
Spawn Rate: $SPAWN_RATE/sec
Timestamp: $TIMESTAMP

Performance Metrics:
-------------------
Average Response Time: ${AVG}ms
p95 Response Time: ${P95}ms
p99 Response Time: ${P99}ms
Failure Rate: ${FAILURE_RATE}%
Requests/sec: ${RPS}

Test Result: $([ "$SUCCESS" = true ] && echo "PASSED" || echo "FAILED")

Files Generated:
---------------
- HTML Report: $HTML_REPORT
- CSV Stats: ${CSV_PREFIX}_stats.csv
- CSV Failures: ${CSV_PREFIX}_failures.csv
- CSV History: ${CSV_PREFIX}_stats_history.csv
- Console Log: ${REPORT_DIR}/console.log
- Summary: ${REPORT_DIR}/summary.txt
EOF

# Display report location
echo -e "${GREEN}Reports saved to: $REPORT_DIR${NC}"
echo ""
echo "View HTML report:"
echo "  open $HTML_REPORT"
echo ""
echo "View summary:"
echo "  cat ${REPORT_DIR}/summary.txt"
echo ""

# Exit with appropriate code
if [ "$SUCCESS" = true ]; then
    exit 0
else
    exit 1
fi
