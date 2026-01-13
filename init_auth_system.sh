#!/bin/bash
# Initialize the authentication system

echo "Initializing authentication system..."

# Install dependencies
echo ""
echo "1. Installing dependencies..."
venv/bin/pip install -q python-dotenv cryptography email-validator flask-login

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

# Initialize database
echo ""
echo "2. Initializing database..."
venv/bin/python database/db.py

if [ $? -eq 0 ]; then
    echo "✓ Database initialized"
else
    echo "✗ Failed to initialize database"
    exit 1
fi

echo ""
echo "✓ Authentication system initialized successfully!"
echo ""
echo "Next steps:"
echo "1. Start the application: pm2 restart tennis-booking"
echo "2. Visit http://localhost:5001/auth/register to create an account"
echo "3. Login and start using the application"
