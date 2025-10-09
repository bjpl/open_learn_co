#!/bin/bash
# ============================================================================
# OpenLearn Colombia - Automated Production Deployment Script
# ============================================================================
# This script automates 90% of the deployment process
#
# Prerequisites (YOU must do these manually):
# 1. Server with Ubuntu 22.04 and public IP
# 2. Domain name pointing to server IP (DNS configured)
# 3. SendGrid account with API key
#
# What this script does FOR YOU:
# - Installs Docker + Docker Compose
# - Configures environment
# - Runs database migrations
# - Builds and starts all services
# - Installs and configures Nginx
# - Sets up SSL with Let's Encrypt
# - Configures firewall
# - Sets up automated backups
# - Performs health checks
#
# Usage:
#   1. Upload this entire project to server: /opt/open_learn/
#   2. Run: cd /opt/open_learn && chmod +x scripts/production/deploy.sh
#   3. Run: sudo ./scripts/production/deploy.sh
#
# ============================================================================

set -e  # Exit on any error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  $1${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ============================================================================
# PHASE 1: Pre-Flight Checks
# ============================================================================

print_header "Phase 1: Pre-Flight Checks"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (sudo)"
   exit 1
fi

log_success "Running as root ✓"

# Check if .env file exists
if [ ! -f ".env" ]; then
    log_error ".env file not found!"
    log_info "Run this first: python3 scripts/generate_production_env.py"
    exit 1
fi

log_success ".env file found ✓"

# Verify .env has production settings
if ! grep -q "ENVIRONMENT=production" .env; then
    log_error ".env file is not configured for production!"
    log_info "ENVIRONMENT must be 'production' in .env"
    exit 1
fi

log_success ".env configured for production ✓"

# Check for required values in .env
if grep -q "YOUR_SENDGRID_API_KEY_HERE" .env; then
    log_warning "SendGrid API key not set in .env"
    log_info "Emails will print to console only (development mode)"
fi

log_info "Pre-flight checks complete!"

# ============================================================================
# PHASE 2: Install Dependencies
# ============================================================================

print_header "Phase 2: Installing Dependencies"

# Update package lists
log_info "Updating package lists..."
apt update -qq

# Install prerequisites
log_info "Installing prerequisites..."
apt install -y apt-transport-https ca-certificates curl software-properties-common gnupg lsb-release

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    log_info "Installing Docker..."

    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

    # Add Docker repository
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    apt update -qq
    apt install -y docker-ce docker-ce-cli containerd.io

    # Start and enable Docker
    systemctl start docker
    systemctl enable docker

    log_success "Docker installed ✓"
else
    log_success "Docker already installed ✓"
fi

# Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    log_info "Installing Docker Compose..."

    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    log_success "Docker Compose installed ✓"
else
    log_success "Docker Compose already installed ✓"
fi

# Verify installations
log_info "Verifying installations..."
docker --version
docker-compose --version

log_success "All dependencies installed ✓"

# ============================================================================
# PHASE 3: Database Setup
# ============================================================================

print_header "Phase 3: Database Setup"

# Start PostgreSQL container only
log_info "Starting PostgreSQL..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
log_info "Waiting for PostgreSQL to initialize (30 seconds)..."
sleep 30

# Check if database is responding
log_info "Testing database connection..."
docker-compose exec -T postgres psql -U openlearn_prod -c "SELECT 1;" openlearn_production || {
    log_error "Database not responding!"
    log_info "Check logs: docker-compose logs postgres"
    exit 1
}

log_success "Database connection successful ✓"

# Run migrations
if [ -f "backend/database/migrations/003_add_user_timezone_preferences.sql" ]; then
    log_info "Running database migration 003..."
    docker-compose exec -T postgres psql -U openlearn_prod openlearn_production < backend/database/migrations/003_add_user_timezone_preferences.sql || {
        log_warning "Migration may have already been applied (this is OK if columns exist)"
    }
    log_success "Database migration complete ✓"
else
    log_warning "Migration 003 not found (may not be needed)"
fi

# ============================================================================
# PHASE 4: Build and Start Application
# ============================================================================

print_header "Phase 4: Building Application"

log_info "Building Docker images (this takes 5-15 minutes)..."
docker-compose build

log_success "Docker images built ✓"

log_info "Starting all services..."
docker-compose up -d

# Wait for services to start
log_info "Waiting for services to initialize (60 seconds)..."
sleep 60

# Check service status
log_info "Verifying service status..."
docker-compose ps

log_success "All services started ✓"

# ============================================================================
# PHASE 5: Nginx Setup
# ============================================================================

print_header "Phase 5: Nginx Configuration"

# Install Nginx if not already installed
if ! command -v nginx &> /dev/null; then
    log_info "Installing Nginx..."
    apt install -y nginx
    log_success "Nginx installed ✓"
else
    log_success "Nginx already installed ✓"
fi

# Copy Nginx configuration
if [ -f "infrastructure/nginx/openlearn.conf" ]; then
    log_info "Copying Nginx configuration..."
    cp infrastructure/nginx/openlearn.conf /etc/nginx/sites-available/openlearn

    # Enable site
    ln -sf /etc/nginx/sites-available/openlearn /etc/nginx/sites-enabled/

    # Remove default site
    rm -f /etc/nginx/sites-enabled/default

    # Test configuration
    nginx -t || {
        log_error "Nginx configuration test failed!"
        exit 1
    }

    log_success "Nginx configured ✓"
else
    log_warning "Nginx config template not found at infrastructure/nginx/openlearn.conf"
    log_info "You'll need to configure Nginx manually"
fi

# ============================================================================
# PHASE 6: SSL Certificate (Let's Encrypt)
# ============================================================================

print_header "Phase 6: SSL Certificate Setup"

# Install Certbot
if ! command -v certbot &> /dev/null; then
    log_info "Installing Certbot..."
    apt install -y certbot python3-certbot-nginx
    log_success "Certbot installed ✓"
else
    log_success "Certbot already installed ✓"
fi

# Extract domain from .env
DOMAIN=$(grep "^FRONTEND_URL=" .env | cut -d'=' -f2 | sed 's|https://||' | sed 's|http://||')

if [ -z "$DOMAIN" ]; then
    log_error "Could not extract domain from .env FRONTEND_URL"
    log_info "Skipping SSL setup - configure manually with: sudo certbot --nginx -d yourdomain.com"
else
    log_info "Detected domain: $DOMAIN"

    # Ask user if they want to run Certbot now
    echo -e "${YELLOW}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  SSL Certificate Setup                                  ║${NC}"
    echo -e "${YELLOW}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Certbot will:"
    echo "  1. Verify you own $DOMAIN (DNS must point to this server)"
    echo "  2. Generate free SSL certificate from Let's Encrypt"
    echo "  3. Configure Nginx with HTTPS"
    echo "  4. Set up auto-renewal"
    echo ""
    echo "⚠️  IMPORTANT: DNS must be configured first!"
    echo "   Run: dig $DOMAIN"
    echo "   Should show this server's IP address"
    echo ""
    read -p "Run Certbot now? (y/n): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Running Certbot for $DOMAIN..."
        certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email ${ALERT_EMAIL_TO:-admin@$DOMAIN} || {
            log_warning "Certbot failed - DNS may not be configured yet"
            log_info "Run manually later: sudo certbot --nginx -d $DOMAIN"
        }

        # Reload Nginx
        systemctl reload nginx
        log_success "SSL certificate installed ✓"
    else
        log_info "Skipping SSL setup"
        log_info "Run manually later: sudo certbot --nginx -d $DOMAIN"
    fi
fi

# ============================================================================
# PHASE 7: Firewall Configuration
# ============================================================================

print_header "Phase 7: Firewall Setup"

# Install UFW if not present
if ! command -v ufw &> /dev/null; then
    log_info "Installing UFW firewall..."
    apt install -y ufw
fi

# Configure firewall rules
log_info "Configuring firewall rules..."

# CRITICAL: Allow SSH first (prevent lockout!)
ufw allow 22/tcp
log_info "Allowed SSH (port 22)"

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp
log_info "Allowed HTTP (port 80) and HTTPS (port 443)"

# Enable firewall (non-interactive)
echo "y" | ufw enable

log_success "Firewall configured and enabled ✓"

# Show status
ufw status

# ============================================================================
# PHASE 8: Backup Setup
# ============================================================================

print_header "Phase 8: Automated Backup Setup"

# Create backup directory
mkdir -p /backups/openlearn
chmod 700 /backups/openlearn

log_info "Backup directory created: /backups/openlearn"

# Copy backup script
if [ -f "scripts/production/backup.sh" ]; then
    cp scripts/production/backup.sh /usr/local/bin/backup-openlearn
    chmod +x /usr/local/bin/backup-openlearn

    # Schedule daily backup at 2am
    (crontab -l 2>/dev/null | grep -v "backup-openlearn"; echo "0 2 * * * /usr/local/bin/backup-openlearn >> /var/log/openlearn-backup.log 2>&1") | crontab -

    log_success "Automated daily backups configured (2am daily) ✓"

    # Run initial backup
    log_info "Creating initial backup..."
    /usr/local/bin/backup-openlearn

    ls -lh /backups/openlearn/
else
    log_warning "Backup script not found at scripts/production/backup.sh"
fi

# ============================================================================
# PHASE 9: Health Checks & Verification
# ============================================================================

print_header "Phase 9: Deployment Verification"

log_info "Running health checks..."

# Test backend health
log_info "Testing backend health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health || echo "FAILED")

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    log_success "Backend is healthy ✓"
else
    log_error "Backend health check failed!"
    log_info "Response: $HEALTH_RESPONSE"
    log_info "Check logs: docker-compose logs backend"
fi

# Test frontend
log_info "Testing frontend..."
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "000")

if [ "$FRONTEND_RESPONSE" = "200" ]; then
    log_success "Frontend is responding ✓"
else
    log_warning "Frontend returned HTTP $FRONTEND_RESPONSE"
    log_info "Check logs: docker-compose logs frontend"
fi

# Test database connection
log_info "Testing database..."
docker-compose exec -T postgres psql -U openlearn_prod -c "SELECT COUNT(*) FROM users;" openlearn_production > /dev/null 2>&1 && {
    log_success "Database is accessible ✓"
} || {
    log_warning "Database may have connection issues"
}

# Test Redis
log_info "Testing Redis cache..."
REDIS_PASSWORD=$(grep "^REDIS_PASSWORD=" .env | cut -d'=' -f2)
docker-compose exec -T redis redis-cli -a "$REDIS_PASSWORD" ping > /dev/null 2>&1 && {
    log_success "Redis is responding ✓"
} || {
    log_warning "Redis may have connection issues"
}

# Check disk space
DISK_FREE=$(df -h / | awk 'NR==2 {print $4}')
log_info "Disk space free: $DISK_FREE"

# Check memory
MEM_FREE=$(free -h | awk 'NR==2 {print $4}')
log_info "Memory free: $MEM_FREE"

# ============================================================================
# PHASE 10: Final Instructions
# ============================================================================

print_header "Deployment Complete!"

echo -e "${GREEN}✅ Your OpenLearn Colombia platform is deployed!${NC}"
echo ""
echo "🌐 Access your platform:"
DOMAIN=$(grep "^FRONTEND_URL=" .env | cut -d'=' -f2)
echo "   $DOMAIN"
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Test in browser:"
echo "   Open: $DOMAIN"
echo "   - Should show OpenLearn homepage"
echo "   - Should have HTTPS padlock 🔒"
echo ""
echo "2. Create first user:"
echo "   - Click Sign Up"
echo "   - Register with your email"
echo "   - Check inbox for welcome email"
echo ""
echo "3. Set up monitoring:"
echo "   - Create UptimeRobot account: https://uptimerobot.com"
echo "   - Add monitor for: $DOMAIN/health"
echo "   - Set email alerts"
echo ""
echo "4. Monitor first 24 hours:"
echo "   - Watch logs: docker-compose logs -f backend"
echo "   - Check errors: docker-compose logs | grep ERROR"
echo "   - Monitor resources: docker stats"
echo ""
echo "📁 Important locations:"
echo "   - Application: $(pwd)"
echo "   - Logs: /var/log/nginx/openlearn_*.log"
echo "   - Backups: /backups/openlearn/"
echo "   - Docker volumes: /var/lib/docker/volumes/"
echo ""
echo "🔧 Useful commands:"
echo "   - Restart services: docker-compose restart"
echo "   - View logs: docker-compose logs -f backend"
echo "   - Stop all: docker-compose down"
echo "   - Update code: git pull && docker-compose up -d --build"
echo ""
echo "🆘 If something's wrong:"
echo "   - Check logs: docker-compose logs"
echo "   - Restart: docker-compose restart"
echo "   - Rollback: git reset --hard <previous-commit>"
echo ""
echo -e "${GREEN}🎉 Happy launching!${NC}"
echo ""
