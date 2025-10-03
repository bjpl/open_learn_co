#!/bin/bash
# SSL Certificate Setup with Let's Encrypt
# Usage: ./setup_ssl.sh yourdomain.com

set -e

DOMAIN=$1
EMAIL=${2:-admin@$DOMAIN}

if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <domain> [email]"
    echo "Example: $0 example.com admin@example.com"
    exit 1
fi

echo "Setting up SSL for: $DOMAIN"
echo "Contact email: $EMAIL"

# Install Certbot
if ! command -v certbot &> /dev/null; then
    echo "Installing Certbot..."
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
fi

# Option 1: Standalone (if no web server running)
echo "Obtaining certificate (standalone mode)..."
sudo certbot certonly --standalone \
    -d $DOMAIN \
    -d www.$DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --staple-ocsp \
    --preferred-challenges http

# Option 2: If using Nginx (uncomment below, comment above)
# sudo certbot --nginx \
#     -d $DOMAIN \
#     -d www.$DOMAIN \
#     --email $EMAIL \
#     --agree-tos \
#     --no-eff-email

# Copy certificates to Docker volume
echo "Copying certificates..."
sudo mkdir -p ./infrastructure/nginx/ssl
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ./infrastructure/nginx/ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ./infrastructure/nginx/ssl/
sudo chmod 644 ./infrastructure/nginx/ssl/*.pem

# Set up auto-renewal
echo "Setting up auto-renewal..."
sudo certbot renew --dry-run

# Add to crontab if not exists
(crontab -l 2>/dev/null | grep -q certbot) || \
    (crontab -l 2>/dev/null; echo "0 0,12 * * * certbot renew --quiet --deploy-hook 'docker-compose restart nginx'") | crontab -

echo "✅ SSL certificates installed!"
echo "Certificates location: ./infrastructure/nginx/ssl/"
echo "Auto-renewal scheduled: Twice daily check"
echo ""
echo "Next steps:"
echo "1. Update nginx.conf to use SSL"
echo "2. Restart nginx: docker-compose restart nginx"
echo "3. Test: https://$DOMAIN"
