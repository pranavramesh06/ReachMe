from datetime import datetime, timedelta
from app.models import db

class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    patient_name = db.Column(db.String(120), nullable=True)
    filename = db.Column(db.String(256), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    
    raw_ocr_text = db.Column(db.Text, nullable=True)
    verified_medications_json = db.Column(db.Text, nullable=True)  # JSON string of structured verified meds
    
    # Review / Clinical Approval fields
    status = db.Column(db.String(30), default='PENDING_REVIEW', index=True)  # PENDING_REVIEW, APPROVED, REJECTED
    reviewed_by_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='SET NULL'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    verification_notes = db.Column(db.Text, nullable=True)
    valid_until = db.Column(db.DateTime, nullable=True)
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    patient = db.relationship('User', foreign_keys=[patient_id], backref='uploaded_prescriptions')
    reviewing_doctor = db.relationship('Doctor', foreign_keys=[reviewed_by_doctor_id], backref='reviewed_prescriptions')
    approval_requests = db.relationship('MedicineApprovalRequest', backref='prescription', lazy='dynamic', cascade='all, delete-orphan')

    def is_valid_for_purchase(self):
        if self.status != 'APPROVED':
            return False
        if self.valid_until and self.valid_until < datetime.utcnow():
            return False
        return True

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'filename': self.filename,
            'file_path': self.file_path,
            'raw_ocr_text': self.raw_ocr_text,
            'status': self.status,
            'reviewed_by_doctor_id': self.reviewed_by_doctor_id,
            'rejection_reason': self.rejection_reason,
            'valid_until': self.valid_until.strftime('%Y-%m-%d') if self.valid_until else None,
            'uploaded_at': self.uploaded_at.strftime('%Y-%m-%d %H:%M')
        }

class MedicineApprovalRequest(db.Model):
    __tablename__ = 'medicine_approval_requests'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id', ondelete='CASCADE'), nullable=False, index=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id', ondelete='SET NULL'), nullable=True, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='SET NULL'), nullable=True, index=True)
    
    quantity_requested = db.Column(db.Integer, nullable=False, default=1)
    quantity_approved = db.Column(db.Integer, nullable=True)
    quantity_used = db.Column(db.Integer, nullable=False, default=0)
    
    clinical_notes = db.Column(db.Text, nullable=True)      # Reason or patient symptoms
    status = db.Column(db.String(30), nullable=False, default='PENDING', index=True)  # PENDING, APPROVED, REJECTED, EXPIRED
    rejection_reason = db.Column(db.Text, nullable=True)
    
    valid_until = db.Column(db.DateTime, nullable=True)
    decision_timestamp = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    patient = db.relationship('User', foreign_keys=[patient_id], backref='medicine_approval_requests')
    medicine = db.relationship('Medicine', foreign_keys=[medicine_id], backref='approval_requests')
    doctor = db.relationship('Doctor', foreign_keys=[doctor_id], backref='handled_approval_requests')

    def remaining_authorized_quantity(self):
        approved = self.quantity_approved if self.quantity_approved is not None else self.quantity_requested
        return max(0, approved - (self.quantity_used or 0))

    def is_currently_valid(self):
        if self.status != 'APPROVED':
            return False
        if self.valid_until and self.valid_until < datetime.utcnow():
            return False
        if self.remaining_authorized_quantity() <= 0:
            return False
        return True

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.full_name if self.patient else 'Unknown',
            'medicine_id': self.medicine_id,
            'medicine_name': self.medicine.name if self.medicine else 'Unknown',
            'prescription_id': self.prescription_id,
            'doctor_id': self.doctor_id,
            'doctor_name': self.doctor.name if self.doctor else 'Unassigned',
            'quantity_requested': self.quantity_requested,
            'quantity_approved': self.quantity_approved,
            'quantity_used': self.quantity_used,
            'remaining_quantity': self.remaining_authorized_quantity(),
            'status': self.status,
            'rejection_reason': self.rejection_reason,
            'valid_until': self.valid_until.strftime('%Y-%m-%d') if self.valid_until else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }
