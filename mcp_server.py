"""MCP Server for Tennis Booking Finder (HTTP/SSE Transport).

This module provides a Model Context Protocol (MCP) server that allows Claude
to interact with the Tennis Booking Finder application. It exposes three tools:
- search_courts: Search for available tennis courts
- book_court: Book a tennis court (requires authentication)
- find_trainers: Find available tennis trainers

Runs as an HTTP server with SSE transport for easy deployment.
Users simply add the URL to their Claude Desktop config.
"""

import asyncio
import os
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import uvicorn
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from mcp.types import (
    Tool,
    TextContent,
)

# Configuration
FLASK_API_BASE_URL = os.getenv("FLASK_API_BASE_URL", "http://localhost:5001")
MCP_SERVICE_USER_TOKEN = os.getenv("MCP_SERVICE_USER_TOKEN", "")
MCP_API_KEY = os.getenv("MCP_API_KEY", "")  # Optional API key for authentication
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8765"))

# Initialize MCP server
mcp = Server("tennis-booking")


def format_court_slots(slots: List[Dict]) -> str:
    """Format court slots for display to Claude."""
    if not slots:
        return "No available courts found."

    result = []
    result.append(f"Found {len(slots)} available court(s):\n")

    for i, slot in enumerate(slots, 1):
        venue = slot.get('venue', 'Unknown')
        court = slot.get('court_name', 'Unknown')
        date = slot.get('date', 'Unknown')
        time = slot.get('time', 'Unknown')

        result.append(f"{i}. {venue} - {court}")
        result.append(f"   Date: {date}")
        result.append(f"   Time: {time}")
        result.append("")

    return "\n".join(result)


def format_trainers(trainers: List[Dict]) -> str:
    """Format trainer information for display to Claude."""
    if not trainers:
        return "No trainers found."

    result = []
    result.append(f"Found {len(trainers)} available trainer(s):\n")

    for i, trainer in enumerate(trainers, 1):
        name = trainer.get('name', 'Unknown')
        availability = trainer.get('availability', 'Unknown')
        date = trainer.get('date', 'Unknown')
        time = trainer.get('time', 'Unknown')

        result.append(f"{i}. {name}")
        result.append(f"   Date: {date}")
        result.append(f"   Time: {time}")
        result.append(f"   Status: {availability}")
        result.append("")

    return "\n".join(result)


@mcp.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for Claude."""
    return [
        Tool(
            name="search_courts",
            description=(
                "Search for available tennis courts by date and time. "
                "This tool does NOT require authentication and can be used by anyone. "
                "Returns a list of available courts with venue, court name, date, and time."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format (e.g., '2026-03-29')",
                    },
                    "time_from": {
                        "type": "string",
                        "description": "Start time in HH:MM format (e.g., '10:00')",
                    },
                    "time_to": {
                        "type": "string",
                        "description": "End time in HH:MM format (optional, e.g., '12:00')",
                    },
                    "location": {
                        "type": "string",
                        "description": "Optional location filter (e.g., 'arsenal', 'postsv')",
                    },
                },
                "required": ["date", "time_from"],
            },
        ),
        Tool(
            name="book_court",
            description=(
                "Book a tennis court for a specific date and time. "
                "IMPORTANT: This tool REQUIRES an authenticated user with a valid token. "
                "If no user_token is provided, you MUST inform the user that an account "
                "is required to make bookings and do NOT call this tool. "
                "The user needs to register or log in to get a token."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "venue": {
                        "type": "string",
                        "description": "Venue name (e.g., 'Das Spiel', 'Post SV')",
                    },
                    "court_name": {
                        "type": "string",
                        "description": "Court name or number (e.g., 'Platz 1')",
                    },
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                    },
                    "time": {
                        "type": "string",
                        "description": "Time slot (e.g., '10:00-11:00')",
                    },
                    "user_token": {
                        "type": "string",
                        "description": "Authentication token from logged-in user (required)",
                    },
                },
                "required": ["venue", "court_name", "date", "time", "user_token"],
            },
        ),
        Tool(
            name="find_trainers",
            description=(
                "Search for available tennis trainers. "
                "This tool uses a service account internally and does NOT require "
                "user authentication. It can be used by anyone to browse trainer availability."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Optional date in YYYY-MM-DD format to search for specific date",
                    },
                    "specialization": {
                        "type": "string",
                        "description": "Optional specialization (e.g., 'Kinder', 'Erwachsene')",
                    },
                },
                "required": [],
            },
        ),
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls from Claude."""

    if name == "search_courts":
        return await handle_search_courts(arguments)
    elif name == "book_court":
        return await handle_book_court(arguments)
    elif name == "find_trainers":
        return await handle_find_trainers(arguments)
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def handle_search_courts(args: Dict[str, Any]) -> List[TextContent]:
    """Handle court search requests."""
    date = args.get("date")
    time_from = args.get("time_from")
    time_to = args.get("time_to", "21:00")
    location = args.get("location")

    # Build timeframe string for the Flask API
    # Parser expects format: "2026-03-30 10:00-12:00" (hyphen, no "from/to")
    timeframe = f"{date} {time_from}-{time_to}"

    # Prepare locations filter
    locations = {"arsenal": True, "postsv": True}
    if location:
        location_lower = location.lower()
        if "arsenal" in location_lower or "dasspiel" in location_lower:
            locations = {"arsenal": True, "postsv": False}
        elif "postsv" in location_lower or "post sv" in location_lower:
            locations = {"arsenal": False, "postsv": True}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {}
            if MCP_SERVICE_USER_TOKEN:
                headers["Authorization"] = f"Bearer {MCP_SERVICE_USER_TOKEN}"

            response = await client.post(
                f"{FLASK_API_BASE_URL}/search",
                json={
                    "timeframe": timeframe,
                    "searchMode": "court",
                    "locations": locations,
                },
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                slots = data.get("slots", [])
                formatted = format_court_slots(slots)
                return [TextContent(type="text", text=formatted)]
            else:
                error_msg = f"Search failed: {response.status_code} - {response.text}"
                return [TextContent(type="text", text=error_msg)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error searching courts: {str(e)}")]


async def handle_book_court(args: Dict[str, Any]) -> List[TextContent]:
    """Handle court booking requests."""
    venue = args.get("venue")
    court_name = args.get("court_name")
    date = args.get("date")
    time = args.get("time")
    user_token = args.get("user_token")

    if not user_token:
        return [TextContent(
            type="text",
            text=(
                "Authentication required!\n\n"
                "To book a tennis court, you need to be logged in with a valid account. "
                "Please register or log in to the Tennis Booking Finder application "
                "to get an authentication token.\n\n"
                "After logging in, provide your token when calling this tool."
            )
        )]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{FLASK_API_BASE_URL}/book",
                json={
                    "slot": {
                        "venue": venue,
                        "court_name": court_name,
                        "date": date,
                        "time": time,
                    }
                },
                headers={"Authorization": f"Bearer {user_token}"},
            )

            if response.status_code == 200:
                data = response.json()
                success_msg = (
                    f"Booking successful!\n\n"
                    f"Venue: {venue}\n"
                    f"Court: {court_name}\n"
                    f"Date: {date}\n"
                    f"Time: {time}\n\n"
                    f"{data.get('message', '')}"
                )
                return [TextContent(type="text", text=success_msg)]
            else:
                error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                error_msg = error_data.get("error", response.text)
                return [TextContent(
                    type="text",
                    text=f"Booking failed: {error_msg}"
                )]

    except Exception as e:
        return [TextContent(type="text", text=f"Error booking court: {str(e)}")]


async def handle_find_trainers(args: Dict[str, Any]) -> List[TextContent]:
    """Handle trainer search requests."""
    date = args.get("date")
    specialization = args.get("specialization")

    # Build timeframe string - if no date provided, use "this week"
    if date:
        timeframe = f"{date} all day"
    else:
        timeframe = "this week"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {}
            if MCP_SERVICE_USER_TOKEN:
                headers["Authorization"] = f"Bearer {MCP_SERVICE_USER_TOKEN}"

            response = await client.post(
                f"{FLASK_API_BASE_URL}/search",
                json={
                    "timeframe": timeframe,
                    "searchMode": "trainer",
                    "trainerName": specialization,
                },
                headers=headers,
            )

            if response.status_code == 200:
                data = response.json()
                trainers = data.get("trainers", [])
                formatted = format_trainers(trainers)
                return [TextContent(type="text", text=formatted)]
            else:
                error_msg = f"Trainer search failed: {response.status_code} - {response.text}"
                return [TextContent(type="text", text=error_msg)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error searching trainers: {str(e)}")]


# --- HTTP/SSE Server Setup ---

def check_api_key(request: Request) -> bool:
    """Check if API key is valid (if configured)."""
    if not MCP_API_KEY:
        return True  # No API key configured, allow all

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        provided_key = auth_header[7:]
        return secrets.compare_digest(provided_key, MCP_API_KEY)
    return False


async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "server": "tennis-booking-mcp",
        "version": "1.0.0",
        "transport": "sse"
    })


# Create SSE transport with /mcp prefix for reverse proxy
MCP_PATH_PREFIX = os.getenv("MCP_PATH_PREFIX", "/mcp")
sse = SseServerTransport(f"{MCP_PATH_PREFIX}/messages/")


async def handle_sse(request: Request) -> Response:
    """Handle SSE connections from MCP clients."""
    # Check API key if configured
    if MCP_API_KEY and not check_api_key(request):
        return JSONResponse(
            {"error": "Unauthorized - Invalid or missing API key"},
            status_code=401
        )

    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp.run(
            streams[0],
            streams[1],
            mcp.create_initialization_options()
        )
    return Response()


async def handle_messages(request: Request) -> Response:
    """Handle POST messages from MCP clients."""
    # Check API key if configured
    if MCP_API_KEY and not check_api_key(request):
        return JSONResponse(
            {"error": "Unauthorized - Invalid or missing API key"},
            status_code=401
        )

    await sse.handle_post_message(request.scope, request.receive, request._send)
    return Response()


# Create Starlette app with CORS middleware
app = Starlette(
    debug=False,
    routes=[
        Route("/health", health_check, methods=["GET"]),
        Route("/sse", handle_sse, methods=["GET"]),
        Route("/messages/", handle_messages, methods=["POST"]),
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]
)


def main():
    """Main entry point for the MCP server."""
    print(f"Starting Tennis Booking MCP Server on port {MCP_SERVER_PORT}")
    print(f"SSE endpoint: http://0.0.0.0:{MCP_SERVER_PORT}/sse")
    print(f"Health check: http://0.0.0.0:{MCP_SERVER_PORT}/health")
    if MCP_API_KEY:
        print("API key authentication: ENABLED")
    else:
        print("API key authentication: DISABLED (open access)")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=MCP_SERVER_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()
