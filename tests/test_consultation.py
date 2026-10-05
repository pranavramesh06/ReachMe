import unittest
from app import create_app
from config import TestingConfig
from app.models import db
from app.models.doctor import Doctor
from app.models.appointment import Appointment

class ConsultationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            doc = Doctor(name='Dr. John Smith', specialty='Cardiologist', consultation_fee=500.0)
            db.session.add(doc)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_appointment_booking_and_double_booking_prevention(self):
        res1 = self.client.post('/submit-consult', data={
            'name': 'Patient One',
            'phone': '9876543210',
            'problem': 'Chest tightness',
            'doctor': 'Dr. John Smith: Cardiologist',
            'date': '2026-10-10',
            'time_slot': '10:00 AM'
        }, follow_redirects=True)
        self.assertEqual(res1.status_code, 200)

        with self.app.app_context():
            app1 = Appointment.query.filter_by(patient_name='Patient One').first()
            self.assertIsNotNone(app1)

        res2 = self.client.post('/submit-consult', data={
            'name': 'Patient Two',
            'phone': '1112223333',
            'problem': 'Routine check',
            'doctor': 'Dr. John Smith: Cardiologist',
            'date': '2026-10-10',
            'time_slot': '10:00 AM'
        }, follow_redirects=True)
        
        with self.app.app_context():
            app2 = Appointment.query.filter_by(patient_name='Patient Two').first()
            self.assertIsNone(app2)

if __name__ == '__main__':
    unittest.main()
