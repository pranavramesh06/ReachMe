from datetime import datetime, date
from sqlalchemy import func
from app.models import db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.medicine import Medicine
from app.models.order import Order, OrderItem
from app.models.appointment import Appointment
from app.models.ambulance import EmergencyRequest
from app.models.prescription import Prescription

def get_dashboard_analytics():
    """
    Retrieves dynamic, database-driven healthcare analytics.
    All figures are generated dynamically from PostgreSQL.
    """
    total_patients = User.query.filter_by(role='PATIENT').count()
    total_doctors = Doctor.query.count()
    
    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    appointments_today = Appointment.query.filter(Appointment.appointment_date == today_str).count()
    total_appointments = Appointment.query.count()
    
    pending_orders = Order.query.filter_by(status='PROCESSING').count()
    total_orders = Order.query.count()
    
    total_revenue = db.session.query(func.sum(Order.total_amount)).scalar() or 0.0
    
    low_stock_medicines = Medicine.query.filter(Medicine.stock_quantity < 20).all()
    emergency_requests = EmergencyRequest.query.count()
    active_emergencies = EmergencyRequest.query.filter(
        EmergencyRequest.status.in_(['REQUESTED', 'ACKNOWLEDGED', 'EN_ROUTE'])
    ).count()

    # Top ordered medicines calculation
    top_medicines = db.session.query(
        OrderItem.medicine_name,
        func.sum(OrderItem.quantity).label('total_qty')
    ).group_by(OrderItem.medicine_name).order_by(func.sum(OrderItem.quantity).desc()).limit(5).all()

    top_meds_list = [{'name': name, 'quantity': int(qty)} for name, qty in top_medicines]

    # Specialization demand distribution
    specialty_counts = db.session.query(
        Appointment.doctor_specialty,
        func.count(Appointment.id)
    ).group_by(Appointment.doctor_specialty).all()

    specialty_dist = [{'specialty': spec or 'General', 'count': count} for spec, count in specialty_counts]

    return {
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'appointments_today': appointments_today,
        'total_appointments': total_appointments,
        'pending_orders': pending_orders,
        'total_orders': total_orders,
        'total_revenue': round(total_revenue, 2),
        'low_stock_count': len(low_stock_medicines),
        'low_stock_medicines': [m.to_dict() for m in low_stock_medicines],
        'emergency_requests': emergency_requests,
        'active_emergencies': active_emergencies,
        'top_medicines': top_meds_list,
        'specialty_distribution': specialty_dist
    }
