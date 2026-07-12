"""Flask web application for Tennis Court Booking Finder."""

from flask import Flask, render_template, request, jsonify, g, session
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
from timeframe_parser import TimeframeParser
from scrapers_v2 import scrape_all_portals
from preference_engine import PreferenceEngine
from booking import book_court
from trainer_finder import find_trainers
from chat_engine import ChatEngine
import config
from database.db import init_db, close_db
from auth import auth_bp, login_required, current_user
from time_parser import time_parser_bp
from credential_manager import CredentialManager
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = config.SESSION_COOKIE_SECURE
app.config['SESSION_COOKIE_HTTPONLY'] = config.SESSION_COOKIE_HTTPONLY
app.config['SESSION_COOKIE_SAMESITE'] = config.SESSION_COOKIE_SAMESITE
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['PERMANENT_SESSION_LIFETIME'] = config.PERMANENT_SESSION_LIFETIME

# Configure app to work behind reverse proxy
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Register authentication blueprint
app.register_blueprint(auth_bp)

# Register time parser blueprint
app.register_blueprint(time_parser_bp)

# Register database teardown
app.teardown_appcontext(close_db)

@app.route('/')
def landing():
    """Landing page - public access."""
    # If user is logged in, redirect to search
    try:
        if current_user():
            return render_template('index.html')
    except:
        pass
    return render_template('landing.html')

@app.route('/api/dashboard/availability')
def dashboard_availability():
    """Get availability data for public dashboard - today only with booking trends."""
    try:
        from database.db import get_db
        from datetime import datetime
        db = get_db()
        cursor = db.cursor()

        # Get today's weekday (0=Monday, 6=Sunday)
        today = datetime.now()
        today_weekday = today.weekday()

        # Get the most recent snapshot timestamp for today
        cursor.execute('''
            SELECT MAX(captured_at) FROM availability_snapshots
            WHERE DATE(captured_at) = DATE('now', 'localtime')
        ''')
        latest_timestamp = cursor.fetchone()[0]

        if not latest_timestamp:
            return jsonify({
                'timestamp': None,
                'data': {},
                'message': 'No data available yet'
            })

        # Get latest snapshots for today's weekday only
        cursor.execute('''
            SELECT location, timeblock, available_slots
            FROM availability_snapshots
            WHERE DATE(captured_at) = DATE('now', 'localtime')
              AND weekday = ?
            ORDER BY captured_at DESC
        ''', (today_weekday,))

        snapshots = cursor.fetchall()

        # Get current availability (most recent per location/timeblock)
        current_data = {}
        seen = set()
        for location, timeblock, slots in snapshots:
            key = f"{location}_{timeblock}"
            if key not in seen:
                seen.add(key)
                if timeblock not in current_data:
                    current_data[timeblock] = {'arsenal': 0, 'postsv': 0, 'tc_gudrun': 0}
                current_data[timeblock][location] = slots

        # Get earliest morning snapshot for today to calculate "booked since morning"
        cursor.execute('''
            SELECT location, timeblock, available_slots, MIN(captured_at)
            FROM availability_snapshots
            WHERE DATE(captured_at) = DATE('now', 'localtime')
              AND weekday = ?
            GROUP BY location, timeblock
        ''', (today_weekday,))

        morning_snapshots = cursor.fetchall()
        morning_data = {}
        for location, timeblock, slots, _ in morning_snapshots:
            if timeblock not in morning_data:
                morning_data[timeblock] = {'arsenal': 0, 'postsv': 0, 'tc_gudrun': 0}
            morning_data[timeblock][location] = slots

        # Build response data for today only
        matrix = {}
        for timeblock in ['morning', 'midday', 'evening']:
            arsenal_current = current_data.get(timeblock, {}).get('arsenal', 0)
            postsv_current = current_data.get(timeblock, {}).get('postsv', 0)
            tc_gudrun_current = current_data.get(timeblock, {}).get('tc_gudrun', 0)
            total_current = arsenal_current + postsv_current + tc_gudrun_current

            arsenal_morning = morning_data.get(timeblock, {}).get('arsenal', 0)
            postsv_morning = morning_data.get(timeblock, {}).get('postsv', 0)
            tc_gudrun_morning = morning_data.get(timeblock, {}).get('tc_gudrun', 0)
            total_morning = arsenal_morning + postsv_morning + tc_gudrun_morning

            # Booked since morning = morning slots - current slots (positive = slots were booked)
            booked_since_morning = total_morning - total_current

            # Determine status
            if total_current >= 3:
                status = 'green'
            elif total_current >= 1:
                status = 'yellow'
            else:
                status = 'red'

            matrix[timeblock] = {
                'status': status,
                'total': total_current,
                'arsenal': arsenal_current,
                'postsv': postsv_current,
                'tc_gudrun': tc_gudrun_current,
                'booked_since_morning': max(0, booked_since_morning)
            }

        return jsonify({
            'timestamp': latest_timestamp,
            'weekday': today_weekday,
            'data': matrix
        })

    except Exception as e:
        logger.error(f"Dashboard availability error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/favorite-trainers-availability')
@login_required
def favorite_trainers_availability():
    """Get availability for user's favorite trainers for next 5 days."""
    try:
        user = current_user()
        from database.db import get_db
        from datetime import datetime, timedelta

        db = get_db()
        cursor = db.cursor()

        # Get user's favorite trainers
        cursor.execute('''
            SELECT favorite_trainer_1, favorite_trainer_2
            FROM users WHERE id = ?
        ''', (user.id,))
        row = cursor.fetchone()

        if not row or (not row[0] and not row[1]):
            return jsonify({'trainers': []})

        trainer_names = [t for t in [row[0], row[1]] if t]

        # Get trainer availability for next 5 days
        placeholders = ','.join(['?' for _ in trainer_names])
        cursor.execute(f'''
            SELECT trainer_name, date, time_start, time_end, price
            FROM trainer_availability_snapshots
            WHERE trainer_name IN ({placeholders})
              AND date >= date('now')
              AND date <= date('now', '+5 days')
              AND captured_at >= datetime('now', '-48 hours')
            ORDER BY trainer_name, date, time_start
        ''', trainer_names)

        rows = cursor.fetchall()

        # Organize by trainer → date → slots
        result = {}
        for trainer_name, date, time_start, time_end, price in rows:
            if trainer_name not in result:
                result[trainer_name] = {}
            if date not in result[trainer_name]:
                result[trainer_name][date] = []

            result[trainer_name][date].append({
                'time_start': time_start,
                'time_end': time_end,
                'price': price,
                'time_window': f"{time_start}-{time_end}"
            })

        # Convert to list format for frontend
        trainers_list = []
        for trainer_name, dates_dict in result.items():
            trainers_list.append({
                'name': trainer_name,
                'dates': dates_dict
            })

        return jsonify({'trainers': trainers_list})

    except Exception as e:
        logger.error(f"Favorite trainers availability error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/search-page')
@login_required
def index():
    """Main search page."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle search request."""
    try:
        timeframe = request.json.get('timeframe', '')
        search_mode = request.json.get('searchMode', 'court')  # 'court' or 'trainer'
        trainer_name = request.json.get('trainerName', None)
        locations = request.json.get('locations', {'arsenal': True, 'postsv': True})

        if not timeframe:
            return jsonify({'error': 'Please enter a timeframe'}), 400

        # Parse timeframe
        parser = TimeframeParser()
        parsed = parser.parse(timeframe)
        date = parsed['date']
        start_time = parsed['start_time']
        end_time = parsed['end_time']

        # Initialize response data
        response_data = {
            'success': True,
            'timeframe': {
                'date': date.strftime('%Y-%m-%d'),
                'day': date.strftime('%A'),
                'start': start_time,
                'end': end_time
            },
            'searchMode': search_mode
        }

        # Search based on mode: EITHER courts OR trainers
        if search_mode == 'trainer':
            # Search for trainers only
            logger.info("=" * 60)
            logger.info("TRAINER SEARCH: Starting trainer search...")
            logger.info("=" * 60)
            trainers = find_trainers(date, start_time, end_time, trainer_name)
            logger.info(f"TRAINER SEARCH: Found {len(trainers)} trainer slots")

            response_data['trainers'] = trainers
            response_data['slots'] = []
            response_data['total'] = len(trainers)
            response_data['preferred_index'] = None
        else:
            # Search for courts only (default)
            slots = scrape_all_portals(date, start_time, end_time, locations)

            # Get preferred slot if available
            pref_engine = PreferenceEngine()
            preferred = None
            if pref_engine.has_confidence() and slots:
                preferred_slot = pref_engine.get_preferred_slot(slots)
                if preferred_slot:
                    preferred = slots.index(preferred_slot)

            response_data['slots'] = slots[:50]  # Top 50
            response_data['total'] = len(slots)
            response_data['preferred_index'] = preferred

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/book', methods=['POST'])
@login_required
def book():
    """Handle booking request."""
    try:
        user = current_user()
        slot = request.json.get('slot', {})

        if not slot:
            return jsonify({'error': 'No slot data provided'}), 400

        # Validate required fields
        required_fields = ['venue', 'date', 'time', 'court_name']
        missing_fields = [f for f in required_fields if not slot.get(f)]
        if missing_fields:
            return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400

        # Attempt booking with user_id for credential manager
        success, message = book_court(slot, user_id=user.id)

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'booking': {
                    'venue': slot.get('venue'),
                    'court': slot.get('court_name'),
                    'date': slot.get('date'),
                    'time': slot.get('time')
                }
            })
        else:
            return jsonify({'error': message}), 400

    except Exception as e:
        return jsonify({'error': f'Booking error: {str(e)}'}), 500

@app.route('/chat')
@login_required
def chat_interface():
    """Conversational interface page."""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
@login_required
def chat_message():
    """Handle chat messages."""
    try:
        data = request.json
        message = data.get('message', '').strip()
        session_id = data.get('session_id')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Initialize chat engine
        chat_engine = ChatEngine()

        # Get or create session context
        if not session_id:
            session_id = str(uuid.uuid4())

        # Get context from Flask session (keyed by session_id)
        session_key = f'chat_context_{session_id}'
        context = session.get(session_key, {
            'state': 'IDLE',
            'last_results': [],
            'last_search': {},
            'conversation_history': []
        })

        # Process message
        response = chat_engine.process_message(message, context)

        # Add message to history
        response['context']['conversation_history'].append({
            'role': 'user',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        response['context']['conversation_history'].append({
            'role': 'assistant',
            'message': response['reply'],
            'timestamp': datetime.now().isoformat()
        })

        # Keep only last 20 messages
        if len(response['context']['conversation_history']) > 20:
            response['context']['conversation_history'] = response['context']['conversation_history'][-20:]

        # Save context back to session
        session[session_key] = response['context']
        session.modified = True

        # Return response
        return jsonify({
            'reply': response['reply'],
            'suggestions': response.get('suggestions', []),
            'session_id': session_id,
            'action': response.get('action'),
            'results_count': len(response.get('results', []))
        })

    except Exception as e:
        return jsonify({'error': f'Chat error: {str(e)}'}), 500

@app.route('/api/chat/clear', methods=['POST'])
@login_required
def clear_chat():
    """Clear chat session."""
    try:
        session_id = request.json.get('session_id')
        if session_id:
            session_key = f'chat_context_{session_id}'
            if session_key in session:
                del session[session_key]
                session.modified = True

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})

@app.route('/credentials')
@login_required
def credentials_page():
    """Credentials management page."""
    user = current_user()
    credential_mgr = CredentialManager()
    portals = credential_mgr.get_all_portals_status(user.id)

    # Enhance portals with health status
    from credential_validator import CredentialValidator
    validator = CredentialValidator()

    for portal in portals:
        health = validator.get_health_status(user.id, portal['portal_key'])
        if health:
            portal['health_status'] = health.get('status', 'untested')
            portal['last_verified_at'] = health.get('last_verified_at')
            portal['last_error_message'] = health.get('last_error_message')
        else:
            portal['health_status'] = 'untested'
            portal['last_verified_at'] = None
            portal['last_error_message'] = None

    return render_template('credentials.html', portals=portals)

@app.route('/credentials/save', methods=['POST'])
@login_required
def save_credentials():
    """Save portal credentials."""
    try:
        user = current_user()
        data = request.json
        portal_name = data.get('portal_name')
        username = data.get('username')
        password = data.get('password')

        if not all([portal_name, username, password]):
            return jsonify({'error': 'Alle Felder sind erforderlich'}), 400

        credential_mgr = CredentialManager()

        # Get old username for audit log
        old_creds = credential_mgr.get_credentials(user.id, portal_name)
        old_username = old_creds.get('username') if old_creds else None

        # Save credentials
        credential_mgr.save_credentials(user.id, portal_name, username, password)

        # Audit log
        from database.db import get_db
        db = get_db()
        cursor = db.cursor()

        # Get credential_id
        cursor.execute('''
            SELECT id FROM portal_credentials
            WHERE user_id = ? AND portal_name = ?
        ''', (user.id, portal_name))
        cred_row = cursor.fetchone()
        credential_id = cred_row[0] if cred_row else None

        # Log the change
        cursor.execute('''
            INSERT INTO credential_change_audit
            (credential_id, user_id, portal_name, action, username_before, username_after,
             ip_address, verification_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (credential_id, user.id, portal_name,
              'updated' if old_username else 'created',
              old_username, username,
              request.remote_addr, 'pending'))
        db.commit()

        return jsonify({'success': True, 'message': 'Zugangsdaten gespeichert'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Fehler beim Speichern: {str(e)}'}), 500

@app.route('/credentials/delete', methods=['POST'])
@login_required
def delete_credentials():
    """Delete portal credentials."""
    try:
        user = current_user()
        data = request.json
        portal_name = data.get('portal_name')

        if not portal_name:
            return jsonify({'error': 'Portal-Name erforderlich'}), 400

        credential_mgr = CredentialManager()
        credential_mgr.delete_credentials(user.id, portal_name)

        return jsonify({'success': True, 'message': 'Zugangsdaten gelöscht'})
    except Exception as e:
        return jsonify({'error': f'Fehler beim Löschen: {str(e)}'}), 500

@app.route('/api/credentials/verify/<portal_name>', methods=['POST'])
@login_required
def verify_portal_credentials(portal_name):
    """Manually verify portal credentials (Test Now button)."""
    try:
        user = current_user()

        if portal_name not in ['arsenal', 'postsv', 'tc_gudrun']:
            return jsonify({'error': 'Ungültiger Portal-Name'}), 400

        # Rate limiting: max 5 verification attempts per hour
        from database.db import get_db
        from datetime import datetime, timedelta
        db = get_db()
        cursor = db.cursor()

        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()

        cursor.execute('''
            SELECT COUNT(*) FROM credential_verification_log
            WHERE user_id = ? AND portal_name = ?
              AND verification_type = 'manual'
              AND verified_at > ?
        ''', (user.id, portal_name, one_hour_ago))

        count = cursor.fetchone()[0]

        if count >= 5:
            return jsonify({
                'error': 'Zu viele Verifikations-Versuche. Bitte versuche es in einer Stunde erneut.',
                'success': False,
                'status': 'rate_limited'
            }), 429

        credential_mgr = CredentialManager()
        success, message, status_dict = credential_mgr.verify_credentials(
            user.id, portal_name,
            verification_type='manual',
            triggered_by='user'
        )

        response_data = {
            'success': success,
            'message': message,
            'status': status_dict.get('status'),
            'response_time_ms': status_dict.get('response_time_ms'),
            'portal_name': portal_name
        }

        # Log the response for debugging
        app.logger.info(f"Verification API response for {portal_name}: {response_data}")

        return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"Verification API exception: {str(e)}")
        return jsonify({'error': f'Fehler bei der Verifikation: {str(e)}'}), 500

@app.route('/api/credentials/update_and_verify', methods=['POST'])
@login_required
def update_and_verify_credentials():
    """Update credentials and verify them before saving (Guided Update Workflow)."""
    try:
        user = current_user()
        data = request.json
        portal_name = data.get('portal_name')
        username = data.get('username')
        password = data.get('password')

        if not all([portal_name, username, password]):
            return jsonify({'error': 'Alle Felder sind erforderlich'}), 400

        if portal_name not in ['arsenal', 'postsv', 'tc_gudrun']:
            return jsonify({'error': 'Ungültiger Portal-Name'}), 400

        credential_mgr = CredentialManager()

        # First, save credentials (they will be encrypted)
        credential_mgr.save_credentials(user.id, portal_name, username, password)

        # Then verify them
        success, message, status_dict = credential_mgr.verify_credentials(
            user.id, portal_name,
            verification_type='post_update',
            triggered_by='user'
        )

        if not success and status_dict.get('status') == 'failed':
            # Credentials failed verification
            # Note: We don't rollback the save - user can fix it later
            return jsonify({
                'success': False,
                'message': f'Zugangsdaten gespeichert, aber Verifikation fehlgeschlagen: {message}',
                'status': status_dict.get('status'),
                'verified': False
            }), 200

        return jsonify({
            'success': True,
            'message': f'Zugangsdaten gespeichert und erfolgreich verifiziert!',
            'status': status_dict.get('status'),
            'response_time_ms': status_dict.get('response_time_ms'),
            'verified': True
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Fehler beim Speichern: {str(e)}'}), 500

@app.route('/api/credentials/health/<portal_name>', methods=['GET'])
@login_required
def get_credential_health(portal_name):
    """Get health status for a specific portal's credentials."""
    try:
        user = current_user()

        if portal_name not in ['arsenal', 'postsv', 'tc_gudrun']:
            return jsonify({'error': 'Ungültiger Portal-Name'}), 400

        from credential_validator import CredentialValidator
        validator = CredentialValidator()

        health_status = validator.get_health_status(user.id, portal_name)

        if not health_status:
            return jsonify({
                'portal_name': portal_name,
                'status': 'untested',
                'message': 'Noch nicht getestet'
            })

        return jsonify({
            'portal_name': portal_name,
            'status': health_status.get('status'),
            'last_verified_at': health_status.get('last_verified_at'),
            'last_success_at': health_status.get('last_success_at'),
            'consecutive_failures': health_status.get('consecutive_failures'),
            'last_error_message': health_status.get('last_error_message'),
            'username': health_status.get('username')
        })

    except Exception as e:
        return jsonify({'error': f'Fehler beim Abrufen: {str(e)}'}), 500

@app.route('/profile')
@login_required
def profile():
    """User profile and newsletter settings page."""
    user = current_user()
    from database.db import get_db
    db = get_db()
    cursor = db.cursor()

    # Get newsletter settings and credential alert settings
    cursor.execute('''
        SELECT newsletter_active, newsletter_weekday, newsletter_timeblock,
               favorite_trainer_1, favorite_trainer_2,
               credential_alerts_enabled, credential_alert_mode
        FROM users WHERE id = ?
    ''', (user.id,))
    row = cursor.fetchone()

    newsletter_settings = {
        'active': bool(row[0]) if row and row[0] is not None else False,
        'weekday': row[1] if row and row[1] is not None else 4,  # Default Friday
        'timeblock': row[2] if row and row[2] else 'evening'  # Default evening
    }

    favorite_trainers = {
        'trainer1': row[3] if row and row[3] else None,
        'trainer2': row[4] if row and row[4] else None
    }

    # Credential alert settings (with defaults if NULL)
    credential_alert_settings = {
        'enabled': bool(row[5]) if row and row[5] is not None else True,  # Default enabled
        'mode': row[6] if row and row[6] else 'immediate'  # Default immediate
    }

    # Get list of all trainers from database (not just currently available ones)
    # This ensures favorite trainers remain in the dropdown even on days without availability
    cursor.execute('''
        SELECT DISTINCT trainer_name
        FROM trainer_availability_snapshots
        ORDER BY trainer_name
    ''')
    available_trainers = [row[0] for row in cursor.fetchall()]

    return render_template('profile.html',
                         user=user,
                         newsletter=newsletter_settings,
                         favorite_trainers=favorite_trainers,
                         available_trainers=available_trainers,
                         credential_alerts=credential_alert_settings)

@app.route('/profile/newsletter', methods=['POST'])
@login_required
def update_newsletter_settings():
    """Update newsletter preferences."""
    try:
        user = current_user()
        data = request.json

        newsletter_active = data.get('active', False)
        newsletter_weekday = data.get('weekday')
        newsletter_timeblock = data.get('timeblock')

        # Validate inputs
        if newsletter_active:
            if newsletter_weekday is None or not (0 <= newsletter_weekday <= 6):
                return jsonify({'error': 'Ungültiger Wochentag'}), 400
            if newsletter_timeblock not in ['morning', 'midday', 'evening']:
                return jsonify({'error': 'Ungültige Tageszeit'}), 400

        from database.db import get_db
        db = get_db()
        cursor = db.cursor()

        cursor.execute('''
            UPDATE users
            SET newsletter_active = ?,
                newsletter_weekday = ?,
                newsletter_timeblock = ?
            WHERE id = ?
        ''', (newsletter_active, newsletter_weekday, newsletter_timeblock, user.id))

        db.commit()

        return jsonify({'success': True, 'message': 'Newsletter-Einstellungen gespeichert'})

    except Exception as e:
        logger.error(f"Newsletter settings error: {e}")
        return jsonify({'error': f'Fehler beim Speichern: {str(e)}'}), 500

@app.route('/profile/trainers', methods=['POST'])
@login_required
def update_favorite_trainers():
    """Update favorite trainer preferences."""
    try:
        user = current_user()
        data = request.json

        favorite_trainer_1 = data.get('favoriteTrainer1', None)
        favorite_trainer_2 = data.get('favoriteTrainer2', None)

        # Empty string should be treated as None
        if favorite_trainer_1 == '':
            favorite_trainer_1 = None
        if favorite_trainer_2 == '':
            favorite_trainer_2 = None

        # Validate: trainers should be different
        if favorite_trainer_1 and favorite_trainer_2 and favorite_trainer_1 == favorite_trainer_2:
            return jsonify({'error': 'Bitte wähle zwei verschiedene Trainer aus'}), 400

        from database.db import get_db
        db = get_db()
        cursor = db.cursor()

        cursor.execute('''
            UPDATE users
            SET favorite_trainer_1 = ?,
                favorite_trainer_2 = ?
            WHERE id = ?
        ''', (favorite_trainer_1, favorite_trainer_2, user.id))

        db.commit()

        return jsonify({'success': True, 'message': 'Lieblings-Trainer gespeichert'})

    except Exception as e:
        logger.error(f"Favorite trainers update error: {e}")
        return jsonify({'error': f'Fehler beim Speichern: {str(e)}'}), 500

@app.route('/profile/credential-alerts', methods=['POST'])
@login_required
def update_credential_alert_settings():
    """Update credential alert preferences."""
    try:
        user = current_user()
        data = request.json

        alerts_enabled = data.get('enabled', True)
        alert_mode = data.get('mode', 'immediate')

        # Validate mode
        if alert_mode not in ['immediate', 'daily_digest', 'disabled']:
            return jsonify({'error': 'Ungültiger Benachrichtigungsmodus'}), 400

        from database.db import get_db
        db = get_db()
        cursor = db.cursor()

        cursor.execute('''
            UPDATE users
            SET credential_alerts_enabled = ?,
                credential_alert_mode = ?
            WHERE id = ?
        ''', (alerts_enabled, alert_mode, user.id))

        db.commit()

        return jsonify({'success': True, 'message': 'Benachrichtigungseinstellungen gespeichert'})

    except Exception as e:
        logger.error(f"Credential alert settings update error: {e}")
        return jsonify({'error': f'Fehler beim Speichern: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
