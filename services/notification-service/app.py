from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import logging
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'database': os.getenv('DB_NAME', 'notification_db'),
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
    """Initialize database with notifications table"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id VARCHAR(36) PRIMARY KEY,
            booking_id VARCHAR(36) NOT NULL,
            notification_type VARCHAR(50) NOT NULL,
            recipient VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            status VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()
    logger.info("Notification database initialized successfully")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'notification-service'}), 200

@app.route('/api/notifications/send', methods=['POST'])
def send_notification():
    """Send notification (email or SMS)"""
    try:
        data = request.get_json()
        
        booking_id = data.get('booking_id')
        notification_type = data.get('type', 'email')  # email or sms
        recipient = data.get('recipient')
        message = data.get('message')
        
        if not all([booking_id, recipient, message]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        notification_id = str(uuid.uuid4())
        
        # Simulate sending notification
        if notification_type == 'email':
            logger.info(f"Sending email to {recipient}: {message}")
            status = 'sent'
        elif notification_type == 'sms':
            logger.info(f"Sending SMS to {recipient}: {message}")
            status = 'sent'
        else:
            return jsonify({'error': 'Invalid notification type'}), 400
        
        # Save to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            '''INSERT INTO notifications 
               (id, booking_id, notification_type, recipient, message, status)
               VALUES (%s, %s, %s, %s, %s, %s)''',
            (notification_id, booking_id, notification_type, recipient, message, status)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'notification_id': notification_id,
            'status': status,
            'type': notification_type,
            'message': f'{notification_type.upper()} sent successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/booking/<booking_id>', methods=['POST'])
def notify_booking_confirmation(booking_id):
    """Send booking confirmation notifications"""
    try:
        data = request.get_json()
        email = data.get('email')
        phone = data.get('phone')
        hotel_name = data.get('hotel_name', 'Hotel')
        
        notifications_sent = []
        
        # Send email notification
        if email:
            email_message = f"Ваше бронирование {booking_id} в отеле {hotel_name} подтверждено!"
            email_result = send_notification_internal(booking_id, 'email', email, email_message)
            notifications_sent.append(email_result)
        
        # Send SMS notification
        if phone:
            sms_message = f"Бронирование {booking_id} подтверждено в {hotel_name}"
            sms_result = send_notification_internal(booking_id, 'sms', phone, sms_message)
            notifications_sent.append(sms_result)
        
        return jsonify({
            'booking_id': booking_id,
            'notifications': notifications_sent,
            'message': 'Notifications sent successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending booking notifications: {str(e)}")
        return jsonify({'error': str(e)}), 500

def send_notification_internal(booking_id, notification_type, recipient, message):
    """Internal function to send notification"""
    notification_id = str(uuid.uuid4())
    
    logger.info(f"Sending {notification_type} to {recipient}: {message}")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        '''INSERT INTO notifications 
           (id, booking_id, notification_type, recipient, message, status)
           VALUES (%s, %s, %s, %s, %s, %s)''',
        (notification_id, booking_id, notification_type, recipient, message, 'sent')
    )
    
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        'notification_id': notification_id,
        'type': notification_type,
        'status': 'sent'
    }

if __name__ == '__main__':
    create_database_if_not_exists()
    init_db()
    app.run(host='0.0.0.0', port=5004, debug=True)

