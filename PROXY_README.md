# Reverse Proxy Configuration - Quick Reference

This directory contains Apache reverse proxy configuration for the Tennis Booking application.

## Quick Start

```bash
# For Apache (automated setup)
sudo bash /opt/Tennis_Booking/setup_apache_proxy.sh
```

## Files

1. **`apache-tennis-booking.conf`** - Apache virtual host configuration
2. **`setup_apache_proxy.sh`** - Automated installation script
3. **`APACHE_PROXY_SETUP.md`** - Complete Apache documentation
4. **`PROXY_FIX_CHAT_ROUTES.md`** - Generic proxy troubleshooting guide

## What It Does

- Forwards all HTTP requests to Flask app on port 5001
- Configures proper headers for reverse proxy
- Explicitly includes new chat routes (`/chat`, `/api/chat`)
- Sets up logging and security headers
- Ready for HTTPS configuration

## Verification

```bash
# Test backend
curl http://localhost:5001/health

# Test proxy (after setup)
curl http://localhost/health

# Check logs
sudo tail -f /var/log/apache2/tennis-booking-access.log
```

## Documentation

- **For Apache users**: See `APACHE_PROXY_SETUP.md`
- **For nginx/Caddy users**: See `PROXY_FIX_CHAT_ROUTES.md`
- **Troubleshooting**: Both documents include troubleshooting sections

## Status

✅ Configuration files created and ready
✅ Setup script tested and documented
✅ Automated installation available

Run the setup script to configure Apache reverse proxy.
