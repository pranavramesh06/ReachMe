from datetime import datetime, timedelta
from flask import render_template, session, request, redirect, url_for, flash, abort, jsonify
from app.routes import doctor_bp
from app.routes.auth import role_required
from app.models import db
from app.models.user import User
from app.models.doctor import Doctor, DoctorAvailability, ConsultationNote, PatientFeedback
from app.models.appointment import Appointment
from app.models.prescription import Prescription, MedicineApprovalRequest

def get_current_doctor():
    """Helper to fetch the authenticated doctor object with flexible resolution"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    doc = Doctor.query.filter_by(user_id=user_id).first()
    if not doc:
        user = db.session.get(User, user_id)
        if user and user.full_name:
            doc = Doctor.query.filter(Doctor.name.ilike(f"%{user.full_name}%")).first()
    if not doc and session.get('user_role') == 'ADMIN':
        doc = Doctor.query.first()
    return doc

@doctor_bp.route('/dashboard')
@role_required(['DOCTOR', 'ADMIN'])
def dashboard():
    doctor_obj = get_current_doctor()
    if not doctor_obj:
        flash('Doctor profile not found for this account.', 'danger')
        return redirect(url_for('main.index'))

    doc_id = doctor_obj.id

    # Filter parameter for appointments: all, today, upcoming, completed, cancelled
    tab = request.args.get('tab', 'overview')
    app_filter = request.args.get('filter', 'all')
    today_str = datetime.utcnow().strftime('%Y-%m-%d')

    base_apps_query = Appointment.query.filter_by(doctor_id=doc_id)

    today_appointments = base_apps_query.filter_by(appointment_date=today_str).order_by(Appointment.time_slot).all()
    upcoming_appointments = base_apps_query.filter(
        Appointment.appointment_date >= today_str,
        Appointment.status == 'CONFIRMED'
    ).order_by(Appointment.appointment_date, Appointment.time_slot).all()
    completed_appointments = base_apps_query.filter_by(status='COMPLETED').order_by(Appointment.appointment_date.desc()).all()
    cancelled_appointments = base_apps_query.filter_by(status='CANCELLED').order_by(Appointment.appointment_date.desc()).all()

    if app_filter == 'today':
        filtered_appointments = today_appointments
    elif app_filter == 'upcoming':
        filtered_appointments = upcoming_appointments
    elif app_filter == 'completed':
        filtered_appointments = completed_appointments
    elif app_filter == 'cancelled':
        filtered_appointments = cancelled_appointments
    else:
        filtered_appointments = base_apps_query.order_by(Appointment.appointment_date.desc(), Appointment.created_at.desc()).all()

    # Pending Prescription & Medicine Approvals Queue
    # Doctors can review requests assigned specifically to them, or unassigned requests across the network
    pending_approvals = MedicineApprovalRequest.query.filter(
        (MedicineApprovalRequest.doctor_id == doc_id) | (MedicineApprovalRequest.doctor_id == None),
        MedicineApprovalRequest.status == 'PENDING'
    ).order_by(MedicineApprovalRequest.created_at.desc()).all()

    # History of reviewed approvals
    reviewed_approvals = MedicineApprovalRequest.query.filter_by(doctor_id=doc_id).filter(
        MedicineApprovalRequest.status != 'PENDING'
    ).order_by(MedicineApprovalRequest.decision_timestamp.desc()).limit(20).all()

    # Clinical Notes & Feedbacks
    clinical_notes = ConsultationNote.query.filter_by(doctor_id=doc_id).order_by(ConsultationNote.created_at.desc()).all()
    feedbacks = PatientFeedback.query.filter_by(doctor_id=doc_id).order_by(PatientFeedback.created_at.desc()).all()
    availabilities = DoctorAvailability.query.filter_by(doctor_id=doc_id).order_by(DoctorAvailability.day_of_week).all()

    return render_template(
        'dashboards/doctor.html',
        doctor=doctor_obj,
        tab=tab,
        app_filter=app_filter,
        filtered_appointments=filtered_appointments,
        today_appointments=today_appointments,
        upcoming=upcoming_appointments,
        completed=completed_appointments,
        cancelled=cancelled_appointments,
        pending_approvals=pending_approvals,
        reviewed_approvals=reviewed_approvals,
        clinical_notes=clinical_notes,
        feedbacks=feedbacks,
        availabilities=availabilities
    )

@doctor_bp.route('/appointment/<int:app_id>/update', methods=['POST'])
@role_required(['DOCTOR', 'ADMIN'])
def update_appointment(app_id):
    appointment = Appointment.query.get_or_404(app_id)
    doc = get_current_doctor()

    # Ownership check: doctor can only manage their own appointments
    if session.get('user_role') != 'ADMIN' and appointment.doctor_id != doc.id:
        abort(403)

    new_status = request.form.get('status', 'CONFIRMED')
    if new_status in ['CONFIRMED', 'COMPLETED', 'CANCELLED']:
        appointment.status = new_status
        db.session.commit()
        flash(f'Appointment status updated to {new_status}.', 'success')
    return redirect(url_for('doctor.dashboard', tab='appointments'))

@doctor_bp.route('/prescription-request/<int:req_id>/decision', methods=['POST'])
@role_required(['DOCTOR', 'ADMIN'])
def review_prescription_request(req_id):
    approval_req = MedicineApprovalRequest.query.get_or_404(req_id)
    doc = get_current_doctor()

    # Ownership / authorization check
    if session.get('user_role') != 'ADMIN' and approval_req.doctor_id and approval_req.doctor_id != doc.id:
        abort(403)

    decision = request.form.get('decision', '').strip().upper()
    rejection_reason = request.form.get('rejection_reason', '').strip()
    valid_days = request.form.get('valid_days', 30, type=int)
    qty_approved = request.form.get('quantity_approved', type=int)

    if decision not in ['APPROVE', 'REJECT']:
        flash('Invalid decision selected.', 'danger')
        return redirect(url_for('doctor.dashboard', tab='prescriptions'))

    if decision == 'REJECT' and not rejection_reason:
        flash('Please provide a clinical reason when rejecting a prescription request.', 'warning')
        return redirect(url_for('doctor.dashboard', tab='prescriptions'))

    approval_req.doctor_id = doc.id
    approval_req.decision_timestamp = datetime.utcnow()

    if decision == 'APPROVE':
        approval_req.status = 'APPROVED'
        approval_req.rejection_reason = None
        approval_req.quantity_approved = qty_approved if qty_approved and qty_approved > 0 else approval_req.quantity_requested
        approval_req.valid_until = datetime.utcnow() + timedelta(days=max(1, valid_days))
        
        # If an associated prescription slip exists, mark it verified as well
        if approval_req.prescription:
            approval_req.prescription.status = 'APPROVED'
            approval_req.prescription.reviewed_by_doctor_id = doc.id
            approval_req.prescription.reviewed_at = datetime.utcnow()
            approval_req.prescription.valid_until = approval_req.valid_until

        flash(f'Approved prescription purchase for {approval_req.medicine.name} (Valid for {valid_days} days).', 'success')
    else:
        approval_req.status = 'REJECTED'
        approval_req.rejection_reason = rejection_reason
        if approval_req.prescription:
            approval_req.prescription.status = 'REJECTED'
            approval_req.prescription.reviewed_by_doctor_id = doc.id
            approval_req.prescription.reviewed_at = datetime.utcnow()
            approval_req.prescription.rejection_reason = rejection_reason

        flash(f'Prescription request rejected with clinical feedback.', 'info')

    db.session.commit()
    return redirect(url_for('doctor.dashboard', tab='prescriptions'))

@doctor_bp.route('/appointment/<int:app_id>/notes', methods=['POST'])
@role_required(['DOCTOR', 'ADMIN'])
def save_consultation_notes(app_id):
    appointment = Appointment.query.get_or_404(app_id)
    doc = get_current_doctor()

    # Ownership check
    if session.get('user_role') != 'ADMIN' and appointment.doctor_id != doc.id:
        abort(403)

    # Fetch or create note
    note = ConsultationNote.query.filter_by(appointment_id=app_id).first()
    if not note:
        note = ConsultationNote(
            appointment_id=app_id,
            doctor_id=doc.id,
            patient_id=appointment.patient_id
        )
        db.session.add(note)

    # Private clinical notes
    note.clinical_summary = request.form.get('clinical_summary', '').strip()
    note.symptoms_observations = request.form.get('symptoms_observations', '').strip()
    note.clinical_assessment = request.form.get('clinical_assessment', '').strip()
    note.private_recommendations = request.form.get('private_recommendations', '').strip()

    # Shareable patient advice
    note.patient_advice = request.form.get('patient_advice', '').strip()
    note.recommended_followup = request.form.get('recommended_followup', '').strip()
    note.followup_date = request.form.get('followup_date', '').strip()
    note.is_shared_with_patient = ('is_shared_with_patient' in request.form)

    # Auto-complete appointment if doctor saves final consultation notes
    if appointment.status == 'CONFIRMED' and request.form.get('mark_completed'):
        appointment.status = 'COMPLETED'

    db.session.commit()
    flash('Consultation notes saved securely.', 'success')
    return redirect(url_for('doctor.dashboard', tab='notes'))

@doctor_bp.route('/availability/save', methods=['POST'])
@role_required(['DOCTOR', 'ADMIN'])
def save_availability():
    doc = get_current_doctor()
    day_of_week = request.form.get('day_of_week', '').strip()
    start_time = request.form.get('start_time', '').strip()
    end_time = request.form.get('end_time', '').strip()

    if not day_of_week or not start_time or not end_time:
        flash('Please fill day, start time, and end time.', 'warning')
        return redirect(url_for('doctor.dashboard', tab='availability'))

    # Check for duplicate slot on same day
    existing = DoctorAvailability.query.filter_by(
        doctor_id=doc.id,
        day_of_week=day_of_week,
        start_time=start_time
    ).first()

    if existing:
        flash('A slot starting at this time already exists.', 'warning')
    else:
        new_slot = DoctorAvailability(
            doctor_id=doc.id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            is_active=True
        )
        db.session.add(new_slot)
        db.session.commit()
        flash('Availability slot registered successfully.', 'success')

    return redirect(url_for('doctor.dashboard', tab='availability'))

@doctor_bp.route('/availability/<int:slot_id>/delete', methods=['POST'])
@role_required(['DOCTOR', 'ADMIN'])
def delete_availability(slot_id):
    slot = DoctorAvailability.query.get_or_404(slot_id)
    doc = get_current_doctor()
    if session.get('user_role') != 'ADMIN' and slot.doctor_id != doc.id:
        abort(403)

    db.session.delete(slot)
    db.session.commit()
    flash('Availability slot removed.', 'info')
    return redirect(url_for('doctor.dashboard', tab='availability'))
