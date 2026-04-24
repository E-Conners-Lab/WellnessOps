#!/bin/bash
# SSL certificate setup for WellnessOps
# Supports three modes: tailscale, letsencrypt, or self-signed

set -e

SSL_DIR="$(dirname "$0")/../docker/ssl"
mkdir -p "$SSL_DIR"

usage() {
    echo "Usage: $0 <mode> [options]"
    echo ""
    echo "Modes:"
    echo "  tailscale              Use Tailscale HTTPS certs (recommended for private access)"
    echo "  letsencrypt <domain>   Use Let's Encrypt (requires public domain + port 80)"
    echo "  selfsigned             Generate self-signed certs (development only)"
    echo ""
    echo "Examples:"
    echo "  $0 tailscale"
    echo "  $0 letsencrypt wellnessops.local"
    echo "  $0 selfsigned"
}

setup_tailscale() {
    echo "=== Tailscale SSL Setup ==="
    echo ""

    # Check if tailscale is installed
    if ! command -v tailscale &> /dev/null; then
        echo "ERROR: tailscale is not installed."
        echo "Install: https://tailscale.com/download"
        exit 1
    fi

    # Get Tailscale HTTPS cert
    HOSTNAME=$(tailscale status --json | python3 -c "import sys,json; print(json.load(sys.stdin)['Self']['DNSName'].rstrip('.'))" 2>/dev/null)

    if [ -z "$HOSTNAME" ]; then
        echo "ERROR: Could not determine Tailscale hostname. Is Tailscale running?"
        exit 1
    fi

    echo "Tailscale hostname: $HOSTNAME"
    echo "Requesting HTTPS certificate..."

    tailscale cert --cert-file "$SSL_DIR/cert.pem" --key-file "$SSL_DIR/key.pem" "$HOSTNAME"

    echo ""
    echo "SSL certificates written to $SSL_DIR/"
    echo "Your app will be available at: https://$HOSTNAME"
    echo ""
    echo "Note: Tailscale certs auto-renew. Re-run this script if they expire."
}

setup_letsencrypt() {
    DOMAIN="$1"
    if [ -z "$DOMAIN" ]; then
        echo "ERROR: Domain required for Let's Encrypt."
        echo "Usage: $0 letsencrypt your-domain.com"
        exit 1
    fi

    echo "=== Let's Encrypt SSL Setup ==="
    echo "Domain: $DOMAIN"
    echo ""

    # Check if certbot is available
    if ! command -v certbot &> /dev/null; then
        echo "Installing certbot via Docker..."
        # Use certbot Docker image
        docker run --rm -it \
            -v "$(pwd)/docker/ssl:/etc/letsencrypt/live/$DOMAIN" \
            -v "$(pwd)/docker/certbot-www:/var/www/certbot" \
            -p 80:80 \
            certbot/certbot certonly \
            --standalone \
            --preferred-challenges http \
            -d "$DOMAIN" \
            --agree-tos \
            --no-eff-email \
            --email "admin@$DOMAIN"

        # Copy certs to expected location
        cp "$(pwd)/docker/ssl/fullchain.pem" "$SSL_DIR/cert.pem"
        cp "$(pwd)/docker/ssl/privkey.pem" "$SSL_DIR/key.pem"
    else
        certbot certonly --standalone \
            --preferred-challenges http \
            -d "$DOMAIN" \
            --agree-tos \
            --no-eff-email

        cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$SSL_DIR/cert.pem"
        cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$SSL_DIR/key.pem"
    fi

    echo ""
    echo "SSL certificates written to $SSL_DIR/"
    echo "Your app will be available at: https://$DOMAIN"
    echo ""
    echo "Set up auto-renewal: certbot renew --quiet (add to crontab)"
}

setup_selfsigned() {
    echo "=== Self-Signed SSL Setup (Development Only) ==="
    echo ""

    openssl req -x509 -nodes -days 365 \
        -newkey rsa:2048 \
        -keyout "$SSL_DIR/key.pem" \
        -out "$SSL_DIR/cert.pem" \
        -subj "/C=US/ST=Tennessee/L=Nashville/O=WellnessOps/CN=localhost"

    echo ""
    echo "Self-signed certificates written to $SSL_DIR/"
    echo "Your browser will show a security warning -- this is expected for self-signed certs."
    echo "Access at: https://localhost"
}

# Main
case "${1:-}" in
    tailscale)
        setup_tailscale
        ;;
    letsencrypt)
        setup_letsencrypt "$2"
        ;;
    selfsigned)
        setup_selfsigned
        ;;
    *)
        usage
        exit 1
        ;;
esac

echo ""
echo "Next steps:"
echo "  1. Start the app: docker compose -f docker/docker-compose.yml up -d"
echo "  2. Open https://your-hostname in your browser"
