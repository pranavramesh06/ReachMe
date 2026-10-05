from flask import render_template, request, redirect, url_for, flash, session
from app.routes import consultation_bp
from app.models import db
from app.models.doctor import Doctor, Specialization
from app.models.appointment import Appointment

@consultation_bp.route('/consult')
def consult():
    search_query = request.args.get('search', '').strip()
    specialty_filter = request.args.get('specialty', '').strip()

    query = Doctor.query.filter_by(is_available=True)
    if search_query:
        query = query.filter(Doctor.name.ilike(f"%{search_query}%"))
    if specialty_filter:
        query = query.filter(Doctor.specialty.ilike(f"%{specialty_filter}%"))

    doctors = query.order_by(Doctor.rating.desc()).all()
    specializations = Specialization.query.order_by(Specialization.name).all()

    return render_template(
        'consult/doctors.html',
        doctors=doctors,
        specializations=specializations,
        search_query=search_query,
        selected_specialty=specialty_filter
    )

@consultation_bp.route('/submit-consult', methods=['POST'])
def submit_consult():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    problem = request.form.get('problem', '').strip()
    doctor_raw = request.form.get('doctor', '').strip()
    date_str = request.form.get('date', '').strip()
    time_slot = request.form.get('time_slot', '').strip()

    if not name or not phone or not problem or not doctor_raw or not date_str or not time_slot:
        flash('Please fill out all required fields to book an appointment.', 'danger')
        return redirect(url_for('consultation.consult'))

    # Parse doctor choice
    doc_name = doctor_raw.split(':')[0].strip() if ':' in doctor_raw else doctor_raw
    doctor = Doctor.query.filter(Doctor.name.ilike(f"%{doc_name}%")).first()

    if not doctor:
        doctor = Doctor.query.first()

    # Backend Double-Booking Check
    existing_booking = Appointment.query.filter_by(
        doctor_id=doctor.id,
        appointment_date=date_str,
        time_slot=time_slot,
        status='CONFIRMED'
    ).first()

    if existing_booking:
        flash(f'Dr. {doctor.name} is already booked at {time_slot} on {date_str}. Please select a different time slot.', 'warning')
        return redirect(url_for('consultation.consult'))

    user_id = session.get('user_id')

    appointment = Appointment(
        patient_id=user_id,
        patient_name=name,
        patient_phone=phone,
        problem_description=problem,
        doctor_id=doctor.id,
        doctor_name=doctor.name,
        doctor_specialty=doctor.specialty,
        appointment_date=date_str,
        time_slot=time_slot,
        status='CONFIRMED'
    )
    db.session.add(appointment)
    db.session.commit()

    return redirect(url_for('consultation.thankyou', name=name, doctor=doctor.name, date=date_str, time_slot=time_slot))

@consultation_bp.route('/thankyou')
def thankyou():
    name = request.args.get('name', 'Patient')
    doctor = request.args.get('doctor', 'Doctor')
    date = request.args.get('date', '')
    time_slot = request.args.get('time_slot', '')
    return render_template('consult/thankyou.html', name=name, doctor=doctor, date=date, time_slot=time_slot)

@consultation_bp.route('/appointment/<int:app_id>/cancel', methods=['POST'])
def cancel_appointment(app_id):
    app = Appointment.query.get_or_404(app_id)
    app.status = 'CANCELLED'
    db.session.commit()
    flash('Appointment cancelled successfully.', 'info')
    return redirect(request.referrer or url_for('patient.dashboard'))
