#!/bin/bash
# Enable SSL/TLS for PostgreSQL
# Run this script on the database server

set -e

echo "Enabling PostgreSQL SSL/TLS..."

# Create SSL directory
sudo mkdir -p /var/lib/postgresql/ssl
cd /var/lib/postgresql/ssl

# Generate self-signed certificate (for testing)
# For production, use real certificates from CA
echo "Generating self-signed certificate..."
sudo openssl req -new -x509 -days 365 -nodes \
    -out server.crt \
    -keyout server.key \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=postgres.local"

# Generate CA certificate
sudo openssl req -new -x509 -days 3650 -nodes \
    -out ca.crt \
    -keyout ca.key \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=PostgreSQL CA"

# Set proper permissions
sudo chmod 600 server.key ca.key
sudo chmod 644 server.crt ca.crt
sudo chown postgres:postgres server.*  ca.*

echo "Updating PostgreSQL configuration..."
# Copy our config (or modify existing postgresql.conf)
sudo cp /path/to/postgresql.conf /etc/postgresql/15/main/postgresql.conf

# Update pg_hba.conf to require SSL
echo "Updating pg_hba.conf..."
sudo bash -c 'cat >> /etc/postgresql/15/main/pg_hba.conf <<EOF

# SSL/TLS Required Connections
hostssl all all 0.0.0.0/0 scram-sha-256
hostnossl all all 0.0.0.0/0 reject
EOF'

echo "Restarting PostgreSQL..."
sudo systemctl restart postgresql

echo "Testing SSL connection..."
psql "postgresql://postgres:password@localhost:5432/postgres?sslmode=require" -c "SELECT version();"

echo "✅ PostgreSQL SSL/TLS enabled!"
echo ""
echo "Connection string example:"
echo "DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require"
