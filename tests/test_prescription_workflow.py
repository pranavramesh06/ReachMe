import unittest
from datetime import datetime, timedelta
from app import create_app
from config import TestingConfig
from app.models import db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.medicine import Medicine, MedicineCategory
from app.models.order import Order
from app.models.prescription import Prescription, MedicineApprovalRequest

class PrescriptionWorkflowTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            
            # Setup category
            cat = MedicineCategory(name='General')
            db.session.add(cat)
            db.session.flush()

            # OTC Medicine
            self.otc_med = Medicine(name='Paracetamol 500mg', price=25.0, stock_quantity=100, requires_prescription=False, category_id=cat.id)
            # Prescription Required Medicine
            self.rx_med = Medicine(name='Amoxicillin 500mg', price=120.0, stock_quantity=50, requires_prescription=True, category_id=cat.id)
            db.session.add_all([self.otc_med, self.rx_med])

            # Patient user
            self.patient = User(email='patient@test.com', full_name='Test Patient', role='PATIENT')
            self.patient.set_password('patient123')

            # Doctor user
            self.doctor_user = User(email='doctor@test.com', full_name='Dr. Smith', role='DOCTOR')
            self.doctor_user.set_password('doctor123')
            db.session.add_all([self.patient, self.doctor_user])
            db.session.flush()

            self.doctor = Doctor(user_id=self.doctor_user.id, name='Dr. Smith', specialty='General Physician')
            db.session.add(self.doctor)

            db.session.commit()

            self.patient_id = self.patient.id
            self.doctor_id = self.doctor.id
            self.rx_med_id = self.rx_med.id
            self.otc_med_id = self.otc_med.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_otc_medicine_purchased_without_prescription(self):
        """1. An unrestricted OTC medicine can be purchased normally through checkout."""
        res = self.client.post('/submit', data={
            'Full_name': 'Test Buyer',
            'Phone_number': '9876543210',
            'Shipping_address': 'Test Address',
            'Medication': ['Paracetamol 500mg'],
            'Quantity': ['2']
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            order = Order.query.filter_by(full_name='Test Buyer').first()
            self.assertIsNotNone(order)
            self.assertEqual(order.total_amount, 50.0)

    def test_rx_medicine_blocked_without_prescription(self):
        """2. A prescription-required medicine cannot be purchased without an approved prescription."""
        # Authenticate patient
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.patient_id
            sess['user_role'] = 'PATIENT'

        res = self.client.post('/submit', data={
            'Full_name': 'Test Patient',
            'Phone_number': '9876543210',
            'Shipping_address': 'Test Address',
            'Medication': ['Amoxicillin 500mg'],
            'Quantity': ['1']
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        # Should redirect back with warning and create no order
        with self.app.app_context():
            order = Order.query.filter_by(full_name='Test Patient').first()
            self.assertIsNone(order)

    def test_rx_upload_alone_does_not_authorize_purchase(self):
        """3. Uploading a prescription alone does not authorize a purchase without doctor review."""
        with self.app.app_context():
            rx = Prescription(
                patient_id=self.patient_id,
                filename='test_rx.png',
                file_path='/static/uploads/test_rx.png',
                status='PENDING_REVIEW'
            )
            db.session.add(rx)
            db.session.commit()

        with self.client.session_transaction() as sess:
            sess['user_id'] = self.patient_id
            sess['user_role'] = 'PATIENT'

        res = self.client.post('/submit', data={
            'Full_name': 'Test Patient',
            'Phone_number': '9876543210',
            'Shipping_address': 'Test Address',
            'Medication': ['Amoxicillin 500mg'],
            'Quantity': ['1']
        }, follow_redirects=True)

        with self.app.app_context():
            order = Order.query.filter_by(full_name='Test Patient').first()
            self.assertIsNone(order)

    def test_pending_or_rejected_request_blocks_purchase(self):
        """4 & 5. A pending or rejected request does not authorize purchase."""
        with self.app.app_context():
            req = MedicineApprovalRequest(
                patient_id=self.patient_id,
                medicine_id=self.rx_med_id,
                doctor_id=self.doctor_id,
                quantity_requested=2,
                status='PENDING'
            )
            db.session.add(req)
            db.session.commit()

        with self.client.session_transaction() as sess:
            sess['user_id'] = self.patient_id
            sess['user_role'] = 'PATIENT'

        # Check pending blocks
        res = self.client.post('/submit', data={
            'Full_name': 'Test Patient',
            'Phone_number': '9876543210',
            'Shipping_address': 'Test Address',
            'Medication': ['Amoxicillin 500mg'],
            'Quantity': ['1']
        }, follow_redirects=True)
        with self.app.app_context():
            self.assertIsNone(Order.query.filter_by(full_name='Test Patient').first())

        # Check rejected blocks
        with self.app.app_context():
            req = MedicineApprovalRequest.query.first()
            req.status = 'REJECTED'
            req.rejection_reason = 'Contraindicated'
            db.session.commit()

        res = self.client.post('/submit', data={
            'Full_name': 'Test Patient',
            'Phone_number': '9876543210',
            'Shipping_address': 'Test Address',
            'Medication': ['Amoxicillin 500mg'],
            'Quantity': ['1']
        }, follow_redirects=True)
        with self.app.app_context():
            self.assertIsNone(Order.query.filter_by(full_name='Test Patient').first())

    def test_doctor_approval_permits_purchase_and_enforces_quantity(self):
        """6 & 8 & 10. Doctor approval permits purchase and enforces authorized quantity limits."""
        with self.app.app_context():
            req = MedicineApprovalRequest(
                patient_id=self.patient_id,
                medicine_id=self.rx_med_id,
                doctor_id=self.doctor_id,
                quantity_requested=5,
                quantity_approved=5,
                quantity_used=0,
                status='APPROVED',
                valid_until=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(req)
            db.session.commit()

        with self.client.session_transaction() as sess:
            sess['user_id'] = self.patient_id
            sess['user_role'] = 'PATIENT'

        # Attempt to order more than approved (qty 6 > 5 authorized)
        res = self.client.post('/submit', data={
            'Full_name': 'Test Patient',
            'Phone_number': '9876543210',
            'Shipping_address': 'Test Address',
            'Medication': ['Amoxicillin 500mg'],
            'Quantity': ['6']
        }, follow_redirects=True)
        with self.app.app_context():
            self.assertIsNone(Order.query.filter_by(full_name='Test Patient').first())

        # Order within approved quantity (qty 3 of 5)
        res = self.client.post('/submit', data={
            'Full_name': 'Test Patient',
            'Phone_number': '9876543210',
            'Shipping_address': 'Test Address',
            'Medication': ['Amoxicillin 500mg'],
            'Quantity': ['3']
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            order = Order.query.filter_by(full_name='Test Patient').first()
            self.assertIsNotNone(order)
            self.assertEqual(order.total_amount, 360.0)

            # Check approval quantity_used was updated
            req = MedicineApprovalRequest.query.first()
            self.assertEqual(req.quantity_used, 3)
            self.assertEqual(req.remaining_authorized_quantity(), 2)

    def test_unauthorized_user_cannot_approve_request(self):
        """7. A non-doctor/patient cannot approve a prescription request."""
        with self.app.app_context():
            req = MedicineApprovalRequest(
                patient_id=self.patient_id,
                medicine_id=self.rx_med_id,
                doctor_id=self.doctor_id,
                quantity_requested=2,
                status='PENDING'
            )
            db.session.add(req)
            db.session.commit()
            req_id = req.id

        with self.client.session_transaction() as sess:
            sess['user_id'] = self.patient_id
            sess['user_role'] = 'PATIENT'

        res = self.client.post(f'/doctor/prescription-request/{req_id}/decision', data={
            'decision': 'APPROVE',
            'quantity_approved': 2
        })
        # Role required decorator returns 403 Forbidden
        self.assertEqual(res.status_code, 403)

if __name__ == '__main__':
    unittest.main()
