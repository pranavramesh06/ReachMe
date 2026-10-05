from datetime import datetime
from app.models import db

class TriageRecommendation(db.Model):
    __tablename__ = 'triage_recommendations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    patient_name = db.Column(db.String(120), nullable=True)
    symptoms_input = db.Column(db.Text, nullable=False)
    
    urgency_level = db.Column(db.String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, ROUTINE
    risk_score = db.Column(db.Float, nullable=False)           # Percentage 0 - 100
    
    recommended_specialization = db.Column(db.String(120), nullable=False)
    recommended_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='SET NULL'), nullable=True)
    recommended_doctor_name = db.Column(db.String(120), nullable=True)
    
    contributing_factors_json = db.Column(db.Text, nullable=False)  # JSON array of string factors
    recommended_action = db.Column(db.Text, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'symptoms_input': self.symptoms_input,
            'urgency_level': self.urgency_level,
            'risk_score': self.risk_score,
            'recommended_specialization': self.recommended_specialization,
            'recommended_doctor_name': self.recommended_doctor_name,
            'contributing_factors': json.loads(self.contributing_factors_json) if self.contributing_factors_json else [],
            'recommended_action': self.recommended_action,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
