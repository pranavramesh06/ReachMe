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
    clinical_notes = db.relationship('ConsultationNote', backref='author_doctor', lazy='dynamic')
    feedbacks = db.relationship('PatientFeedback', backref='doctor', lazy='dynamic')

    def update_rating_average(self):
        all_feedback = PatientFeedback.query.filter_by(doctor_id=self.id).all()
        if all_feedback:
            avg = sum(f.rating for f in all_feedback) / len(all_feedback)
            self.rating = round(avg, 2)
            db.session.commit()

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

class ConsultationNote(db.Model):
    __tablename__ = 'consultation_notes'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='RESTRICT'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    # Private clinical notes (for clinicians only)
    clinical_summary = db.Column(db.Text, nullable=True)
    symptoms_observations = db.Column(db.Text, nullable=True)
    clinical_assessment = db.Column(db.Text, nullable=True)
    private_recommendations = db.Column(db.Text, nullable=True)

    # Patient-facing consultation summary (explicitly shareable)
    patient_advice = db.Column(db.Text, nullable=True)
    recommended_followup = db.Column(db.Text, nullable=True)
    followup_date = db.Column(db.String(20), nullable=True)  # YYYY-MM-DD
    is_shared_with_patient = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    appointment = db.relationship('Appointment', backref=db.backref('clinical_note', uselist=False))
    patient = db.relationship('User', foreign_keys=[patient_id], backref='consultation_notes')

    def to_patient_dict(self):
        """Only returns shareable patient-facing feedback"""
        if not self.is_shared_with_patient:
            return None
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'doctor_name': self.author_doctor.name if self.author_doctor else 'Doctor',
            'patient_advice': self.patient_advice,
            'recommended_followup': self.recommended_followup,
            'followup_date': self.followup_date,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else ''
        }

    def to_clinical_dict(self):
        """Complete clinical record for doctors only"""
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'doctor_id': self.doctor_id,
            'patient_id': self.patient_id,
            'clinical_summary': self.clinical_summary,
            'symptoms_observations': self.symptoms_observations,
            'clinical_assessment': self.clinical_assessment,
            'private_recommendations': self.private_recommendations,
            'patient_advice': self.patient_advice,
            'recommended_followup': self.recommended_followup,
            'followup_date': self.followup_date,
            'is_shared_with_patient': self.is_shared_with_patient,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else ''
        }

class PatientFeedback(db.Model):
    __tablename__ = 'patient_feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    rating = db.Column(db.Integer, nullable=False)  # 1 to 5 stars
    feedback_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    appointment = db.relationship('Appointment', backref=db.backref('patient_feedback', uselist=False))
    patient = db.relationship('User', foreign_keys=[patient_id], backref='given_feedbacks')

    def to_dict(self):
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'doctor_id': self.doctor_id,
            'patient_name': self.patient.full_name if self.patient else 'Patient',
            'rating': self.rating,
            'feedback_text': self.feedback_text,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }
