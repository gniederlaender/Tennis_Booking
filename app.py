"""Flask web application for Tennis Court Booking Finder."""

from flask import Flask, render_template, request, jsonify, g
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime
from timeframe_parser import TimeframeParser
from scrapers_v2 import scrape_all_portals
from preference_engine import PreferenceEngine
from booking import book_court
from trainer_finder import find_trainers
import config
from database.db import init_db, close_db
from auth import auth_bp, login_required

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SESSION_COOKIE_SECURE'] = config.SESSION_COOKIE_SECURE
app.config['SESSION_COOKIE_HTTPONLY'] = config.SESSION_COOKIE_HTTPONLY
app.config['SESSION_COOKIE_SAMESITE'] = config.SESSION_COOKIE_SAMESITE
app.config['PERMANENT_SESSION_LIFETIME'] = config.PERMANENT_SESSION_LIFETIME

# Configure app to work behind reverse proxy
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Register authentication blueprint
app.register_blueprint(auth_bp)

# Register database teardown
app.teardown_appcontext(close_db)

@app.route('/')
@login_required
def index():
    """Main search page."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
@login_required
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
            print(f"\n{'='*60}")
            print("Searching for trainers...")
            print(f"{'='*60}")
            trainers = find_trainers(date, start_time, end_time, trainer_name)
            print(f"Found {len(trainers)} trainer slots\n")

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
        slot = request.json.get('slot', {})

        if not slot:
            return jsonify({'error': 'No slot data provided'}), 400

        # Validate required fields
        required_fields = ['venue', 'date', 'time', 'court_name']
        missing_fields = [f for f in required_fields if not slot.get(f)]
        if missing_fields:
            return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400

        # Attempt booking
        success, message = book_court(slot)

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

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
