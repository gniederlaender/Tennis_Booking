#!/bin/bash
# Test script to verify chat routes are accessible

echo "=========================================="
echo "Tennis Booking - Chat Routes Test Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test localhost routes
echo "Testing LOCALHOST routes (should work)..."
echo "------------------------------------------"

echo -n "1. GET /chat: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/chat)
if [ "$STATUS" = "302" ] || [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ $STATUS (OK)${NC}"
else
    echo -e "${RED}✗ $STATUS (FAIL)${NC}"
fi

echo -n "2. POST /api/chat: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d '{"message":"test"}' http://localhost:5001/api/chat)
if [ "$STATUS" = "302" ] || [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ $STATUS (OK)${NC}"
else
    echo -e "${RED}✗ $STATUS (FAIL)${NC}"
fi

echo -n "3. POST /api/chat/clear: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "Content-Type: application/json" -d '{"session_id":"test"}' http://localhost:5001/api/chat/clear)
if [ "$STATUS" = "302" ] || [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ $STATUS (OK)${NC}"
else
    echo -e "${RED}✗ $STATUS (FAIL)${NC}"
fi

echo ""
echo "Testing OTHER routes (for comparison)..."
echo "------------------------------------------"

echo -n "4. GET / (index): "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/)
if [ "$STATUS" = "302" ] || [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ $STATUS (OK)${NC}"
else
    echo -e "${RED}✗ $STATUS (FAIL)${NC}"
fi

echo -n "5. GET /health: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/health)
if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ $STATUS (OK)${NC}"
else
    echo -e "${RED}✗ $STATUS (FAIL)${NC}"
fi

echo ""
echo "Checking PROXY configuration..."
echo "------------------------------------------"

# Check if nginx is running
if pgrep nginx > /dev/null; then
    echo -e "${YELLOW}✓ Nginx is running${NC}"
    echo "  Config locations to check:"
    echo "  - /etc/nginx/sites-enabled/"
    echo "  - /etc/nginx/conf.d/"
    echo ""
    echo "  Search for Tennis Booking config:"
    echo "  sudo grep -r 'localhost:5001' /etc/nginx/"
elif pgrep apache2 > /dev/null; then
    echo -e "${YELLOW}✓ Apache is running${NC}"
    echo "  Config locations to check:"
    echo "  - /etc/apache2/sites-enabled/"
    echo "  - /etc/apache2/conf.d/"
    echo ""
    echo "  Search for Tennis Booking config:"
    echo "  sudo grep -r 'localhost:5001' /etc/apache2/"
elif pgrep caddy > /dev/null; then
    echo -e "${YELLOW}✓ Caddy is running${NC}"
    echo "  Config location: /etc/caddy/Caddyfile"
else
    echo -e "${RED}✗ No common proxy detected (nginx/apache/caddy)${NC}"
fi

echo ""
echo "Application Status..."
echo "------------------------------------------"

# Check if app is running
if curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Application is running on localhost:5001${NC}"
    echo "  PM2 status:"
    pm2 list | grep tennis-booking
else
    echo -e "${RED}✗ Application not responding on localhost:5001${NC}"
fi

echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""
echo "If localhost routes work but external access fails:"
echo "1. The application is configured correctly"
echo "2. The proxy needs to be updated with new routes"
echo "3. See PROXY_FIX_CHAT_ROUTES.md for instructions"
echo ""
echo "If localhost routes fail:"
echo "1. Check if application is running: pm2 status"
echo "2. Restart if needed: pm2 restart tennis-booking"
echo "3. Check logs: tail -f /opt/Tennis_Booking/logs/error.log"
echo ""
