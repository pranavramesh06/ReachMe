from flask import render_template, session, request, redirect, url_for, flash
from app.routes import patient_bp
from app.routes.auth import login_required
from app.models import db
from app.models.user import User
from app.models.order import Order
from app.models.appointment import Appointment
from app.models.prescription import Prescription, MedicineApprovalRequest
from app.models.triage import TriageRecommendation
from app.models.ambulance import EmergencyRequest
from app.models.doctor import ConsultationNote, PatientFeedback

@patient_bp.route('/dashboard')
@login_required
def dashboard():
    user = db.session.get(User, session['user_id'])
    
    # Query user-specific appointments
    appointments = Appointment.query.filter(
        (Appointment.patient_id == user.id) | (Appointment.patient_phone == user.phone)
    ).order_by(Appointment.created_at.desc()).limit(10).all()

    # Query user-specific orders
    orders = Order.query.filter(
        (Order.user_id == user.id) | (Order.phone_number == user.phone)
    ).order_by(Order.created_at.desc()).limit(10).all()

    # Query uploaded prescriptions
    prescriptions = Prescription.query.filter_by(patient_id=user.id).order_by(Prescription.uploaded_at.desc()).limit(10).all()

    # Query requested medicine approvals
    medicine_approvals = MedicineApprovalRequest.query.filter_by(patient_id=user.id).order_by(MedicineApprovalRequest.created_at.desc()).all()

    # Query recent triage recommendations
    triage_history = TriageRecommendation.query.filter_by(user_id=user.id).order_by(TriageRecommendation.created_at.desc()).limit(5).all()

    # Query patient's emergency requests
    emergency_history = EmergencyRequest.query.filter_by(patient_id=user.id).order_by(EmergencyRequest.created_at.desc()).limit(5).all()

    # Query doctor-shared consultation notes for this patient
    shared_notes = (
        ConsultationNote.query
        .filter_by(patient_id=user.id, is_shared_with_patient=True)
        .order_by(ConsultationNote.created_at.desc())
        .all()
    )

    return render_template(
        'dashboards/patient.html',
        user=user,
        appointments=appointments,
        orders=orders,
        prescriptions=prescriptions,
        medicine_approvals=medicine_approvals,
        triage_history=triage_history,
        emergency_history=emergency_history,
        shared_notes=shared_notes
    )

@patient_bp.route('/appointment/<int:app_id>/feedback', methods=['POST'])
@login_required
def submit_feedback(app_id):
    user_id = session.get('user_id')
    appointment = Appointment.query.get_or_404(app_id)

    # Authorization: check patient owns the appointment
    if appointment.patient_id and appointment.patient_id != user_id:
        flash('Unauthorized to review this appointment.', 'danger')
        return redirect(url_for('patient.dashboard'))

    # Appointment must be completed
    if appointment.status != 'COMPLETED':
        flash('Feedback can only be submitted for completed consultations.', 'warning')
        return redirect(url_for('patient.dashboard'))

    # Prevent duplicate reviews
    existing = PatientFeedback.query.filter_by(appointment_id=app_id).first()
    if existing:
        flash('You have already submitted feedback for this consultation.', 'info')
        return redirect(url_for('patient.dashboard'))

    rating = request.form.get('rating', type=int)
    feedback_text = request.form.get('feedback_text', '').strip()

    if not rating or rating < 1 or rating > 5:
        flash('Please select a star rating between 1 and 5.', 'warning')
        return redirect(url_for('patient.dashboard'))

    feedback = PatientFeedback(
        appointment_id=app_id,
        doctor_id=appointment.doctor_id,
        patient_id=user_id,
        rating=rating,
        feedback_text=feedback_text
    )
    db.session.add(feedback)
    db.session.commit()

    # Update doctor's cumulative rating average
    if appointment.doctor:
        appointment.doctor.update_rating_average()

    flash('Thank you for submitting your consultation feedback!', 'success')
    return redirect(url_for('patient.dashboard'))
