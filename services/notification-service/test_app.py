import unittest
import json
from unittest.mock import patch, MagicMock
from app import app


class TestNotificationService(unittest.TestCase):
    """Unit tests for Notification Service"""

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
        self.assertEqual(data['service'], 'notification-service')

    @patch('app.get_db_connection')
    def test_send_notification_success(self, mock_db):
        """Test successful notification sending"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {'id': 1}
        mock_conn.cursor.return_value = mock_cur
        mock_db.return_value = mock_conn

        payload = {
            'booking_id': 1,
            'recipient': 'john@example.com',
            'notification_type': 'email',
            'message': 'Your booking is confirmed'
        }

        response = self.app.post(
            '/api/notifications/send',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('notification_id', data)
        self.assertIn('message', data)

    @patch('app.get_db_connection')
    def test_get_notifications_by_booking(self, mock_db):
        """Test sending booking confirmation notification"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = {'id': 1}
        mock_conn.cursor.return_value = mock_cur
        mock_db.return_value = mock_conn

        payload = {
            'email': 'john@example.com',
            'hotel_name': 'Test Hotel',
            'check_in': '2025-12-15',
            'check_out': '2025-12-20'
        }

        response = self.app.post(
            '/api/notifications/booking/1',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('notification_id', data)


if __name__ == '__main__':
    unittest.main()

