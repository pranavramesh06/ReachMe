import unittest
from app import create_app
from config import TestingConfig
from app.models import db
from app.models.medicine import Medicine, MedicineCategory
from app.models.order import Order
class MedicineTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            cat = MedicineCategory.query.filter_by(name='General Care').first()
            if not cat:
                cat = MedicineCategory(name='General Care')
                db.session.add(cat)
                db.session.flush()
            med = Medicine.query.filter_by(name='Paracetamol').first()
            if not med:
                med = Medicine(name='Paracetamol', price=20.0, stock_quantity=100, category_id=cat.id)
                db.session.add(med)
            else:
                med.stock_quantity = 100
                med.price = 20.0
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_order_submission_and_price_validation(self):
        res = self.client.post('/submit', data={
            'Full_name': 'Test Buyer',
            'Phone_number': '1234567890',
            'Shipping_address': 'VIT Vellore',
            'Medication': ['Paracetamol'],
            'Quantity': ['2']
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        with self.app.app_context():
            order = Order.query.filter_by(full_name='Test Buyer').first()
            self.assertIsNotNone(order)
            self.assertEqual(order.total_amount, 40.0)
            
            med = Medicine.query.filter_by(name='Paracetamol').first()
            self.assertEqual(med.stock_quantity, 98)

if __name__ == '__main__':
    unittest.main()
