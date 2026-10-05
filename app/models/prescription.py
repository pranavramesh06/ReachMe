from datetime import datetime
from app.models import db

class Prescription(db.Model):
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    patient_name = db.Column(db.String(120), nullable=True)
    filename = db.Column(db.String(256), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    
    raw_ocr_text = db.Column(db.Text, nullable=True)
    verified_medications_json = db.Column(db.Text, nullable=True)  # JSON string of structured verified meds
    
    status = db.Column(db.String(30), default='PENDING_VERIFICATION')  # PENDING_VERIFICATION, VERIFIED, REJECTED
    verification_notes = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_name': self.patient_name,
            'filename': self.filename,
            'raw_ocr_text': self.raw_ocr_text,
            'status': self.status,
            'uploaded_at': self.uploaded_at.strftime('%Y-%m-%d %H:%M')
        }
