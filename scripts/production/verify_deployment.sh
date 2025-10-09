#!/bin/bash
# ============================================================================
# OpenLearn Colombia - Post-Deployment Verification Script
# ============================================================================
# Comprehensive health check after deployment
# Tests all critical systems and generates report
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0
WARNINGS=0

print_test() {
    echo -n "  Testing: $1... "
}

test_pass() {
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}"
    echo -e "    ${RED}Error: $1${NC}"
    ((FAILED++))
}

test_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}"
    echo -e "    ${YELLOW}Warning: $1${NC}"
    ((WARNINGS++))
}

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  OpenLearn Colombia - Deployment Verification           ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# Test 1: Docker Services
# ============================================================================

echo -e "${BLUE}[1] Docker Services${NC}"

print_test "Docker daemon"
if docker info > /dev/null 2>&1; then
    test_pass
else
    test_fail "Docker is not running"
fi

print_test "Docker Compose"
if docker-compose version > /dev/null 2>&1; then
    test_pass
else
    test_fail "Docker Compose not installed"
fi

print_test "Backend container"
if docker-compose ps | grep -q "backend.*Up"; then
    test_pass
else
    test_fail "Backend container not running"
fi

print_test "Frontend container"
if docker-compose ps | grep -q "frontend.*Up"; then
    test_pass
else
    test_fail "Frontend container not running"
fi

print_test "PostgreSQL container"
if docker-compose ps | grep -q "postgres.*Up"; then
    test_pass
else
    test_fail "PostgreSQL container not running"
fi

print_test "Redis container"
if docker-compose ps | grep -q "redis.*Up"; then
    test_pass
else
    test_fail "Redis container not running"
fi

# ============================================================================
# Test 2: Network Connectivity
# ============================================================================

echo ""
echo -e "${BLUE}[2] Network Connectivity${NC}"

print_test "Backend health endpoint (localhost)"
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health || echo "FAILED")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    test_pass
else
    test_fail "Backend not responding"
fi

print_test "Frontend (localhost)"
FRONTEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "000")
if [ "$FRONTEND_CODE" = "200" ]; then
    test_pass
else
    test_fail "Frontend returned HTTP $FRONTEND_CODE"
fi

print_test "Nginx service"
if systemctl is-active --quiet nginx; then
    test_pass
else
    test_fail "Nginx not running"
fi

# Extract domain from .env
DOMAIN=$(grep "^FRONTEND_URL=" .env 2>/dev/null | cut -d'=' -f2 | sed 's|https://||' | sed 's|http://||' || echo "")

if [ -n "$DOMAIN" ]; then
    print_test "External HTTPS ($DOMAIN)"
    HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/health || echo "000")
    if [ "$HTTPS_CODE" = "200" ]; then
        test_pass
    else
        test_warn "HTTPS not accessible (DNS may not be configured yet)"
    fi
fi

# ============================================================================
# Test 3: Database Connections
# ============================================================================

echo ""
echo -e "${BLUE}[3] Database Connections${NC}"

print_test "PostgreSQL connection"
if docker-compose exec -T postgres psql -U openlearn_prod -c "SELECT 1;" openlearn_production > /dev/null 2>&1; then
    test_pass
else
    test_fail "Cannot connect to PostgreSQL"
fi

print_test "User table exists"
if docker-compose exec -T postgres psql -U openlearn_prod -c "\d users" openlearn_production | grep -q "Table"; then
    test_pass
else
    test_fail "Users table not found"
fi

print_test "Migration 003 applied (timezone column)"
if docker-compose exec -T postgres psql -U openlearn_prod -c "\d users" openlearn_production | grep -q "timezone"; then
    test_pass
else
    test_warn "Timezone column not found - run migration 003"
fi

REDIS_PASSWORD=$(grep "^REDIS_PASSWORD=" .env 2>/dev/null | cut -d'=' -f2 || echo "")
print_test "Redis connection"
if [ -n "$REDIS_PASSWORD" ]; then
    if docker-compose exec -T redis redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q "PONG"; then
        test_pass
    else
        test_fail "Cannot connect to Redis"
    fi
else
    if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        test_pass
    else
        test_fail "Cannot connect to Redis"
    fi
fi

# ============================================================================
# Test 4: Configuration
# ============================================================================

echo ""
echo -e "${BLUE}[4] Configuration${NC}"

print_test ".env file exists"
if [ -f ".env" ]; then
    test_pass
else
    test_fail ".env file not found"
fi

print_test ".env permissions (should be 600)"
if [ -f ".env" ]; then
    PERMS=$(stat -c %a .env 2>/dev/null || stat -f %A .env 2>/dev/null || echo "000")
    if [ "$PERMS" = "600" ]; then
        test_pass
    else
        test_warn ".env permissions are $PERMS (should be 600)"
    fi
fi

print_test "ENVIRONMENT=production"
if grep -q "^ENVIRONMENT=production" .env 2>/dev/null; then
    test_pass
else
    test_fail "ENVIRONMENT not set to production in .env"
fi

print_test "SECRET_KEY set (not default)"
if grep -q "^SECRET_KEY=" .env 2>/dev/null; then
    if grep -q "INSECURE_DEFAULT_KEY" .env; then
        test_fail "SECRET_KEY is still the default insecure key!"
    else
        test_pass
    fi
else
    test_fail "SECRET_KEY not set in .env"
fi

print_test "SendGrid API key configured"
if grep -q "^SMTP_PASSWORD=SG\." .env 2>/dev/null; then
    test_pass
elif grep -q "YOUR_SENDGRID_API_KEY_HERE" .env 2>/dev/null; then
    test_warn "SendGrid API key not configured (emails will print to console only)"
else
    test_warn "SMTP_PASSWORD may not be configured correctly"
fi

# ============================================================================
# Test 5: Security
# ============================================================================

echo ""
echo -e "${BLUE}[5] Security${NC}"

print_test "Firewall (UFW)"
if command -v ufw > /dev/null && ufw status | grep -q "Status: active"; then
    test_pass
else
    test_warn "Firewall not active (run: sudo ufw enable)"
fi

if [ -n "$DOMAIN" ]; then
    print_test "SSL certificate"
    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        test_pass
    else
        test_warn "SSL certificate not found (run: sudo certbot --nginx -d $DOMAIN)"
    fi

    print_test "HTTPS redirect"
    HTTP_REDIRECT=$(curl -s -o /dev/null -w "%{http_code}" -L http://$DOMAIN 2>/dev/null || echo "000")
    if [ "$HTTP_REDIRECT" = "200" ]; then
        test_pass
    else
        test_warn "HTTP redirect may not be configured"
    fi
fi

# ============================================================================
# Test 6: Monitoring & Backups
# ============================================================================

echo ""
echo -e "${BLUE}[6] Monitoring & Backups${NC}"

print_test "Backup directory exists"
if [ -d "/backups/openlearn" ]; then
    test_pass
else
    test_warn "Backup directory not found (create: sudo mkdir -p /backups/openlearn)"
fi

print_test "Backup script installed"
if [ -f "/usr/local/bin/backup-openlearn" ]; then
    test_pass
else
    test_warn "Backup script not installed"
fi

print_test "Backup cron job"
if crontab -l 2>/dev/null | grep -q "backup-openlearn"; then
    test_pass
else
    test_warn "Backup cron job not scheduled"
fi

# ============================================================================
# Test 7: Application Functionality
# ============================================================================

echo ""
echo -e "${BLUE}[7] Application Functionality${NC}"

print_test "API documentation accessible"
DOCS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs || echo "000")
if [ "$DOCS_CODE" = "200" ]; then
    test_pass
else
    test_fail "API docs returned HTTP $DOCS_CODE"
fi

print_test "Database has users table"
USER_COUNT=$(docker-compose exec -T postgres psql -U openlearn_prod -t -c "SELECT COUNT(*) FROM users;" openlearn_production 2>/dev/null | tr -d ' ' || echo "0")
if [ "$USER_COUNT" = "0" ]; then
    test_warn "No users in database (this is OK for new deployment)"
else
    test_pass
fi

# ============================================================================
# Test 8: Resource Usage
# ============================================================================

echo ""
echo -e "${BLUE}[8] Resource Usage${NC}"

print_test "Disk space (need >10GB free)"
DISK_FREE_GB=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$DISK_FREE_GB" -gt 10 ]; then
    test_pass
    echo "    Free: ${DISK_FREE_GB}GB"
else
    test_warn "Low disk space: ${DISK_FREE_GB}GB free"
fi

print_test "Memory usage (should be <80%)"
MEM_PERCENT=$(free | awk 'NR==2 {printf "%.0f", $3*100/$2}')
if [ "$MEM_PERCENT" -lt 80 ]; then
    test_pass
    echo "    Used: ${MEM_PERCENT}%"
else
    test_warn "High memory usage: ${MEM_PERCENT}%"
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Verification Summary                                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}Passed:  $PASSED${NC}"
echo -e "  ${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "  ${RED}Failed:  $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment Verification: PASSED${NC}"
    echo ""
    echo "Your platform is ready for production!"
    echo ""
    echo "🌐 Access your site: https://$DOMAIN"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Deployment Verification: FAILED${NC}"
    echo ""
    echo "Please fix the failed checks before going live."
    echo "Check logs with: docker-compose logs"
    echo ""
    exit 1
fi
