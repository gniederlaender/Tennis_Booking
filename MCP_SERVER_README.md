# Tennis Booking MCP Server

## Overview

The Tennis Booking MCP Server is an adapter module that runs alongside the Flask application and provides Claude (via Model Context Protocol) with direct access to tennis court booking functionality. Claude can autonomously search for courts, make bookings, and find trainers through natural language requests.

## Architecture

```
User (Natural Language)
        ↓
   Claude Desktop
        ↓  MCP Protocol (stdio)
  mcp_server.py
        ↓  HTTP Requests (internal)
   Flask app.py (Port 5001)
        ↓
   scrapers_v2, booking, trainer_finder
```

## Features

The MCP server exposes three tools to Claude:

### 1. `search_courts` - Tennis Court Search
- **Purpose**: Search for available tennis courts by date and time
- **Authentication**: None required (anonymous access)
- **Parameters**:
  - `date` (required): Date in YYYY-MM-DD format
  - `time_from` (required): Start time in HH:MM format
  - `time_to` (optional): End time in HH:MM format
  - `location` (optional): Location filter ('arsenal' or 'postsv')
- **Output**: List of available courts with venue, court name, date, and time

### 2. `book_court` - Tennis Court Booking
- **Purpose**: Book a specific court for a logged-in user
- **Authentication**: Required - user must provide valid token
- **Parameters**:
  - `venue` (required): Venue name
  - `court_name` (required): Court name or number
  - `date` (required): Date in YYYY-MM-DD format
  - `time` (required): Time slot (e.g., '10:00-11:00')
  - `user_token` (required): Authentication token from logged-in user
- **Output**: Booking confirmation or error message
- **Note**: Claude will inform users if no token is provided and explain how to register/login

### 3. `find_trainers` - Trainer Search
- **Purpose**: Search for available tennis trainers
- **Authentication**: Service user (transparent to end user)
- **Parameters**:
  - `date` (optional): Date in YYYY-MM-DD format
  - `specialization` (optional): Specialization filter (e.g., 'Kinder', 'Erwachsene')
- **Output**: List of trainers with availability and contact information

## Installation

### 1. Install Dependencies

```bash
cd /opt/Tennis_Booking
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Edit `mcp_config.env` and set the service user token:

```bash
FLASK_API_BASE_URL=http://localhost:5001
MCP_SERVICE_USER_TOKEN=your_actual_service_token_here
MCP_SERVER_PORT=8001
```

To create a service user token:
1. Register a service account in the Tennis Booking app
2. Log in and extract the session token
3. Add the token to `mcp_config.env`

### 3. Install Systemd Service (Optional)

For production deployment with automatic restarts:

```bash
# Copy service file to systemd directory
sudo cp tennis-mcp.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable tennis-mcp

# Start the service
sudo systemctl start tennis-mcp

# Check status
sudo systemctl status tennis-mcp
```

### 4. Configure Claude Desktop

Add the following to your Claude Desktop configuration file:

**For stdio transport (recommended):**

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or equivalent on other platforms:

```json
{
  "mcpServers": {
    "tennis-booking": {
      "command": "/opt/Tennis_Booking/venv/bin/python",
      "args": ["/opt/Tennis_Booking/mcp_server.py"],
      "env": {
        "FLASK_API_BASE_URL": "http://localhost:5001",
        "MCP_SERVICE_USER_TOKEN": "your_service_token_here"
      }
    }
  }
}
```

**For SSH tunnel (remote server):**

If running on a remote server, create an SSH tunnel:

```bash
ssh -L 5001:localhost:5001 user@remote-server
```

Then use the same configuration above.

## Usage Examples

### Anonymous Court Search

User asks Claude:
> "Which tennis courts are available on Friday from 6pm?"

Claude will:
1. Call `search_courts` with appropriate date and time
2. Return formatted list of available courts

### Booking (Authenticated)

User asks Claude:
> "Book me a court at Arsenal on Saturday at 10am"

Claude will:
1. Check if user has provided a token
2. If no token: Inform user that authentication is required
3. If token present: Call `book_court` with the parameters
4. Return booking confirmation or error

### Trainer Search

User asks Claude:
> "Which trainers are available next week?"

Claude will:
1. Call `find_trainers` with appropriate date range
2. Return formatted list of trainers with availability

## Testing

### Manual Testing

Test the MCP server directly:

```bash
cd /opt/Tennis_Booking
source venv/bin/activate

# Set environment variables
export FLASK_API_BASE_URL=http://localhost:5001
export MCP_SERVICE_USER_TOKEN=your_token_here

# Run the server (it will wait for stdio input)
python mcp_server.py
```

### Integration Testing

1. Ensure Flask app is running on port 5001
2. Configure Claude Desktop with the MCP server
3. Restart Claude Desktop
4. Ask Claude to search for courts or trainers

## Troubleshooting

### MCP Server Not Appearing in Claude

1. Check Claude Desktop configuration file syntax
2. Verify the Python path and mcp_server.py path are correct
3. Check Claude Desktop logs for errors
4. Restart Claude Desktop

### Authentication Errors

1. Verify `MCP_SERVICE_USER_TOKEN` is set correctly
2. Check that the Flask app is running on the correct port
3. Verify the service user account is valid and not expired

### Connection Errors

1. Ensure Flask app is running: `curl http://localhost:5001/health`
2. Check firewall settings if using remote server
3. Verify SSH tunnel is active if connecting remotely

## Security Considerations

### Service User Token

- The `MCP_SERVICE_USER_TOKEN` is stored only on the server
- It is NEVER exposed to Claude or the end user
- Used only for endpoints that require authentication (search_courts, find_trainers)
- Rotate periodically for security

### User Tokens

- User tokens for `book_court` must be provided by the user
- Tokens should be short-lived session tokens
- Never log or store user tokens in the MCP server

### Network Security

- MCP server communicates only with localhost Flask app
- For production: Use SSH tunnel or VPN for remote access
- Do NOT expose port 8001 publicly
- Consider adding nginx reverse proxy with TLS for production

## Maintenance

### Logs

View MCP server logs:

```bash
# If using systemd
sudo journalctl -u tennis-mcp -f

# Or check Flask app logs
tail -f /opt/Tennis_Booking/logs/out.log
tail -f /opt/Tennis_Booking/logs/error.log
```

### Updates

When updating the MCP server:

```bash
# Edit mcp_server.py
vim /opt/Tennis_Booking/mcp_server.py

# Restart service
sudo systemctl restart tennis-mcp

# Restart Claude Desktop to pick up changes
```

### Monitoring

Monitor the service:

```bash
# Check service status
sudo systemctl status tennis-mcp

# Check if Flask app is responding
curl http://localhost:5001/health
```

## Development

### Adding New Tools

To add a new tool to the MCP server:

1. Add tool definition in `list_tools()` function
2. Create handler function (e.g., `async def handle_new_tool()`)
3. Add tool name to the dispatcher in `call_tool()`
4. Test thoroughly before deploying

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Use Python debugger:

```bash
python -m pdb mcp_server.py
```

## Reference

- [MCP Documentation](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/anthropics/python-sdk)
- [Claude Desktop Configuration](https://docs.anthropic.com/claude/docs/claude-desktop)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Flask app logs for API errors
3. Check Claude Desktop logs for MCP errors
4. Verify all dependencies are installed correctly
