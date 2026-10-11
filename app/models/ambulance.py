from datetime import datetime
from app.models import db

class Ambulance(db.Model):
    __tablename__ = 'ambulances'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_identifier = db.Column(db.String(50), unique=True, nullable=False, index=True) # e.g. AMB-CHN-01
    driver_name = db.Column(db.String(100), nullable=False)
    contact_phone = db.Column(db.String(30), nullable=False)
    
    # Geographic location
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    base_location_name = db.Column(db.String(120), nullable=False)
    
    # State & speed
    status = db.Column(db.String(30), default='AVAILABLE', index=True) # AVAILABLE, ASSIGNED, BUSY, MAINTENANCE
    simulated_speed_kmh = db.Column(db.Float, default=40.0) # Urban response speed
    is_active = db.Column(db.Boolean, default=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignments = db.relationship('EmergencyRequest', backref='assigned_ambulance_rel', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_identifier': self.vehicle_identifier,
            'driver_name': self.driver_name,
            'contact_phone': self.contact_phone,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'base_location_name': self.base_location_name,
            'status': self.status,
            'simulated_speed_kmh': self.simulated_speed_kmh,
            'is_simulation': True
        }

class EmergencyRequest(db.Model):
    __tablename__ = 'emergency_requests'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    patient_name = db.Column(db.String(120), nullable=False)
    patient_phone = db.Column(db.String(30), nullable=False)
    emergency_type = db.Column(db.String(120), nullable=False)
    location_address = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    # Allocation & Simulation results
    ambulance_id = db.Column(db.Integer, db.ForeignKey('ambulances.id', ondelete='SET NULL'), nullable=True, index=True)
    assigned_vehicle = db.Column(db.String(100), default='ReachMe Ambulance Unit #104')
    distance_km = db.Column(db.Float, nullable=True)
    eta_minutes = db.Column(db.Integer, default=5)
    
    priority = db.Column(db.String(20), default='HIGH')  # CRITICAL, HIGH, MEDIUM, LOW
    status = db.Column(db.String(30), default='REQUESTED', index=True)  # REQUESTED, ASSIGNED, EN_ROUTE, ARRIVED, COMPLETED, CANCELLED
    notes = db.Column(db.Text, nullable=True)
    is_simulation = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = db.relationship('User', foreign_keys=[patient_id], backref='emergency_requests')

    def to_dict(self):
        amb = self.assigned_ambulance_rel
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'patient_phone': self.patient_phone,
            'emergency_type': self.emergency_type,
            'location_address': self.location_address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'priority': self.priority,
            'status': self.status,
            'eta_minutes': self.eta_minutes,
            'distance_km': round(self.distance_km, 2) if self.distance_km is not None else None,
            'assigned_vehicle': self.assigned_vehicle,
            'ambulance_id': self.ambulance_id,
            'ambulance_lat': amb.latitude if amb else None,
            'ambulance_lng': amb.longitude if amb else None,
            'is_simulation': self.is_simulation,
            'disclaimer': 'DEMO SIMULATION ONLY: This does not dispatch a real emergency vehicle. Dial 108 / 911 for actual medical emergencies.',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
