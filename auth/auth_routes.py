"""Authentication routes."""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from auth.models import User, LoginAttempt
from auth.utils import hash_password, verify_password, validate_email, validate_password
import config

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    """Registration page."""
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('register.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Handle registration."""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()

        # Validate inputs
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        if not validate_email(email):
            return jsonify({'error': 'Please enter a valid email address'}), 400

        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400

        valid, message = validate_password(password)
        if not valid:
            return jsonify({'error': message}), 400

        # Check if email already exists
        existing_user = User.get_by_email(email)
        if existing_user:
            return jsonify({'error': 'An account with this email already exists'}), 400

        # Create user
        user = User(
            email=email,
            password_hash=hash_password(password),
            first_name=first_name if first_name else None,
            last_name=last_name if last_name else None,
            is_active=True,
            email_verified=False
        )
        user.save()

        # Auto-login user
        session['user_id'] = user.id
        session['user_email'] = user.email
        session.permanent = True

        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': user.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/login', methods=['GET'])
def login_page():
    """Login page."""
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle login."""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Check rate limiting
        ip_address = request.remote_addr
        failed_attempts_email = LoginAttempt.get_recent_failed_attempts(
            email, config.LOGIN_RATE_LIMIT_WINDOW
        )
        failed_attempts_ip = LoginAttempt.get_recent_failed_attempts_by_ip(
            ip_address, config.LOGIN_RATE_LIMIT_WINDOW
        )

        if failed_attempts_email >= config.MAX_LOGIN_ATTEMPTS:
            return jsonify({
                'error': 'Too many failed login attempts. Please try again in 15 minutes'
            }), 429

        if failed_attempts_ip >= config.MAX_LOGIN_ATTEMPTS * 2:
            return jsonify({
                'error': 'Too many failed login attempts from this IP. Please try again later'
            }), 429

        # Find user
        user = User.get_by_email(email)
        if not user or not verify_password(user.password_hash, password):
            LoginAttempt.log_attempt(email, ip_address, False)
            return jsonify({'error': 'Invalid email or password'}), 401

        # Check if account is active
        if not user.is_active:
            LoginAttempt.log_attempt(email, ip_address, False)
            return jsonify({
                'error': 'Your account has been deactivated. Please contact support'
            }), 403

        # Login successful
        LoginAttempt.log_attempt(email, ip_address, True)
        user.update_last_login()

        # Set session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session.permanent = remember_me

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name
            }
        }), 200

    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """Handle logout."""
    session.clear()
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/status', methods=['GET'])
def status():
    """Check authentication status."""
    if 'user_id' in session:
        user = User.get_by_id(session['user_id'])
        if user:
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name
                }
            })
    return jsonify({'authenticated': False}), 401
