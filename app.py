"""Flask web application for Tennis Court Booking Finder."""

from flask import Flask, render_template, request, jsonify
from datetime import datetime
from timeframe_parser import TimeframeParser
from scrapers_v2 import scrape_all_portals
from preference_engine import PreferenceEngine
from booking import book_court
from trainer_finder import find_trainers

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tennis-booking-secret-key-change-in-production'

@app.route('/')
def index():
    """Main search page."""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle search request."""
    try:
        timeframe = request.json.get('timeframe', '')
        include_trainers = request.json.get('includeTrainers', False)
        trainer_name = request.json.get('trainerName', None)

        if not timeframe:
            return jsonify({'error': 'Please enter a timeframe'}), 400

        # Parse timeframe
        parser = TimeframeParser()
        parsed = parser.parse(timeframe)
        date = parsed['date']
        start_time = parsed['start_time']
        end_time = parsed['end_time']

        # Scrape portals
        slots = scrape_all_portals(date, start_time, end_time)

        # Get preferred slot if available
        pref_engine = PreferenceEngine()
        preferred = None
        if pref_engine.has_confidence() and slots:
            preferred_slot = pref_engine.get_preferred_slot(slots)
            if preferred_slot:
                preferred = slots.index(preferred_slot)

        # Search for trainers if requested
        trainers = []
        if include_trainers:
            print(f"\n{'='*60}")
            print("Searching for trainers...")
            print(f"{'='*60}")
            trainers = find_trainers(date, start_time, end_time, trainer_name)
            print(f"Found {len(trainers)} trainer slots\n")

        # Format response
        response_data = {
            'success': True,
            'timeframe': {
                'date': date.strftime('%Y-%m-%d'),
                'day': date.strftime('%A'),
                'start': start_time,
                'end': end_time
            },
            'slots': slots[:20],  # Top 20
            'total': len(slots),
            'preferred_index': preferred
        }

        # Add trainer data if available
        if trainers:
            response_data['trainers'] = trainers

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/book', methods=['POST'])
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
