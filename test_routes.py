#!/usr/bin/env python3
"""Test that all routes are registered properly."""

from app import app

def test_routes():
    """Check if chat_interface route is registered."""
    print("Checking registered routes...")
    print("=" * 60)

    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'})),
            'path': str(rule)
        })

    # Sort by path
    routes.sort(key=lambda x: x['path'])

    # Print all routes
    for route in routes:
        print(f"{route['path']:30} -> {route['endpoint']:30} [{route['methods']}]")

    print("\n" + "=" * 60)

    # Check if chat_interface exists
    chat_routes = [r for r in routes if 'chat' in r['endpoint']]
    if chat_routes:
        print("✓ Chat routes found:")
        for route in chat_routes:
            print(f"  {route['endpoint']}: {route['path']}")
    else:
        print("✗ No chat routes found!")

    print("=" * 60)

if __name__ == '__main__':
    test_routes()
