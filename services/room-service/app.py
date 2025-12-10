from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'database': os.getenv('DB_NAME', 'room_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'port': os.getenv('DB_PORT', '5432')
}

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
    """Initialize database with room types and pricing"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS room_types (
            id SERIAL PRIMARY KEY,
            room_type VARCHAR(50) UNIQUE NOT NULL,
            name_ru VARCHAR(100) NOT NULL,
            description TEXT,
            base_price DECIMAL(10,2) NOT NULL,
            max_guests INTEGER NOT NULL,
            amenities TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pricing_rules (
            id SERIAL PRIMARY KEY,
            tariff_type VARCHAR(50) NOT NULL,
            name_ru VARCHAR(100) NOT NULL,
            multiplier DECIMAL(3,2) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS extra_services (
            id SERIAL PRIMARY KEY,
            service_code VARCHAR(50) UNIQUE NOT NULL,
            name_ru VARCHAR(100) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            per_day BOOLEAN DEFAULT FALSE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert room types if table is empty
    cur.execute('SELECT COUNT(*) FROM room_types')
    if cur.fetchone()['count'] == 0:
        room_types = [
            ('Standard', 'Стандартный номер', 'Уютный одноместный номер с базовыми удобствами', 100.0, 2, 
             ['Wi-Fi', 'Телевизор', 'Кондиционер']),
            ('Luxury', 'Люкс', 'Просторный номер с премиум-удобствами и видом на город', 250.0, 3,
             ['Wi-Fi', 'Телевизор', 'Кондиционер', 'Мини-бар', 'Джакузи']),
            ('Apartment', 'Апартаменты', 'Полноценный номер с кухней и гостиной', 400.0, 4,
             ['Wi-Fi', 'Телевизор', 'Кондиционер', 'Кухня', 'Стиральная машина', 'Балкон'])
        ]
        
        for room in room_types:
            cur.execute(
                '''INSERT INTO room_types (room_type, name_ru, description, base_price, max_guests, amenities)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                room
            )
    
    # Insert pricing rules if table is empty
    cur.execute('SELECT COUNT(*) FROM pricing_rules')
    if cur.fetchone()['count'] == 0:
        pricing_rules = [
            ('Flexible', 'Гибкий тариф', 1.2, 'Возможность бесплатной отмены, +20% к стоимости'),
            ('NonRefundable', 'Невозвратный тариф', 0.9, 'Без возможности отмены, скидка 10%')
        ]
        
        for rule in pricing_rules:
            cur.execute(
                '''INSERT INTO pricing_rules (tariff_type, name_ru, multiplier, description)
                   VALUES (%s, %s, %s, %s)''',
                rule
            )
    
    # Insert extra services if table is empty
    cur.execute('SELECT COUNT(*) FROM extra_services')
    if cur.fetchone()['count'] == 0:
        extra_services = [
            ('minibar', 'Мини-бар', 50.0, False, 'Доступ к мини-бару в номере'),
            ('late_checkout', 'Поздний выезд', 30.0, False, 'Выезд до 18:00 вместо 12:00'),
            ('breakfast', 'Завтрак', 20.0, True, 'Завтрак "шведский стол"'),
            ('transfer', 'Трансфер', 40.0, False, 'Трансфер из/в аэропорт')
        ]
        
        for service in extra_services:
            cur.execute(
                '''INSERT INTO extra_services (service_code, name_ru, price, per_day, description)
                   VALUES (%s, %s, %s, %s, %s)''',
                service
            )
    
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Room database initialized successfully")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'room-service'}), 200

@app.route('/api/rooms/types', methods=['GET'])
def get_room_types():
    """Get all room types with details"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM room_types ORDER BY base_price')
        rooms = cur.fetchall()

        cur.close()
        conn.close()

        result = []
        for room in rooms:
            result.append({
                'id': room['id'],
                'room_type': room['room_type'],
                'name': room['name_ru'],
                'description': room['description'],
                'base_price': float(room['base_price']),
                'max_guests': room['max_guests'],
                'amenities': room['amenities']
            })

        return jsonify({'room_types': result}), 200

    except Exception as e:
        logger.error(f"Error getting room types: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rooms/types/<room_type>', methods=['GET'])
def get_room_type(room_type):
    """Get specific room type details"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM room_types WHERE room_type = %s', (room_type,))
        room = cur.fetchone()

        cur.close()
        conn.close()

        if not room:
            return jsonify({'error': 'Room type not found'}), 404

        return jsonify({
            'id': room['id'],
            'room_type': room['room_type'],
            'name': room['name_ru'],
            'description': room['description'],
            'base_price': float(room['base_price']),
            'max_guests': room['max_guests'],
            'amenities': room['amenities']
        }), 200

    except Exception as e:
        logger.error(f"Error getting room type: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pricing/tariffs', methods=['GET'])
def get_tariffs():
    """Get all pricing tariffs"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM pricing_rules')
        tariffs = cur.fetchall()

        cur.close()
        conn.close()

        result = []
        for tariff in tariffs:
            result.append({
                'tariff_type': tariff['tariff_type'],
                'name': tariff['name_ru'],
                'multiplier': float(tariff['multiplier']),
                'description': tariff['description']
            })

        return jsonify({'tariffs': result}), 200

    except Exception as e:
        logger.error(f"Error getting tariffs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/services/extra', methods=['GET'])
def get_extra_services():
    """Get all extra services"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM extra_services ORDER BY price')
        services = cur.fetchall()

        cur.close()
        conn.close()

        result = []
        for service in services:
            result.append({
                'service_code': service['service_code'],
                'name': service['name_ru'],
                'price': float(service['price']),
                'per_day': service['per_day'],
                'description': service['description']
            })

        return jsonify({'extra_services': result}), 200

    except Exception as e:
        logger.error(f"Error getting extra services: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pricing/calculate', methods=['POST'])
def calculate_price():
    """Calculate total price based on room type, tariff, days, and extras"""
    try:
        data = request.get_json()

        room_type = data.get('room_type')
        tariff_type = data.get('tariff', 'Flexible')
        days = int(data.get('days', 1))
        extras = data.get('extras', [])

        if not room_type or days < 1:
            return jsonify({'error': 'Invalid parameters'}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        # Get room base price
        cur.execute('SELECT base_price FROM room_types WHERE room_type = %s', (room_type,))
        room = cur.fetchone()

        if not room:
            cur.close()
            conn.close()
            return jsonify({'error': 'Room type not found'}), 404

        base_price = float(room['base_price'])

        # Get tariff multiplier
        cur.execute('SELECT multiplier FROM pricing_rules WHERE tariff_type = %s', (tariff_type,))
        tariff = cur.fetchone()

        if not tariff:
            cur.close()
            conn.close()
            return jsonify({'error': 'Tariff not found'}), 404

        multiplier = float(tariff['multiplier'])

        # Calculate base price with tariff
        total_price = base_price * days * multiplier

        # Add extra services
        extras_total = 0
        extras_details = []

        for extra_code in extras:
            cur.execute('SELECT * FROM extra_services WHERE service_code = %s', (extra_code,))
            service = cur.fetchone()

            if service:
                service_price = float(service['price'])
                if service['per_day']:
                    service_price *= days

                extras_total += service_price
                extras_details.append({
                    'code': service['service_code'],
                    'name': service['name_ru'],
                    'price': service_price
                })

        total_price += extras_total

        cur.close()
        conn.close()

        return jsonify({
            'room_type': room_type,
            'base_price': base_price,
            'days': days,
            'tariff': tariff_type,
            'tariff_multiplier': multiplier,
            'room_total': base_price * days * multiplier,
            'extras': extras_details,
            'extras_total': extras_total,
            'total_price': round(total_price, 2)
        }), 200

    except Exception as e:
        logger.error(f"Error calculating price: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    create_database_if_not_exists()
    init_db()
    app.run(host='0.0.0.0', port=5003, debug=True)

