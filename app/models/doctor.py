from datetime import datetime
from app.models import db

class Specialization(db.Model):
    __tablename__ = 'specializations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    doctors = db.relationship('Doctor', backref='specialization_obj', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

class Doctor(db.Model):
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, unique=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    specialty = db.Column(db.String(120), nullable=False, index=True)  # Name string for easy search/display
    specialization_id = db.Column(db.Integer, db.ForeignKey('specializations.id', ondelete='SET NULL'), nullable=True)
    experience_years = db.Column(db.Integer, default=5)
    consultation_fee = db.Column(db.Float, default=500.0)
    bio = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Float, default=4.8)
    is_available = db.Column(db.Boolean, default=True)
    hospital_affinity = db.Column(db.String(150), default='ReachMe Virtual Care Network')

    availabilities = db.relationship('DoctorAvailability', backref='doctor', lazy='dynamic', cascade="all, delete-orphan")
    appointments = db.relationship('Appointment', backref='doctor', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'specialty': self.specialty,
            'experience_years': self.experience_years,
            'consultation_fee': self.consultation_fee,
            'rating': self.rating,
            'is_available': self.is_available,
            'bio': self.bio
        }

class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availabilities'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)  # Monday, Tuesday, etc.
    start_time = db.Column(db.String(10), nullable=False)    # e.g. "09:00"
    end_time = db.Column(db.String(10), nullable=False)      # e.g. "17:00"
    is_active = db.Column(db.Boolean, default=True)
