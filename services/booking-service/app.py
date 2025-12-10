from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
import uuid
from datetime import datetime
import redis
import json

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'database': os.getenv('DB_NAME', 'booking_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'port': os.getenv('DB_PORT', '5432')
}

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            database='postgres',
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_CONFIG['database']}'")
        exists = cur.fetchone()

        if not exists:
            cur.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
            logger.info(f"Database {DB_CONFIG['database']} created successfully")
        else:
            logger.info(f"Database {DB_CONFIG['database']} already exists")

        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        raise

def init_db():
    """Initialize database with bookings and rooms tables"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id VARCHAR(36) PRIMARY KEY,
            hotel_id INTEGER NOT NULL,
            hotel_name VARCHAR(255) NOT NULL,
            room_type VARCHAR(50) NOT NULL,
            check_in DATE NOT NULL,
            check_out DATE NOT NULL,
            services TEXT,
            total_price DECIMAL(10,2) NOT NULL,
            status VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS room_availability (
            id SERIAL PRIMARY KEY,
            room_type VARCHAR(50) UNIQUE NOT NULL,
            available_count INTEGER NOT NULL,
            base_price DECIMAL(10,2) NOT NULL
        )
    ''')
    
    # Initialize room availability
    cur.execute('SELECT COUNT(*) FROM room_availability')
    if cur.fetchone()['count'] == 0:
        rooms = [
            ('Standard', 10, 100.0),
            ('Luxury', 5, 250.0),
            ('Apartment', 3, 400.0)
        ]
        
        for room in rooms:
            cur.execute(
                'INSERT INTO room_availability (room_type, available_count, base_price) VALUES (%s, %s, %s)',
                room
            )
    
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Booking database initialized successfully")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'booking-service'}), 200

@app.route('/api/rooms/availability', methods=['GET'])
def get_room_availability():
    """Get available rooms"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT room_type, available_count, base_price FROM room_availability')
        rooms = cur.fetchall()
        
        cur.close()
        conn.close()
        
        result = []
        for room in rooms:
            result.append({
                'room_type': room['room_type'],
                'available': room['available_count'],
                'base_price': float(room['base_price'])
            })
        
        return jsonify({'rooms': result}), 200
        
    except Exception as e:
        logger.error(f"Error getting room availability: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rooms/check', methods=['POST'])
def check_availability():
    """Check if specific room type is available"""
    try:
        data = request.get_json()
        room_type = data.get('room_type')
        quantity = data.get('quantity', 1)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            'SELECT available_count FROM room_availability WHERE room_type = %s',
            (room_type,)
        )

        result = cur.fetchone()
        cur.close()
        conn.close()

        if not result:
            return jsonify({'available': False, 'error': 'Room type not found'}), 404

        available = result['available_count'] >= quantity

        return jsonify({
            'available': available,
            'room_type': room_type,
            'requested': quantity,
            'in_stock': result['available_count']
        }), 200

    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    """Create a new booking"""
    try:
        data = request.get_json()

        hotel_id = data.get('hotel_id')
        hotel_name = data.get('hotel_name')
        room_type = data.get('room_type')
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        services = data.get('services', [])
        total_price = data.get('total_price')
        quantity = data.get('quantity', 1)

        # Validate required fields
        if not all([hotel_id, hotel_name, room_type, check_in, check_out, total_price]):
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Check availability
        cur.execute(
            'SELECT available_count FROM room_availability WHERE room_type = %s FOR UPDATE',
            (room_type,)
        )

        result = cur.fetchone()
        if not result or result['available_count'] < quantity:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({'error': 'Room not available'}), 400

        # Reserve rooms
        cur.execute(
            'UPDATE room_availability SET available_count = available_count - %s WHERE room_type = %s',
            (quantity, room_type)
        )

        # Create bookings
        booking_ids = []
        for _ in range(quantity):
            booking_id = str(uuid.uuid4())
            booking_ids.append(booking_id)

            cur.execute(
                '''INSERT INTO bookings
                   (id, hotel_id, hotel_name, room_type, check_in, check_out, services, total_price, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (booking_id, hotel_id, hotel_name, room_type, check_in, check_out,
                 json.dumps(services), total_price, 'pending')
            )

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Created {len(booking_ids)} bookings")

        return jsonify({
            'booking_ids': booking_ids,
            'status': 'pending',
            'message': 'Bookings created successfully'
        }), 201

    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings/<booking_id>', methods=['GET'])
def get_booking(booking_id):
    """Get booking details"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM bookings WHERE id = %s', (booking_id,))
        booking = cur.fetchone()

        cur.close()
        conn.close()

        if not booking:
            return jsonify({'error': 'Booking not found'}), 404

        return jsonify({
            'id': booking['id'],
            'hotel_id': booking['hotel_id'],
            'hotel_name': booking['hotel_name'],
            'room_type': booking['room_type'],
            'check_in': str(booking['check_in']),
            'check_out': str(booking['check_out']),
            'services': json.loads(booking['services']) if booking['services'] else [],
            'total_price': float(booking['total_price']),
            'status': booking['status']
        }), 200

    except Exception as e:
        logger.error(f"Error getting booking: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings/<booking_id>/confirm', methods=['PUT'])
def confirm_booking(booking_id):
    """Confirm a booking after payment"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            'UPDATE bookings SET status = %s WHERE id = %s RETURNING *',
            ('confirmed', booking_id)
        )

        booking = cur.fetchone()

        if not booking:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({'error': 'Booking not found'}), 404

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Booking {booking_id} confirmed")

        return jsonify({
            'booking_id': booking_id,
            'status': 'confirmed',
            'message': 'Booking confirmed successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error confirming booking: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    create_database_if_not_exists()
    init_db()
    app.run(host='0.0.0.0', port=5002, debug=True)

