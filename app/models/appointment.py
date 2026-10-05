from datetime import datetime
from app.models import db

class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    patient_name = db.Column(db.String(120), nullable=False)
    patient_phone = db.Column(db.String(30), nullable=False)
    problem_description = db.Column(db.Text, nullable=False)
    
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='RESTRICT'), nullable=False)
    doctor_name = db.Column(db.String(120), nullable=False)
    doctor_specialty = db.Column(db.String(120), nullable=True)
    
    appointment_date = db.Column(db.String(20), nullable=False, index=True) # YYYY-MM-DD
    time_slot = db.Column(db.String(20), nullable=False)        # HH:MM format
    
    status = db.Column(db.String(30), nullable=False, default='CONFIRMED') # CONFIRMED, COMPLETED, CANCELLED
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_name': self.patient_name,
            'patient_phone': self.patient_phone,
            'problem_description': self.problem_description,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor_name,
            'doctor_specialty': self.doctor_specialty,
            'appointment_date': self.appointment_date,
            'time_slot': self.time_slot,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }
