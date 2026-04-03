#!/bin/bash
cd /opt/Tennis_Booking
exec /opt/Tennis_Booking/venv/bin/python /opt/Tennis_Booking/mcp_server.py 2>/tmp/mcp_debug.log
