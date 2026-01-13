#!/bin/bash
# Deploy authentication system updates

echo "==================================="
echo "Deploying Authentication System"
echo "==================================="
echo ""

# Check if database exists
if [ ! -f "tennis_booking.db" ]; then
    echo "Creating database..."
    python3 create_db.py
    echo ""
fi

# Install dependencies
echo "Installing dependencies..."
echo "This step requires running: venv/bin/pip install python-dotenv cryptography email-validator flask-login"
echo ""
echo "Please run manually:"
echo "  venv/bin/pip install python-dotenv cryptography email-validator flask-login"
echo "  pm2 restart tennis-booking"
echo ""
echo "Or run this script with sudo if it has permissions."
