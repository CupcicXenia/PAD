import unittest
import json
from unittest.mock import patch, MagicMock
from app import app


class TestBookingService(unittest.TestCase):
    """Unit tests for Booking Service"""

    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True

    def test_health_check(self):
        """Test health check endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'booking-service')

    @patch('app.get_db_connection')
    def test_create_booking_success(self, mock_db):
        """Test successful booking creation"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {'id': 1}
        mock_conn.cursor.return_value = mock_cur
        mock_db.return_value = mock_conn

        payload = {
            'hotel_id': 1,
            'hotel_name': 'Test Hotel',
            'room_type': 'Standard',
            'check_in': '2025-12-15',
            'check_out': '2025-12-20',
            'guest_name': 'John Doe',
            'guest_email': 'john@example.com',
            'total_price': 500.0
        }
        
        response = self.app.post(
            '/api/bookings',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('booking_id', data)
        self.assertIn('message', data)

    @patch('app.get_db_connection')
    def test_get_booking_success(self, mock_db):
        """Test getting booking by ID"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {
            'id': 1,
            'hotel_id': 1,
            'hotel_name': 'Test Hotel',
            'room_type': 'Standard',
            'check_in': '2025-12-15',
            'check_out': '2025-12-20',
            'guest_name': 'John Doe',
            'guest_email': 'john@example.com',
            'total_price': 500.0,
            'status': 'confirmed'
        }
        mock_conn.cursor.return_value = mock_cur
        mock_db.return_value = mock_conn

        response = self.app.get('/api/bookings/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['guest_name'], 'John Doe')

    @patch('app.get_db_connection')
    def test_get_booking_not_found(self, mock_db):
        """Test getting non-existent booking"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cur
        mock_db.return_value = mock_conn

        response = self.app.get('/api/bookings/999')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main()

