import unittest
from app import app


class TestFrontendService(unittest.TestCase):
    """Unit tests for Frontend Service"""

    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True

    def test_health_check(self):
        """Test index page as health check"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_index_page(self):
        """Test index page loads"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)

    def test_search_page_get(self):
        """Test search page GET request"""
        response = self.app.get('/search')
        # Should redirect or show error since it's POST only
        self.assertIn(response.status_code, [200, 302, 405])


if __name__ == '__main__':
    unittest.main()

