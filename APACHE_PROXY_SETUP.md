# Apache Reverse Proxy Setup for Tennis Booking

**Date:** January 26, 2026
**Status:** Ready for Deployment
**Purpose:** Configure Apache as reverse proxy for Flask application

---

## Overview

This document describes the Apache reverse proxy configuration for the Tennis Booking application. The configuration forwards all HTTP requests from Apache (port 80/443) to the Flask application running on `localhost:5001`.

---

## Files Created

1. **`apache-tennis-booking.conf`** - Apache virtual host configuration
2. **`setup_apache_proxy.sh`** - Automated setup script
3. **`APACHE_PROXY_SETUP.md`** - This documentation

---

## Quick Setup

### Automated Setup (Recommended)

```bash
# Run the setup script
sudo bash /opt/Tennis_Booking/setup_apache_proxy.sh
```

This script will:
- ✓ Enable required Apache modules (proxy, proxy_http, headers, rewrite)
- ✓ Copy configuration to `/etc/apache2/sites-available/`
- ✓ Test Apache configuration syntax
- ✓ Enable the Tennis Booking site
- ✓ Optionally disable default site
- ✓ Reload Apache to apply changes

### Manual Setup

If you prefer manual setup:

```bash
# 1. Enable required modules
sudo a2enmod proxy proxy_http headers rewrite

# 2. Copy configuration
sudo cp /opt/Tennis_Booking/apache-tennis-booking.conf \
        /etc/apache2/sites-available/tennis-booking.conf

# 3. Enable the site
sudo a2ensite tennis-booking.conf

# 4. (Optional) Disable default site
sudo a2dissite 000-default.conf

# 5. Test configuration
sudo apache2ctl configtest

# 6. Reload Apache
sudo systemctl reload apache2
```

---

## Configuration Details

### What the Configuration Does

1. **Reverse Proxy**: Forwards all requests from Apache to Flask app on port 5001
2. **Header Forwarding**: Sets X-Forwarded-* headers for proper proxy handling
3. **Chat Routes**: Explicitly includes `/chat` and `/api/chat` routes
4. **Security Headers**: Adds security headers (X-Frame-Options, etc.)
5. **Logging**: Separate log files for Tennis Booking app
6. **Timeouts**: Sets 120-second timeout for long-running requests

### Routes Configured

All routes are proxied, including:
- `/` - Main application index
- `/auth/login` - Authentication routes
- `/search` - Search functionality
- `/book` - Booking functionality
- `/chat` - Chat interface (NEW)
- `/api/chat` - Chat API endpoint (NEW)
- `/api/chat/clear` - Clear chat session (NEW)
- `/health` - Health check endpoint

### Key Configuration Lines

```apache
ProxyPreserveHost On          # Preserve original Host header
ProxyRequests Off             # Disable forward proxy
ProxyTimeout 120              # 120 second timeout

# Forward all requests
ProxyPass / http://localhost:5001/
ProxyPassReverse / http://localhost:5001/
```

---

## Verification

### 1. Check Apache Status

```bash
sudo systemctl status apache2
```

Should show "active (running)".

### 2. Check Configuration

```bash
# Test syntax
sudo apache2ctl configtest

# List enabled sites
ls -l /etc/apache2/sites-enabled/

# View configuration
cat /etc/apache2/sites-enabled/tennis-booking.conf
```

### 3. Test Routes

```bash
# Health check
curl http://localhost/health
# Expected: {"status":"healthy"}

# Chat page (should redirect to login)
curl -I http://localhost/chat
# Expected: HTTP/1.1 302 Found

# API endpoint (should redirect to login)
curl -I -X POST http://localhost/api/chat
# Expected: HTTP/1.1 302 Found
```

### 4. Check Logs

```bash
# Real-time monitoring
sudo tail -f /var/log/apache2/tennis-booking-access.log
sudo tail -f /var/log/apache2/tennis-booking-error.log

# Check recent errors
sudo tail -50 /var/log/apache2/tennis-booking-error.log
```

---

## Troubleshooting

### Issue: Apache won't start

**Symptoms:**
- `systemctl reload apache2` fails
- Configuration test fails

**Solutions:**

1. Check syntax:
   ```bash
   sudo apache2ctl configtest
   ```

2. Check if modules are enabled:
   ```bash
   apache2ctl -M | grep proxy
   ```
   Should show: `proxy_module`, `proxy_http_module`

3. Check port conflicts:
   ```bash
   sudo netstat -tlnp | grep :80
   ```

4. View Apache error log:
   ```bash
   sudo tail -50 /var/log/apache2/error.log
   ```

### Issue: 404 errors on chat routes

**Symptoms:**
- `/chat` returns 404
- `/api/chat` returns 404

**Solutions:**

1. Verify proxy is forwarding:
   ```bash
   curl -v http://localhost/chat
   # Check X-Forwarded headers in output
   ```

2. Test backend directly:
   ```bash
   curl http://localhost:5001/chat
   # Should work and redirect to login
   ```

3. Check Apache access log:
   ```bash
   sudo tail -f /var/log/apache2/tennis-booking-access.log
   # Make request and see if it appears
   ```

### Issue: Backend not responding

**Symptoms:**
- Apache works but gets 502/504 errors
- "Connection refused" in logs

**Solutions:**

1. Check if Flask app is running:
   ```bash
   pm2 status tennis-booking
   curl http://localhost:5001/health
   ```

2. Restart Flask app if needed:
   ```bash
   pm2 restart tennis-booking
   ```

3. Check Flask logs:
   ```bash
   tail -f /opt/Tennis_Booking/logs/error.log
   ```

### Issue: Slow responses

**Symptoms:**
- Requests timeout
- 504 Gateway Timeout errors

**Solutions:**

1. Increase ProxyTimeout in config:
   ```apache
   ProxyTimeout 300  # 5 minutes
   ```

2. Check Flask app performance:
   ```bash
   tail -f /opt/Tennis_Booking/logs/out.log
   ```

---

## HTTPS Configuration

To enable HTTPS (recommended for production):

### 1. Obtain SSL Certificate

```bash
# Using Let's Encrypt (recommended)
sudo apt-get install certbot python3-certbot-apache
sudo certbot --apache -d your-domain.com
```

### 2. Or Manual Certificate

If you have existing certificates, edit the configuration file and uncomment the HTTPS section:

```apache
<VirtualHost *:443>
    ServerName your-domain.com

    SSLEngine on
    SSLCertificateFile /path/to/certificate.crt
    SSLCertificateKeyFile /path/to/private.key
    SSLCertificateChainFile /path/to/chain.crt

    # ... rest of proxy configuration
</VirtualHost>
```

### 3. Enable SSL Module

```bash
sudo a2enmod ssl
sudo systemctl reload apache2
```

---

## Custom Domain Configuration

To use a custom domain (e.g., tennis.example.com):

### 1. Update Apache Configuration

Edit `/etc/apache2/sites-available/tennis-booking.conf`:

```apache
ServerName tennis.example.com
ServerAlias www.tennis.example.com
```

### 2. Update DNS

Point your domain to the server's IP address:

```
A Record: tennis.example.com → YOUR_SERVER_IP
```

### 3. Reload Apache

```bash
sudo systemctl reload apache2
```

---

## Maintenance

### Viewing Logs

```bash
# Access logs
sudo tail -f /var/log/apache2/tennis-booking-access.log

# Error logs
sudo tail -f /var/log/apache2/tennis-booking-error.log

# Both logs
sudo tail -f /var/log/apache2/tennis-booking-*.log
```

### Log Rotation

Apache automatically rotates logs daily. Old logs are compressed and stored:
- `/var/log/apache2/tennis-booking-access.log.1`
- `/var/log/apache2/tennis-booking-access.log.2.gz`
- etc.

### Disabling the Proxy

If you need to temporarily disable:

```bash
# Disable site
sudo a2dissite tennis-booking.conf

# Reload Apache
sudo systemctl reload apache2

# Re-enable later
sudo a2ensite tennis-booking.conf
sudo systemctl reload apache2
```

---

## Performance Tuning

For high-traffic scenarios:

### 1. Enable KeepAlive

In Apache main config (`/etc/apache2/apache2.conf`):

```apache
KeepAlive On
MaxKeepAliveRequests 100
KeepAliveTimeout 5
```

### 2. Adjust Worker Settings

In `/etc/apache2/mods-available/mpm_prefork.conf`:

```apache
<IfModule mpm_prefork_module>
    StartServers          5
    MinSpareServers       5
    MaxSpareServers      10
    MaxRequestWorkers   150
    MaxConnectionsPerChild   0
</IfModule>
```

### 3. Enable Compression

```bash
sudo a2enmod deflate
```

Add to virtual host:

```apache
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css application/json
</IfModule>
```

---

## Security Best Practices

### 1. Restrict Access (if internal only)

```apache
<Proxy *>
    Order deny,allow
    Deny from all
    Allow from 192.168.1.0/24  # Your internal network
    Allow from localhost
</Proxy>
```

### 2. Rate Limiting

Install and configure mod_evasive:

```bash
sudo apt-get install libapache2-mod-evasive
sudo a2enmod evasive
```

### 3. Hide Apache Version

In `/etc/apache2/conf-available/security.conf`:

```apache
ServerTokens Prod
ServerSignature Off
```

---

## Integration with Flask Application

The Flask application is already configured to work behind a proxy:

**In `app.py`:**
```python
from werkzeug.middleware.proxy_fix import ProxyFix

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)
```

This ensures Flask correctly handles:
- `X-Forwarded-For` - Client IP address
- `X-Forwarded-Proto` - Original protocol (http/https)
- `X-Forwarded-Host` - Original host header
- `X-Forwarded-Prefix` - URL prefix if any

**No application changes needed!**

---

## Rollback Procedure

If you need to revert the proxy setup:

```bash
# 1. Disable the site
sudo a2dissite tennis-booking.conf

# 2. Re-enable default site (if disabled)
sudo a2ensite 000-default.conf

# 3. Reload Apache
sudo systemctl reload apache2

# 4. (Optional) Remove configuration
sudo rm /etc/apache2/sites-available/tennis-booking.conf
```

The application will still be accessible directly on port 5001.

---

## Summary

**What was configured:**
- ✅ Apache reverse proxy on port 80
- ✅ All routes forwarded to Flask app (port 5001)
- ✅ Chat routes explicitly included
- ✅ Security headers configured
- ✅ Logging configured
- ✅ HTTPS template ready

**How to use:**
1. Run setup script: `sudo bash setup_apache_proxy.sh`
2. Test: `curl http://localhost/health`
3. Access via browser: `http://your-server-ip/`

**Key files:**
- Config: `/etc/apache2/sites-available/tennis-booking.conf`
- Logs: `/var/log/apache2/tennis-booking-*.log`
- App: Running on `localhost:5001` (unchanged)

**Status:** Ready for deployment ✅

---

## Support

For issues:
1. Check logs: `/var/log/apache2/tennis-booking-*.log`
2. Test backend: `curl http://localhost:5001/health`
3. Test proxy: `curl http://localhost/health`
4. Review this documentation
5. Check `PROXY_FIX_CHAT_ROUTES.md` for troubleshooting

---

**Last Updated:** January 26, 2026
**Maintained By:** Tennis Booking Team
