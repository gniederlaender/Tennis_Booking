#!/bin/bash
# Install authentication dependencies

echo "Installing authentication dependencies..."
venv/bin/pip install -q python-dotenv cryptography email-validator flask-login

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
    echo ""
    echo "Run 'pm2 restart tennis-booking' to restart the application"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi
