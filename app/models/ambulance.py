from datetime import datetime
from app.models import db

class EmergencyRequest(db.Model):
    __tablename__ = 'emergency_requests'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    patient_name = db.Column(db.String(120), nullable=False)
    patient_phone = db.Column(db.String(30), nullable=False)
    emergency_type = db.Column(db.String(120), nullable=False)
    location_address = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    priority = db.Column(db.String(20), default='HIGH')  # CRITICAL, HIGH, MEDIUM, LOW
    status = db.Column(db.String(30), default='REQUESTED')  # REQUESTED, ACKNOWLEDGED, ASSIGNED, EN_ROUTE, ARRIVED, COMPLETED, CANCELLED
    eta_minutes = db.Column(db.Integer, default=5)
    assigned_vehicle = db.Column(db.String(100), default='ReachMe Ambulance Unit #104')
    notes = db.Column(db.Text, nullable=True)
    is_simulation = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_name': self.patient_name,
            'patient_phone': self.patient_phone,
            'emergency_type': self.emergency_type,
            'location_address': self.location_address,
            'priority': self.priority,
            'status': self.status,
            'eta_minutes': self.eta_minutes,
            'assigned_vehicle': self.assigned_vehicle,
            'is_simulation': self.is_simulation,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
