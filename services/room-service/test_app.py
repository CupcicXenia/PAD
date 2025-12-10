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
            {
                'id': 1,
                'room_type': 'standard',
                'name_ru': 'Стандартный',
                'base_price': 100.0,
                'description': 'Standard room',
                'max_guests': 2,
                'amenities': 'WiFi, TV'
            },
            {
                'id': 2,
                'room_type': 'luxury',
                'name_ru': 'Люкс',
                'base_price': 250.0,
                'description': 'Luxury room',
                'max_guests': 4,
                'amenities': 'WiFi, TV, Minibar'
            }
        ]
        mock_conn.cursor.return_value = mock_cur
        mock_db.return_value = mock_conn

        response = self.app.get('/api/rooms/types')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('room_types', data)
        self.assertEqual(len(data['room_types']), 2)
        self.assertEqual(data['room_types'][0]['room_type'], 'standard')
        self.assertEqual(data['room_types'][1]['room_type'], 'luxury')

    @patch('app.get_db_connection')
    def test_get_pricing_rules(self, mock_db):
        """Test getting pricing rules"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [
            {
                'tariff_type': 'flexible',
                'name_ru': 'Гибкий',
                'multiplier': 1.2,
                'description': 'Flexible tariff'
            },
            {
                'tariff_type': 'non_refundable',
                'name_ru': 'Невозвратный',
                'multiplier': 0.9,
                'description': 'Non-refundable tariff'
            }
        ]
        mock_conn.cursor.return_value = mock_cur
        mock_db.return_value = mock_conn

        response = self.app.get('/api/pricing/tariffs')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('tariffs', data)
        self.assertEqual(len(data['tariffs']), 2)
        self.assertEqual(data['tariffs'][0]['tariff_type'], 'flexible')
        self.assertEqual(data['tariffs'][1]['tariff_type'], 'non_refundable')

    @patch('app.get_db_connection')
    def test_get_extra_services(self, mock_db):
        """Test getting extra services"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = [
            {
                'service_code': 'minibar',
                'name_ru': 'Мини-бар',
                'price': 50.0,
                'per_day': False,
                'description': 'Minibar service'
            },
            {
                'service_code': 'breakfast',
                'name_ru': 'Завтрак',
                'price': 20.0,
                'per_day': True,
                'description': 'Breakfast service'
            }
        ]
        mock_conn.cursor.return_value = mock_cur
        mock_db.return_value = mock_conn

        response = self.app.get('/api/services/extra')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('extra_services', data)
        self.assertEqual(len(data['extra_services']), 2)
        self.assertEqual(data['extra_services'][0]['service_code'], 'minibar')
        self.assertEqual(data['extra_services'][1]['service_code'], 'breakfast')


if __name__ == '__main__':
    unittest.main()

