import unittest
from app import create_app
from config import TestingConfig
from app.models import db
from app.models.ambulance import EmergencyRequest

class AmbulanceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_emergency_ambulance_request_simulation(self):
        res = self.client.post('/submitAmbulanceRequest', json={
            'name': 'Emergency Patient',
            'phone': '+91 99999 11111',
            'emergency': 'Severe chest pain and shortness of breath',
            'location': 'Main Gate Campus 1'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(data['is_simulation'])
        self.assertEqual(data['status'], 'ACKNOWLEDGED')

        with self.app.app_context():
            req = EmergencyRequest.query.filter_by(patient_name='Emergency Patient').first()
            self.assertIsNotNone(req)
            self.assertEqual(req.priority, 'CRITICAL')
            self.assertTrue(req.is_simulation)

if __name__ == '__main__':
    unittest.main()
