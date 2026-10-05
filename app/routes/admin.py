from flask import render_template, request, redirect, url_for, flash
from app.routes import admin_bp
from app.routes.auth import role_required
from app.models import db
from app.models.user import User
from app.models.doctor import Doctor, Specialization
from app.models.medicine import Medicine, MedicineCategory
from app.models.order import Order
from app.models.appointment import Appointment
from app.models.ambulance import EmergencyRequest
from app.services.analytics_service import get_dashboard_analytics

@admin_bp.route('/dashboard')
@role_required(['ADMIN'])
def dashboard():
    stats = get_dashboard_analytics()
    users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(10).all()
    medicines = Medicine.query.order_by(Medicine.name).all()
    doctors = Doctor.query.order_by(Doctor.name).all()
    emergencies = EmergencyRequest.query.order_by(EmergencyRequest.created_at.desc()).limit(10).all()

    return render_template(
        'dashboards/admin.html',
        stats=stats,
        users=users,
        recent_orders=recent_orders,
        recent_appointments=recent_appointments,
        medicines=medicines,
        doctors=doctors,
        emergencies=emergencies
    )

@admin_bp.route('/medicine/add', methods=['POST'])
@role_required(['ADMIN'])
def add_medicine():
    name = request.form.get('name', '').strip()
    price = float(request.form.get('price', 0))
    stock = int(request.form.get('stock_quantity', 100))
    dosage = request.form.get('dosage', 'Standard dosage')
    category_name = request.form.get('category', 'General Care')

    if not name or price <= 0:
        flash('Valid medicine name and price are required.', 'danger')
        return redirect(url_for('admin.dashboard'))

    cat = MedicineCategory.query.filter_by(name=category_name).first()
    if not cat:
        cat = MedicineCategory(name=category_name)
        db.session.add(cat)
        db.session.flush()

    medicine = Medicine(
        name=name,
        price=price,
        stock_quantity=stock,
        dosage=dosage,
        category_id=cat.id,
        is_available=True
    )
    db.session.add(medicine)
    db.session.commit()
    flash(f'Medicine "{name}" added to inventory.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/order/<int:order_id>/status', methods=['POST'])
@role_required(['ADMIN'])
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status in ['PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED']:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.id} status updated to {new_status}.', 'success')
    return redirect(url_for('admin.dashboard'))
