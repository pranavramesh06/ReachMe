from flask import render_template, session
from app.routes import patient_bp
from app.routes.auth import login_required
from app.models import db
from app.models.user import User
from app.models.order import Order
from app.models.appointment import Appointment
from app.models.prescription import Prescription
from app.models.triage import TriageRecommendation

@patient_bp.route('/dashboard')
@login_required
def dashboard():
    user = db.session.get(User, session['user_id'])
    
    # Query user-specific appointments or match by phone/name
    appointments = Appointment.query.filter(
        (Appointment.patient_id == user.id) | (Appointment.patient_phone == user.phone)
    ).order_by(Appointment.created_at.desc()).limit(5).all()

    # Query user-specific orders
    orders = Order.query.filter(
        (Order.user_id == user.id) | (Order.phone_number == user.phone)
    ).order_by(Order.created_at.desc()).limit(5).all()

    # Query prescriptions
    prescriptions = Prescription.query.filter_by(patient_id=user.id).order_by(Prescription.uploaded_at.desc()).limit(5).all()

    # Query recent triage recommendations
    triage_history = TriageRecommendation.query.filter_by(user_id=user.id).order_by(TriageRecommendation.created_at.desc()).limit(3).all()

    return render_template(
        'dashboards/patient.html',
        user=user,
        appointments=appointments,
        orders=orders,
        prescriptions=prescriptions,
        triage_history=triage_history
    )
