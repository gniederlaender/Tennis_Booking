"""Authentication decorators."""

from functools import wraps
from flask import session, redirect, url_for, request

def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Use relative path for 'next' parameter to work with reverse proxy
            return redirect(url_for('auth.login_page', next=request.path))
        return f(*args, **kwargs)
    return decorated_function
