#!/bin/bash
set -e

##############################################################################
# OpenLearn Colombia - Deployment Validation Script
#
# This script runs both pre-deployment and post-deployment validation tests
# to ensure the deployment is ready and successful.
#
# Usage:
#   ./validate-deployment.sh [pre|post] [environment]
#
# Examples:
#   ./validate-deployment.sh pre staging
#   ./validate-deployment.sh post production
##############################################################################

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
VALIDATION_TYPE=${1:-pre}
ENVIRONMENT=${2:-staging}

# Environment URLs
case $ENVIRONMENT in
    staging)
        DEPLOYMENT_URL="https://staging.openlearn.colombia"
        ;;
    production)
        DEPLOYMENT_URL="https://openlearn.colombia"
        ;;
    local)
        DEPLOYMENT_URL="http://localhost:8000"
        ;;
    *)
        echo -e "${RED}Error: Environment must be 'local', 'staging', or 'production'${NC}"
        exit 1
        ;;
esac

# Validation type check
if [ "$VALIDATION_TYPE" != "pre" ] && [ "$VALIDATION_TYPE" != "post" ]; then
    echo -e "${RED}Error: Validation type must be 'pre' or 'post'${NC}"
    echo "Usage: $0 [pre|post] [environment]"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     OpenLearn Colombia - Deployment Validation           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "  Validation Type: ${VALIDATION_TYPE}-deployment"
echo "  Environment: $ENVIRONMENT"
if [ "$VALIDATION_TYPE" == "post" ]; then
    echo "  Target URL: $DEPLOYMENT_URL"
fi
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Install test dependencies if needed
echo -e "${GREEN}Checking test dependencies...${NC}"
pip install -q requests psycopg2-binary redis elasticsearch 2>/dev/null || true

# Run appropriate validation
cd "$(dirname "$0")/../../tests/deployment"

if [ "$VALIDATION_TYPE" == "pre" ]; then
    # Pre-deployment validation
    echo -e "${GREEN}Running pre-deployment validation...${NC}"
    echo ""

    python3 pre_deployment.py
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Pre-deployment validation PASSED${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Review validation results above"
        echo "  2. Proceed with deployment"
        echo "  3. Run post-deployment validation after deployment"
        echo ""
    else
        echo ""
        echo -e "${RED}❌ Pre-deployment validation FAILED${NC}"
        echo ""
        echo "Action required:"
        echo "  1. Review errors above"
        echo "  2. Fix identified issues"
        echo "  3. Re-run validation"
        echo "  4. DO NOT deploy until validation passes"
        echo ""
    fi

    exit $EXIT_CODE

else
    # Post-deployment validation
    echo -e "${GREEN}Running post-deployment smoke tests...${NC}"
    echo ""

    export DEPLOYMENT_URL
    python3 post_deployment.py
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Post-deployment validation PASSED${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Monitor application metrics"
        echo "  2. Check error logs"
        echo "  3. Run load tests (optional)"
        echo "  4. Notify team of successful deployment"
        echo ""
    else
        echo ""
        echo -e "${RED}❌ Post-deployment validation FAILED${NC}"
        echo ""
        echo "Action required:"
        echo "  1. Review errors above"
        echo "  2. Check application logs"
        echo "  3. Verify database connectivity"
        echo "  4. Consider rollback if critical issues"
        echo ""
        echo "Rollback command:"
        echo "  ./scripts/deployment/rollback.sh $ENVIRONMENT application"
        echo ""
    fi

    exit $EXIT_CODE
fi
