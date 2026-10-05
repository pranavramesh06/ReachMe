import unittest
from app import create_app
from config import TestingConfig
from app.models import db
from app.services.triage_service import analyze_triage_symptoms

class IntelligenceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_triage_engine_cardiac_urgency(self):
        with self.app.app_context():
            res = analyze_triage_symptoms("Patient reporting severe chest pain and left arm pain", severity=9, duration_days=1)
            self.assertEqual(res['urgency_level'], 'CRITICAL')
            self.assertGreaterEqual(res['risk_score'], 80.0)
            self.assertEqual(res['recommended_specialization'], 'Cardiologist')
            self.assertGreater(len(res['contributing_factors']), 0)

    def test_triage_engine_routine_urgency(self):
        with self.app.app_context():
            res = analyze_triage_symptoms("Mild skin rash on arm", severity=2, duration_days=1)
            self.assertIn(res['urgency_level'], ['ROUTINE', 'MEDIUM'])
            self.assertLess(res['risk_score'], 60.0)
            self.assertEqual(res['recommended_specialization'], 'Dermatologist')

if __name__ == '__main__':
    unittest.main()
