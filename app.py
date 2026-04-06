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
    """Get availability data for public dashboard."""
    try:
        from database.db import get_db
        db = get_db()
        cursor = db.cursor()

        # Get the most recent snapshot timestamp
        cursor.execute('''
            SELECT MAX(captured_at) FROM availability_snapshots
        ''')
        latest_timestamp = cursor.fetchone()[0]

        if not latest_timestamp:
            return jsonify({
                'timestamp': None,
                'data': {},
                'message': 'No data available yet'
            })

        # Get latest snapshots for each location/weekday/timeblock combination
        cursor.execute('''
            SELECT location, weekday, timeblock, available_slots
            FROM availability_snapshots
            WHERE DATE(captured_at) = DATE(?)
            ORDER BY captured_at DESC
        ''', (latest_timestamp,))

        snapshots = cursor.fetchall()

        # Aggregate data by weekday and timeblock
        data = {}
        for location, weekday, timeblock, slots in snapshots:
            key = f"{weekday}_{timeblock}"
            if key not in data:
                data[key] = {'arsenal': 0, 'postsv': 0}
            data[key][location] = slots

        # Calculate status (green/yellow/red) for each cell
        matrix = {}
        for weekday in range(7):  # 0=Monday to 6=Sunday
            for timeblock in ['morning', 'midday', 'evening']:
                key = f"{weekday}_{timeblock}"
                arsenal_slots = data.get(key, {}).get('arsenal', 0)
                postsv_slots = data.get(key, {}).get('postsv', 0)
                total_slots = arsenal_slots + postsv_slots

                # Determine status
                if total_slots >= 3:
                    status = 'green'
                elif total_slots >= 1:
                    status = 'yellow'
                else:
                    status = 'red'

                matrix[key] = {
                    'status': status,
                    'total': total_slots,
                    'arsenal': arsenal_slots,
                    'postsv': postsv_slots
                }

        return jsonify({
            'timestamp': latest_timestamp,
            'data': matrix
        })

    except Exception as e:
        logger.error(f"Dashboard availability error: {e}")
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

            response_data['slots'] = slots[:20]  # Top 20
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
        credential_mgr.save_credentials(user.id, portal_name, username, password)

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

@app.route('/profile')
@login_required
def profile():
    """User profile and newsletter settings page."""
    user = current_user()
    from database.db import get_db
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        SELECT newsletter_active, newsletter_weekday, newsletter_timeblock
        FROM users WHERE id = ?
    ''', (user.id,))
    row = cursor.fetchone()

    newsletter_settings = {
        'active': bool(row[0]) if row and row[0] is not None else False,
        'weekday': row[1] if row and row[1] is not None else 4,  # Default Friday
        'timeblock': row[2] if row and row[2] else 'evening'  # Default evening
    }

    return render_template('profile.html', user=user, newsletter=newsletter_settings)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
