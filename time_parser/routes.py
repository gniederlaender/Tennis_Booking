"""Flask Blueprint for time parser API endpoints."""

from flask import Blueprint, request, jsonify
from .parser import TimeParser

# Create Blueprint
time_parser_bp = Blueprint('time_parser', __name__, url_prefix='/api')


@time_parser_bp.route('/parse-time', methods=['POST'])
def parse_time():
    """
    Parse natural language time query into structured TimeWindow objects.

    Request JSON:
        {
            "query": "morgen zwischen 10 und 13"
        }

    Response JSON:
        {
            "success": true,
            "interpreted_as": "morgen, 10:00–13:00",
            "confidence": 0.95,
            "windows": [
                {
                    "date": "2025-01-29",
                    "day_name": "Mittwoch",
                    "from": "10:00",
                    "to": "13:00"
                }
            ],
            "corrections": {
                "original": "morgen zwischen 10 und 13",
                "normalized": "morgen zwischen 10 und 13"
            }
        }
    """
    try:
        # Validate request
        if not request.json:
            return jsonify({
                "success": False,
                "error": "Request body must be JSON",
                "hint": "Send a JSON object with 'query' field"
            }), 400

        query = request.json.get('query', '').strip()

        if not query:
            return jsonify({
                "success": False,
                "error": "Query parameter is required",
                "hint": "Beispiele: 'morgen früh', 'next Sunday afternoon', 'between 10 and 12'"
            }), 400

        # Parse the query
        parser = TimeParser()
        result = parser.parse(query)

        # Return appropriate status code
        status_code = 200 if result['success'] else 400

        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "hint": "Beispiele: 'morgen früh', 'next Sunday afternoon', 'between 10 and 12'"
        }), 500
