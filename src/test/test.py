import unittest

from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()

    def tearDown(self):
        self.ctx.pop()

    def test_home(self):
        response = self.client.get('/')
        assert response.status_code == 200
    
if __name__ == "__main__":
    unittest.main()