from flask import render_template, session, request, redirect, url_for, flash
from app.routes import doctor_bp
from app.routes.auth import role_required
from app.models import db
from app.models.doctor import Doctor, DoctorAvailability
from app.models.appointment import Appointment

@doctor_bp.route('/dashboard')
@role_required(['DOCTOR', 'ADMIN'])
def dashboard():
    doc = Doctor.query.filter_by(user_id=session['user_id']).first()
    if not doc:
        user = db.session.get(User, session['user_id'])
        if user and user.full_name:
            doc = Doctor.query.filter(Doctor.name.ilike(f"%{user.full_name}%")).first()
        if not doc:
            doc = Doctor.query.first()

    if not doc and session.get('user_role') != 'ADMIN':
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('main.index'))

    doc_id = doc.id if doc else Doctor.query.first().id
    doctor_obj = doc if doc else Doctor.query.first()

    appointments = Appointment.query.filter_by(doctor_id=doc_id).order_by(Appointment.created_at.desc()).all()
    upcoming = [a for a in appointments if a.status == 'CONFIRMED']
    completed = [a for a in appointments if a.status == 'COMPLETED']

    return render_template(
        'dashboards/doctor.html',
        doctor=doctor_obj,
        appointments=appointments,
        upcoming=upcoming,
        completed=completed
    )

@doctor_bp.route('/appointment/<int:app_id>/update', methods=['POST'])
@role_required(['DOCTOR', 'ADMIN'])
def update_appointment(app_id):
    appointment = Appointment.query.get_or_404(app_id)
    new_status = request.form.get('status', 'CONFIRMED')
    if new_status in ['CONFIRMED', 'COMPLETED', 'CANCELLED']:
        appointment.status = new_status
        db.session.commit()
        flash(f'Appointment status updated to {new_status}.', 'success')
    return redirect(url_for('doctor.dashboard'))
