import unittest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app import app


class TestAPIGateway(unittest.TestCase):
    """Unit tests for API Gateway (FastAPI)"""

    def setUp(self):
        """Set up test client"""
        self.client = TestClient(app)

    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'api-gateway')

    @patch('httpx.AsyncClient.post')
    async def test_search_hotels_proxy(self, mock_post):
        """Test search hotels proxy endpoint"""
        # Mock response from hotel-search-service
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'hotels': [
                {'id': 1, 'name': 'Test Hotel', 'city': 'Moscow'}
            ],
            'check_in': '2025-12-15',
            'check_out': '2025-12-20'
        }
        mock_post.return_value = mock_response

        payload = {
            'city': 'Moscow',
            'check_in': '2025-12-15',
            'check_out': '2025-12-20'
        }
        
        response = self.client.post('/api/search', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('hotels', data)

    def test_search_hotels_missing_city(self):
        """Test search fails when city is missing"""
        payload = {
            'check_in': '2025-12-15',
            'check_out': '2025-12-20'
        }
        
        response = self.client.post('/api/search', json=payload)
        self.assertEqual(response.status_code, 422)  # FastAPI validation error


if __name__ == '__main__':
    unittest.main()

