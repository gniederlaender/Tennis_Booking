"""Authentication package for Tennis Court Booking application."""

from .auth_routes import auth_bp
from .decorators import login_required

__all__ = ['auth_bp', 'login_required']
