import unittest
import json
from unittest.mock import patch, MagicMock
from app import app


class TestRoomService(unittest.TestCase):
    """Unit tests for Room Service"""

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
        self.assertEqual(data['service'], 'room-service')

    @patch('app.get_db_connection')
    def test_get_room_types(self, mock_db):
        """Test getting all room types"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [
            {'id': 1, 'name': 'Standard', 'base_price': 100.0, 'description': 'Standard room'},
            {'id': 2, 'name': 'Luxury', 'base_price': 250.0, 'description': 'Luxury room'}
        ]
        mock_conn.cursor.return_value = mock_cur
        mock_db.return_value = mock_conn

        response = self.app.get('/api/room-types')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], 'Standard')
        self.assertEqual(data[1]['name'], 'Luxury')

    @patch('app.get_db_connection')
    def test_get_pricing_rules(self, mock_db):
        """Test getting pricing rules"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [
            {'id': 1, 'tariff_name': 'Flexible', 'price_multiplier': 1.2},
            {'id': 2, 'tariff_name': 'NonRefundable', 'price_multiplier': 0.9}
        ]
        mock_conn.cursor.return_value = mock_cur
        mock_db.return_value = mock_conn

        response = self.app.get('/api/pricing-rules')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['tariff_name'], 'Flexible')
        self.assertEqual(data[1]['tariff_name'], 'NonRefundable')

    @patch('app.get_db_connection')
    def test_get_extra_services(self, mock_db):
        """Test getting extra services"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [
            {'id': 1, 'service_name': 'minibar', 'price': 50.0, 'is_per_day': False},
            {'id': 2, 'service_name': 'breakfast', 'price': 20.0, 'is_per_day': True}
        ]
        mock_conn.cursor.return_value = mock_cur
        mock_db.return_value = mock_conn

        response = self.app.get('/api/extra-services')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['service_name'], 'minibar')
        self.assertEqual(data[1]['service_name'], 'breakfast')


if __name__ == '__main__':
    unittest.main()

