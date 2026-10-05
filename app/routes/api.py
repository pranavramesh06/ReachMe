from flask import jsonify, request, session
from app.routes import api_bp
from app.models.doctor import Doctor
from app.models.medicine import Medicine
from app.models.appointment import Appointment
from app.models.order import Order
from app.services.analytics_service import get_dashboard_analytics
from app.services.triage_service import analyze_triage_symptoms

@api_bp.route('/doctors', methods=['GET'])
def get_doctors():
    specialty = request.args.get('specialty')
    query = Doctor.query.filter_by(is_available=True)
    if specialty:
        query = query.filter(Doctor.specialty.ilike(f"%{specialty}%"))
    doctors = query.all()
    return jsonify([d.to_dict() for d in doctors])

@api_bp.route('/medicines', methods=['GET'])
def get_medicines():
    search = request.args.get('q')
    query = Medicine.query.filter_by(is_available=True)
    if search:
        query = query.filter(Medicine.name.ilike(f"%{search}%"))
    medicines = query.all()
    return jsonify([m.to_dict() for m in medicines])

@api_bp.route('/dashboard', methods=['GET'])
def get_analytics():
    stats = get_dashboard_analytics()
    return jsonify(stats)

@api_bp.route('/triage', methods=['POST'])
def api_triage():
    data = request.get_json() or {}
    symptoms = data.get('symptoms', '')
    if not symptoms:
        return jsonify({'error': 'Symptoms input required'}), 400
    
    result = analyze_triage_symptoms(
        symptoms,
        severity=data.get('severity', 5),
        duration_days=data.get('duration', 1)
    )
    return jsonify(result)
