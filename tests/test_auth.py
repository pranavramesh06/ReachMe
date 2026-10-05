import unittest
from app import create_app
from config import TestingConfig
from app.models import db
from app.models.user import User

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_registration_and_login(self):
        response = self.client.post('/register', data={
            'full_name': 'Test Patient',
            'email': 'testpatient@example.com',
            'phone': '+91 99999 88888',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'PATIENT'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            user = User.query.filter_by(email='testpatient@example.com').first()
            self.assertIsNotNone(user)
            self.assertTrue(user.check_password('password123'))

        login_res = self.client.post('/login', data={
            'email': 'testpatient@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)

if __name__ == '__main__':
    unittest.main()
