#!/bin/bash
# Setup script for Apache reverse proxy configuration
# Run with: sudo bash setup_apache_proxy.sh

set -e

echo "=========================================="
echo "Tennis Booking - Apache Proxy Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Check if Apache is installed
if ! command -v apache2 &> /dev/null; then
    echo "ERROR: Apache2 is not installed"
    echo "Install with: sudo apt-get install apache2"
    exit 1
fi

echo "✓ Apache2 is installed"
echo ""

# Enable required Apache modules
echo "Enabling required Apache modules..."
a2enmod proxy
a2enmod proxy_http
a2enmod headers
a2enmod rewrite

echo "✓ Required modules enabled"
echo ""

# Copy configuration file
CONFIG_SOURCE="/opt/Tennis_Booking/apache-tennis-booking.conf"
CONFIG_DEST="/etc/apache2/sites-available/tennis-booking.conf"

if [ ! -f "$CONFIG_SOURCE" ]; then
    echo "ERROR: Configuration file not found at $CONFIG_SOURCE"
    exit 1
fi

echo "Copying configuration file..."
cp "$CONFIG_SOURCE" "$CONFIG_DEST"
echo "✓ Configuration copied to $CONFIG_DEST"
echo ""

# Test configuration
echo "Testing Apache configuration..."
if apache2ctl configtest 2>&1 | grep -q "Syntax OK"; then
    echo "✓ Apache configuration syntax is valid"
else
    echo "WARNING: Apache configuration test showed warnings (might be OK)"
    apache2ctl configtest
fi
echo ""

# Enable the site
echo "Enabling Tennis Booking site..."
a2ensite tennis-booking.conf
echo "✓ Site enabled"
echo ""

# Option to disable default site
read -p "Disable Apache default site? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    a2dissite 000-default.conf
    echo "✓ Default site disabled"
fi
echo ""

# Reload Apache
echo "Reloading Apache..."
systemctl reload apache2
echo "✓ Apache reloaded"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Configuration file: $CONFIG_DEST"
echo "Application: http://localhost (proxied to localhost:5001)"
echo ""
echo "Next steps:"
echo "1. Update ServerName in $CONFIG_DEST if needed"
echo "2. Configure DNS/hosts file if using custom domain"
echo "3. Test access: curl http://localhost/health"
echo "4. For HTTPS, uncomment the SSL section and configure certificates"
echo ""
echo "Logs:"
echo "- Error log: /var/log/apache2/tennis-booking-error.log"
echo "- Access log: /var/log/apache2/tennis-booking-access.log"
echo ""
