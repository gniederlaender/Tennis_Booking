"""Authentication decorators."""

from functools import wraps
from flask import session, redirect, url_for, request
from .models import User

def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Use relative path for 'next' parameter to work with reverse proxy
            return redirect(url_for('auth.login_page', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def current_user():
    """Get the currently logged in user."""
    user_id = session.get('user_id')
    if user_id:
        return User.get_by_id(user_id)
    return None
