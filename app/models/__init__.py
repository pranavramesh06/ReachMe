from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Ensure all models are imported and registered with SQLAlchemy metadata
from app.models.user import User, PatientProfile
from app.models.doctor import Doctor, Specialization, DoctorAvailability, ConsultationNote, PatientFeedback
from app.models.medicine import Medicine, MedicineCategory
from app.models.order import Order, OrderItem
from app.models.appointment import Appointment
from app.models.prescription import Prescription, MedicineApprovalRequest
from app.models.ambulance import Ambulance, EmergencyRequest
from app.models.triage import TriageRecommendation, AuditLog
