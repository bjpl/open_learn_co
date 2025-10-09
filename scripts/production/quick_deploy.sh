#!/bin/bash
# ============================================================================
# OpenLearn Colombia - One-Command Deployment
# ============================================================================
# This script does EVERYTHING possible automatically
#
# What YOU need first:
# 1. Server with Ubuntu 22.04 (DigitalOcean, AWS, etc.)
# 2. Domain name (openlearn.co) pointing to server IP
# 3. SendGrid API key (from sendgrid.com)
#
# Then run THIS ONE COMMAND:
#   curl -sSL https://raw.githubusercontent.com/yourusername/open_learn/main/scripts/production/quick_deploy.sh | sudo bash
#
# Or if code already on server:
#   cd /opt/open_learn && sudo bash scripts/production/quick_deploy.sh
#
# ============================================================================

set -e

echo "🚀 OpenLearn Colombia - Automated Deployment"
echo "============================================"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root"
   echo "Run: sudo bash scripts/production/quick_deploy.sh"
   exit 1
fi

# Interactive setup (if .env doesn't exist)
if [ ! -f ".env" ]; then
    echo "📝 Initial Configuration"
    echo ""

    read -p "Enter your domain name (e.g., openlearn.co): " DOMAIN
    read -p "Enter your SendGrid API key (or press Enter to skip): " SENDGRID_KEY
    read -p "Enter admin email (default: admin@$DOMAIN): " ADMIN_EMAIL
    ADMIN_EMAIL=${ADMIN_EMAIL:-admin@$DOMAIN}

    echo ""
    echo "⚙️  Generating production .env file..."

    python3 scripts/generate_production_env.py $DOMAIN <<EOF
$SENDGRID_KEY
$ADMIN_EMAIL
EOF

    mv .env.production .env
    chmod 600 .env

    echo "✅ .env file created"
    echo ""
fi

# Run main deployment script
echo "🔧 Running automated deployment..."
echo ""

bash scripts/production/deploy.sh

# Run verification
echo ""
echo "🧪 Running deployment verification..."
echo ""

bash scripts/production/verify_deployment.sh

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  🎉 DEPLOYMENT COMPLETE!                                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Your OpenLearn Colombia platform is live!"
echo ""
DOMAIN=$(grep "^FRONTEND_URL=" .env | cut -d'=' -f2)
echo "🌐 Access at: $DOMAIN"
echo ""
echo "📋 Next steps:"
echo "   1. Open $DOMAIN in browser"
echo "   2. Create your first user account"
echo "   3. Test password reset email"
echo "   4. Set up UptimeRobot monitoring"
echo ""
echo "📊 Monitor your platform:"
echo "   - Logs: docker-compose logs -f"
echo "   - Health: $DOMAIN/health"
echo "   - API docs: $DOMAIN/docs"
echo ""
echo "Happy launching! 🚀"
echo ""
