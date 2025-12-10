from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# No database needed - hotels are generated dynamically like in monolith

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'hotel-search-service'}), 200

@app.route('/api/search', methods=['POST'])
def search_hotels():
    """Search hotels by city and dates - generates hotels dynamically like in monolith"""
    try:
        data = request.get_json()
        city = data.get('city')
        check_in = data.get('check_in')
        check_out = data.get('check_out')

        if not city:
            return jsonify({'error': 'City is required'}), 400

        # Generate hotels dynamically based on city (like in original monolith)
        hotels = [
            {
                'id': 1,
                'name': f"Отель {city} Городской",
                'city': city,
                'type': 'City',
                'description': f"Современный городской отель в центре города {city}",
                'rating': 4.5
            },
            {
                'id': 2,
                'name': f"Отель {city} Курортный",
                'city': city,
                'type': 'Resort',
                'description': f"Роскошный курортный отель в {city} с видом на парк",
                'rating': 4.8
            }
        ]

        logger.info(f"Generated {len(hotels)} hotels for city: {city}")
        return jsonify({
            'hotels': hotels,
            'check_in': check_in,
            'check_out': check_out
        }), 200

    except Exception as e:
        logger.error(f"Error searching hotels: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

