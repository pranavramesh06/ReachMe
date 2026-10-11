import unittest
from app import create_app
from config import TestingConfig
from app.models import db
from app.models.user import User
from app.models.doctor import Doctor, ConsultationNote, PatientFeedback
from app.models.appointment import Appointment

class DoctorClinicalWorkspaceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

            # Doctor user & profile
            self.doc_user = User(email='doc@hospital.com', full_name='Dr. Marcus Vance', role='DOCTOR')
            self.doc_user.set_password('doc123')
            db.session.add(self.doc_user)
            db.session.flush()

            self.doctor = Doctor(user_id=self.doc_user.id, name='Dr. Marcus Vance', specialty='Neurology')
            db.session.add(self.doctor)

            # Patient user
            self.patient_user = User(email='pt@hospital.com', full_name='Alice Walker', role='PATIENT')
            self.patient_user.set_password('pt123')
            db.session.add(self.patient_user)
            db.session.flush()

            # Appointment
            self.appointment = Appointment(
                patient_id=self.patient_user.id,
                patient_name='Alice Walker',
                patient_phone='+91 99999 88888',
                problem_description='Chronic migraine headaches',
                doctor_id=self.doctor.id,
                doctor_name=self.doctor.name,
                doctor_specialty=self.doctor.specialty,
                appointment_date='2026-10-15',
                time_slot='11:00 AM',
                status='CONFIRMED'
            )
            db.session.add(self.appointment)
            db.session.commit()

            self.doc_user_id = self.doc_user.id
            self.patient_user_id = self.patient_user.id
            self.doctor_id = self.doctor.id
            self.appt_id = self.appointment.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_doctor_dashboard_access_control(self):
        """Only authenticated doctors can access the clinical doctor workspace."""
        # Unauthenticated attempt redirects to login
        res = self.client.get('/doctor/dashboard')
        self.assertEqual(res.status_code, 302)

        # Patient attempt is rejected with 403
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.patient_user_id
            sess['user_role'] = 'PATIENT'
        res = self.client.get('/doctor/dashboard')
        self.assertEqual(res.status_code, 403)

        # Doctor attempt succeeds with 200
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.doc_user_id
            sess['user_role'] = 'DOCTOR'
        res = self.client.get('/doctor/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Clinical Workspace', res.get_data(as_text=True))

    def test_doctor_can_save_consultation_notes(self):
        """Doctor can save clinical notes and distinguish private notes from patient advice."""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.doc_user_id
            sess['user_role'] = 'DOCTOR'

        res = self.client.post(f'/doctor/appointment/{self.appt_id}/notes', data={
            'clinical_assessment': 'Tension-type migraine secondary to stress',
            'symptoms_observations': 'Photophobia and unilateral throbbing',
            'private_recommendations': 'Order MRI if symptoms persist past 2 weeks',
            'patient_advice': 'Maintain regular hydration and sleep patterns',
            'recommended_followup': '2 weeks review',
            'followup_date': '2026-10-29',
            'is_shared_with_patient': 'on',
            'mark_completed': 'on'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            note = ConsultationNote.query.filter_by(appointment_id=self.appt_id).first()
            self.assertIsNotNone(note)
            self.assertEqual(note.clinical_assessment, 'Tension-type migraine secondary to stress')
            self.assertTrue(note.is_shared_with_patient)

            # Appointment marked as completed
            appt = Appointment.query.get(self.appt_id)
            self.assertEqual(appt.status, 'COMPLETED')

    def test_private_clinical_notes_not_leaked_to_patient(self):
        """Private clinical notes are never exposed in patient-facing dictionaries."""
        with self.app.app_context():
            note = ConsultationNote(
                appointment_id=self.appt_id,
                doctor_id=self.doctor_id,
                patient_id=self.patient_user_id,
                clinical_assessment='Confidential diagnostic suspicion',
                private_recommendations='Private internal physician remarks',
                patient_advice='Drink plenty of water',
                is_shared_with_patient=True
            )
            db.session.add(note)
            db.session.commit()

            # Test the patient dictionary method
            patient_view = note.to_patient_dict()
            self.assertIsNotNone(patient_view)
            self.assertNotIn('clinical_assessment', patient_view)
            self.assertNotIn('private_recommendations', patient_view)
            self.assertEqual(patient_view['patient_advice'], 'Drink plenty of water')

    def test_patient_feedback_workflow_and_duplicate_prevention(self):
        """Patient can submit feedback only for completed appointments, and duplicates are prevented."""
        # While confirmed (not yet completed), feedback is blocked
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.patient_user_id
            sess['user_role'] = 'PATIENT'

        res = self.client.post(f'/patient/appointment/{self.appt_id}/feedback', data={
            'rating': '5',
            'feedback_text': 'Dr. Vance was attentive and thorough.'
        }, follow_redirects=True)

        with self.app.app_context():
            self.assertEqual(PatientFeedback.query.count(), 0)

        # Mark appointment completed
        with self.app.app_context():
            appt = Appointment.query.get(self.appt_id)
            appt.status = 'COMPLETED'
            db.session.commit()

        # Submit valid feedback
        res = self.client.post(f'/patient/appointment/{self.appt_id}/feedback', data={
            'rating': '5',
            'feedback_text': 'Dr. Vance was attentive and thorough.'
        }, follow_redirects=True)

        with self.app.app_context():
            fb = PatientFeedback.query.filter_by(appointment_id=self.appt_id).first()
            self.assertIsNotNone(fb)
            self.assertEqual(fb.rating, 5)

        # Attempt duplicate feedback
        res_dup = self.client.post(f'/patient/appointment/{self.appt_id}/feedback', data={
            'rating': '4',
            'feedback_text': 'Duplicate attempt'
        }, follow_redirects=True)

        with self.app.app_context():
            self.assertEqual(PatientFeedback.query.count(), 1)

if __name__ == '__main__':
    unittest.main()
