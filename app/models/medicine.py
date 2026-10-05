from datetime import datetime
from app.models import db

class MedicineCategory(db.Model):
    __tablename__ = 'medicine_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    medicines = db.relationship('Medicine', backref='category', lazy='dynamic')

class Medicine(db.Model):
    __tablename__ = 'medicines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('medicine_categories.id', ondelete='SET NULL'), nullable=True)
    price = db.Column(db.Float, nullable=False)  # INR
    stock_quantity = db.Column(db.Integer, nullable=False, default=100)
    dosage = db.Column(db.String(100), nullable=True, default='As directed by physician')
    description = db.Column(db.Text, nullable=True)
    requires_prescription = db.Column(db.Boolean, default=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order_items = db.relationship('OrderItem', backref='medicine', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'stock_quantity': self.stock_quantity,
            'dosage': self.dosage,
            'category': self.category.name if self.category else 'General',
            'requires_prescription': self.requires_prescription,
            'is_available': self.is_available
        }
