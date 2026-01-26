# Proxy Configuration Fix: Chat Routes 404 Error

**Date:** January 26, 2026
**Issue:** Chat endpoint returning 404 with "API endpoint not found" error
**Root Cause:** Reverse proxy not configured to forward new chat routes

---

## Problem Description

When accessing the chat interface through the external domain/proxy, the following error occurs:

```json
{
    "success": false,
    "error": {
        "code": "NOT_FOUND",
        "message": "API endpoint not found"
    }
}
```

### What Works

✅ Direct localhost access to all endpoints:
- `http://localhost:5001/chat` - Returns 302 redirect (expected)
- `http://localhost:5001/api/chat` - Returns 302 redirect (expected)
- `http://localhost:5001/api/chat/clear` - Works

✅ Application routes are properly defined in `app.py`:
- Line 144: `@app.route('/chat')`
- Line 150: `@app.route('/api/chat', methods=['POST'])`
- Line 213: `@app.route('/api/chat/clear', methods=['POST'])`

### What Doesn't Work

❌ External proxy/domain access returns structured 404 error
❌ The error format suggests an API gateway or reverse proxy is intercepting requests

---

## Root Cause Analysis

### Timeline of New Routes

1. **Commit 1490da9** (Jan 24): Conversational interface added
   - New routes: `/chat`, `/api/chat`, `/api/chat/clear`
   - Routes work on localhost
   - Not yet configured in external proxy

2. **Current State**: Application serves routes correctly on port 5001
   - Gunicorn binding: `0.0.0.0:5001`
   - All routes accessible via localhost
   - External access blocked by proxy configuration

### Why This Happens

The Tennis Booking application is deployed behind a reverse proxy (nginx, Apache, or API gateway). When new routes are added to the Flask application, the proxy configuration also needs to be updated to:

1. **Forward the new paths** to the backend application
2. **Preserve the path** when proxying requests
3. **Handle WebSocket connections** (if chat features expand)

The structured JSON error response suggests the proxy has a custom 404 handler that returns:
```json
{"success": false, "error": {"code": "NOT_FOUND", "message": "API endpoint not found"}}
```

This is not coming from Flask/Gunicorn (which returns HTML 404 pages), confirming it's the proxy layer.

---

## Solution: Proxy Configuration Update

### Option 1: Nginx Configuration

If using nginx as reverse proxy, update the configuration file (typically in `/etc/nginx/sites-available/` or `/etc/nginx/conf.d/`):

**Find the existing configuration:**
```bash
# Common locations:
ls /etc/nginx/sites-enabled/
ls /etc/nginx/conf.d/
grep -r "tennis" /etc/nginx/
grep -r "5001" /etc/nginx/
```

**Add chat routes to the location blocks:**

```nginx
# Existing configuration probably looks like:
location / {
    proxy_pass http://localhost:5001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Ensure these specific routes are included (if using path-based routing):
location /chat {
    proxy_pass http://localhost:5001/chat;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /api/chat {
    proxy_pass http://localhost:5001/api/chat;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Content-Type application/json;
}
```

**Test and reload nginx:**
```bash
# Test configuration
sudo nginx -t

# Reload if test passes
sudo systemctl reload nginx
# or
sudo nginx -s reload
```

### Option 2: Apache Configuration

If using Apache as reverse proxy (`.htaccess` or `httpd.conf`):

```apache
# Existing configuration
ProxyPass / http://localhost:5001/
ProxyPassReverse / http://localhost:5001/

# Add specific routes
ProxyPass /chat http://localhost:5001/chat
ProxyPassReverse /chat http://localhost:5001/chat

ProxyPass /api/chat http://localhost:5001/api/chat
ProxyPassReverse /api/chat http://localhost:5001/api/chat
```

**Reload Apache:**
```bash
sudo systemctl reload apache2
# or
sudo apachectl graceful
```

### Option 3: Caddy Configuration

If using Caddy, update the `Caddyfile`:

```caddy
yourdomain.com {
    reverse_proxy localhost:5001
    # Caddy automatically handles all routes if using wildcard
}
```

Caddy typically doesn't need route-specific configuration.

**Reload Caddy:**
```bash
sudo systemctl reload caddy
```

### Option 4: API Gateway / Cloud Proxy

If using a cloud API gateway (AWS API Gateway, Google Cloud Endpoints, etc.):

1. Add new route definitions:
   - `GET /chat` → Forward to backend
   - `POST /api/chat` → Forward to backend
   - `POST /api/chat/clear` → Forward to backend

2. Ensure path forwarding is enabled
3. Update CORS settings if needed
4. Deploy gateway configuration

---

## Verification Steps

After updating proxy configuration:

### 1. Test Chat Page Access
```bash
# Should redirect to login (302) or show chat page if authenticated
curl -I https://yourdomain.com/chat
```

### 2. Test API Endpoint
```bash
# Should redirect to login (302) or require authentication
curl -X POST https://yourdomain.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"test"}'
```

### 3. Browser Test
1. Open browser
2. Navigate to `https://yourdomain.com/chat`
3. Should either:
   - Redirect to login page
   - Show chat interface (if already logged in)
4. Try sending a message
5. Should receive response from chat engine

### 4. Check Logs
```bash
# Application logs should show requests
tail -f /opt/Tennis_Booking/logs/out.log

# Proxy logs should show successful forwards
# Nginx: tail -f /var/log/nginx/access.log
# Apache: tail -f /var/log/apache2/access.log
```

---

## Application is Already Configured Correctly

The Flask application has proper proxy support configured in `app.py`:

```python
# Configure app to work behind reverse proxy
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)
```

This means the application correctly:
- ✓ Handles `X-Forwarded-For` headers
- ✓ Handles `X-Forwarded-Proto` headers
- ✓ Handles `X-Forwarded-Host` headers
- ✓ Handles path prefix forwarding

**No changes needed in the application code.**

---

## Troubleshooting

### Issue: Still getting 404 after proxy update

**Check:**
1. Proxy configuration syntax is correct
2. Proxy was actually reloaded (not just tested)
3. Correct proxy is being used (might have multiple)
4. DNS/routing points to the right proxy
5. Firewall rules allow traffic

**Debug:**
```bash
# Check if proxy is listening
sudo netstat -tlnp | grep nginx  # or apache2

# Check proxy error logs
tail -f /var/log/nginx/error.log
tail -f /var/log/apache2/error.log

# Test direct backend
curl http://localhost:5001/chat
```

### Issue: CORS errors in browser console

**Fix:** Add CORS headers in proxy:

```nginx
# Nginx
add_header Access-Control-Allow-Origin *;
add_header Access-Control-Allow-Methods "POST, GET, OPTIONS";
add_header Access-Control-Allow-Headers "Content-Type";
```

### Issue: WebSocket errors (future-proofing)

If chat features expand to use WebSockets:

```nginx
# Nginx WebSocket support
location /api/chat {
    proxy_pass http://localhost:5001/api/chat;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

## Quick Diagnosis Commands

**To identify the proxy in use:**
```bash
# Check what's listening on ports 80/443
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443

# Check for nginx
ps aux | grep nginx
sudo nginx -v

# Check for Apache
ps aux | grep apache
apache2 -v

# Check for Caddy
ps aux | grep caddy
caddy version
```

**To find configuration files:**
```bash
# Nginx
find /etc/nginx -name "*.conf" -type f
grep -r "localhost:5001" /etc/nginx/

# Apache
find /etc/apache2 -name "*.conf" -type f
grep -r "localhost:5001" /etc/apache2/

# Caddy
find /etc/caddy -name "Caddyfile"
```

---

## Prevention for Future Route Additions

When adding new routes to the application:

1. **Document in CHANGELOG**: List new routes added
2. **Update proxy config**: Before deploying
3. **Test locally first**: Verify route works on localhost
4. **Test through proxy**: Verify external access
5. **Update API documentation**: If routes are API endpoints

### Deployment Checklist

- [ ] New route added in `app.py`
- [ ] Route tested on localhost
- [ ] Proxy configuration updated
- [ ] Proxy reloaded/restarted
- [ ] External access tested
- [ ] Logs checked for errors
- [ ] Documentation updated

---

## Summary

**The Problem:** New chat routes (`/chat`, `/api/chat`, `/api/chat/clear`) return 404 when accessed through external proxy.

**The Cause:** Proxy configuration hasn't been updated to forward these new routes to the backend application.

**The Solution:** Update the reverse proxy configuration to include the new routes, then reload the proxy.

**Action Required:** Update proxy configuration file (nginx, Apache, or other) and reload the service.

---

## Files Referenced

- `app.py` - Application with routes (lines 144, 150, 213)
- `templates/chat.html` - Frontend making API calls (line 336)
- `ecosystem.config.js` - PM2 configuration
- External proxy config (location varies by setup)

---

**Status:** ⚠️ REQUIRES EXTERNAL PROXY CONFIGURATION UPDATE

The application is correctly configured and serving all routes on localhost:5001. The proxy configuration needs to be updated to forward the new chat-related paths.
