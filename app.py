"""Flask web application for Tennis Court Booking Finder."""

from flask import Flask, render_template, request, jsonify
from datetime import datetime
from timeframe_parser import TimeframeParser
from scrapers_v2 import scrape_all_portals
from preference_engine import PreferenceEngine

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

        # Format response
        return jsonify({
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
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
