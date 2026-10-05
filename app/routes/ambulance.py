from flask import render_template, request, jsonify, session
from app.routes import ambulance_bp
from app.models import db
from app.models.ambulance import EmergencyRequest

@ambulance_bp.route('/call-ambulance')
def call_ambulance():
    requests_history = []
    user_id = session.get('user_id')
    if user_id:
        requests_history = EmergencyRequest.query.filter_by(patient_id=user_id).order_by(EmergencyRequest.created_at.desc()).all()
    return render_template('ambulance/request.html', requests_history=requests_history)

@ambulance_bp.route('/submitAmbulanceRequest', methods=['POST'])
def submit_ambulance_request():
    if request.is_json:
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')
        emergency = data.get('emergency')
        location = data.get('location')
    else:
        name = request.form.get('name')
        phone = request.form.get('phone')
        emergency = request.form.get('emergency')
        location = request.form.get('location')

    if not name or not phone or not emergency or not location:
        return jsonify({'error': 'Please fill all required emergency fields.'}), 400

    user_id = session.get('user_id')

    # Determine priority tier based on emergency description
    emergency_lower = emergency.lower()
    if any(k in emergency_lower for k in ['heart', 'stroke', 'unconscious', 'bleeding', 'accident', 'breath']):
        priority = 'CRITICAL'
        eta = 3
    else:
        priority = 'HIGH'
        eta = 5

    req = EmergencyRequest(
        patient_id=user_id,
        patient_name=name,
        patient_phone=phone,
        emergency_type=emergency,
        location_address=location,
        priority=priority,
        status='ACKNOWLEDGED',
        eta_minutes=eta,
        assigned_vehicle='ReachMe Rapid Response Ambulance #104',
        is_simulation=True
    )
    db.session.add(req)
    db.session.commit()

    response_message = f"SIMULATION DEMO: Emergency request acknowledged! Ambulance Unit #104 dispatched. ETA: ~{eta} mins to {location}."

    return jsonify({
        'success': True,
        'request_id': req.id,
        'message': response_message,
        'status': req.status,
        'eta_minutes': eta,
        'vehicle': req.assigned_vehicle,
        'is_simulation': True,
        'disclaimer': 'DEMO SIMULATION ONLY: In real medical emergencies, dial local emergency services (108 / 911).'
    })

@ambulance_bp.route('/ambulance/status/<int:req_id>')
def check_status(req_id):
    req = EmergencyRequest.query.get_or_404(req_id)
    
    # Progress simulation state machine based on seconds elapsed
    from datetime import datetime
    elapsed_seconds = (datetime.utcnow() - req.created_at).total_seconds()
    
    if elapsed_seconds > 180:
        req.status = 'ARRIVED'
        req.eta_minutes = 0
    elif elapsed_seconds > 60:
        req.status = 'EN_ROUTE'
        req.eta_minutes = max(1, req.eta_minutes - 1)
    elif elapsed_seconds > 10:
        req.status = 'ACKNOWLEDGED'
        
    db.session.commit()
    
    return jsonify(req.to_dict())
