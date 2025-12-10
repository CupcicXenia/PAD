import unittest
import json
from app import app


class TestHotelSearchService(unittest.TestCase):
    """Unit tests for Hotel Search Service"""

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
        self.assertEqual(data['service'], 'hotel-search-service')

    def test_search_hotels_success(self):
        """Test successful hotel search"""
        payload = {
            'city': 'Кишинёв',
            'check_in': '2025-12-15',
            'check_out': '2025-12-20'
        }
        response = self.app.post(
            '/api/search',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Check response structure
        self.assertIn('hotels', data)
        self.assertIn('check_in', data)
        self.assertIn('check_out', data)
        
        # Check hotels generated
        self.assertEqual(len(data['hotels']), 2)
        
        # Check first hotel
        hotel1 = data['hotels'][0]
        self.assertEqual(hotel1['id'], 1)
        self.assertEqual(hotel1['city'], 'Кишинёв')
        self.assertEqual(hotel1['type'], 'City')
        self.assertIn('Городской', hotel1['name'])
        self.assertEqual(hotel1['rating'], 4.5)
        
        # Check second hotel
        hotel2 = data['hotels'][1]
        self.assertEqual(hotel2['id'], 2)
        self.assertEqual(hotel2['city'], 'Кишинёв')
        self.assertEqual(hotel2['type'], 'Resort')
        self.assertIn('Курортный', hotel2['name'])
        self.assertEqual(hotel2['rating'], 4.8)

    def test_search_hotels_any_city(self):
        """Test hotel search works for any city"""
        cities = ['Moscow', 'Paris', 'Tokyo', 'Test City']
        
        for city in cities:
            payload = {
                'city': city,
                'check_in': '2025-12-15',
                'check_out': '2025-12-20'
            }
            response = self.app.post(
                '/api/search',
                data=json.dumps(payload),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(len(data['hotels']), 2)
            self.assertEqual(data['hotels'][0]['city'], city)
            self.assertEqual(data['hotels'][1]['city'], city)

    def test_search_hotels_missing_city(self):
        """Test search fails when city is missing"""
        payload = {
            'check_in': '2025-12-15',
            'check_out': '2025-12-20'
        }
        response = self.app.post(
            '/api/search',
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main()

