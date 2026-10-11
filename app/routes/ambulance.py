import re
from datetime import datetime
from flask import render_template, request, jsonify, session, abort
from app.routes import ambulance_bp
from app.models import db
from app.models.ambulance import Ambulance, EmergencyRequest
from app.services.ambulance_service import (
    haversine_distance_km,
    estimate_eta_minutes,
    validate_coordinates,
    allocate_nearest_ambulance
)

# Known demo coordinates for Tamil Nadu / Chennai landmarks when user enters text
DEMO_LANDMARKS = {
    'chennai central': (13.0827, 80.2707),
    'anna nagar': (13.0850, 80.2101),
    'adyar': (13.0012, 80.2565),
    'tambaram': (12.9249, 80.1000),
    't. nagar': (13.0418, 80.2341),
    't nagar': (13.0418, 80.2341),
    'guindy': (13.0067, 80.2021),
    'velachery': (12.9815, 80.2180),
    'vit vellore': (12.9698, 79.1559),
    'vellore': (12.9165, 79.1325)
}

def parse_location_string(location_str):
    """
    Parses location text to extract latitude and longitude.
    Handles 'Lat: 13.0827, Long: 80.2707' formats or known landmark names.
    """
    if not location_str:
        return None, None

    # Check for direct coordinates pattern
    match = re.search(r'[-+]?\d*\.\d+|\b[-+]?\d+\b', location_str)
    coords = re.findall(r'[-+]?\d+\.\d+', location_str)
    if len(coords) >= 2:
        return validate_coordinates(coords[0], coords[1])

    # Check known landmarks
    loc_lower = location_str.lower()
    for landmark, (lat, lon) in DEMO_LANDMARKS.items():
        if landmark in loc_lower:
            return lat, lon

    # Default fallback to Chennai Central demo coordinate
    return 13.0827, 80.2707

@ambulance_bp.route('/call-ambulance')
def call_ambulance():
    requests_history = []
    user_id = session.get('user_id')
    if user_id:
        requests_history = EmergencyRequest.query.filter_by(patient_id=user_id).order_by(EmergencyRequest.created_at.desc()).all()
    
    # Public simulated fleet locations (no sensitive patient data)
    ambulances = Ambulance.query.filter_by(is_active=True).all()
    
    return render_template(
        'ambulance/request.html',
        requests_history=requests_history,
        ambulances=[a.to_dict() for a in ambulances]
    )

@ambulance_bp.route('/api/fleet', methods=['GET'])
def get_fleet():
    """Returns the simulated fleet status and positions for map rendering"""
    ambulances = Ambulance.query.filter_by(is_active=True).all()
    return jsonify([a.to_dict() for a in ambulances])

@ambulance_bp.route('/submitAmbulanceRequest', methods=['POST'])
def submit_ambulance_request():
    if request.is_json:
        data = request.get_json() or {}
        name = data.get('name')
        phone = data.get('phone')
        emergency = data.get('emergency')
        location = data.get('location')
        req_lat = data.get('latitude')
        req_lon = data.get('longitude')
    else:
        name = request.form.get('name')
        phone = request.form.get('phone')
        emergency = request.form.get('emergency')
        location = request.form.get('location')
        req_lat = request.form.get('latitude')
        req_lon = request.form.get('longitude')

    if not name or not phone or not emergency or not location:
        return jsonify({'error': 'Please fill all required emergency fields.'}), 400

    # Parse and validate coordinates
    lat, lon = validate_coordinates(req_lat, req_lon)
    if lat is None or lon is None:
        lat, lon = parse_location_string(location)

    user_id = session.get('user_id')

    # Determine priority tier based on emergency clinical keywords
    emergency_lower = emergency.lower()
    if any(k in emergency_lower for k in ['heart', 'cardiac', 'stroke', 'unconscious', 'bleeding', 'accident', 'breath', 'severe']):
        priority = 'CRITICAL'
    else:
        priority = 'HIGH'

    # Concurrency-safe nearest ambulance allocation using Haversine algorithm
    allocated_amb, distance_km, eta_minutes = allocate_nearest_ambulance(lat, lon)

    if not allocated_amb:
        # Honest response when no vehicle is currently available
        req = EmergencyRequest(
            patient_id=user_id,
            patient_name=name,
            patient_phone=phone,
            emergency_type=emergency,
            location_address=location,
            latitude=lat,
            longitude=lon,
            priority=priority,
            status='REQUESTED',
            assigned_vehicle='None Available',
            notes='All simulated ambulances are currently assigned or unavailable.',
            is_simulation=True
        )
        db.session.add(req)
        db.session.commit()

        return jsonify({
            'success': False,
            'request_id': req.id,
            'no_ambulance_available': True,
            'message': 'No simulated ambulances are currently available in this sector. For real emergencies, please call 108 or 911 immediately.',
            'status': req.status,
            'is_simulation': True,
            'disclaimer': 'DEMO SIMULATION ONLY: This does not dispatch a real emergency vehicle.'
        }), 200

    # Create request with allocated ambulance
    req = EmergencyRequest(
        patient_id=user_id,
        patient_name=name,
        patient_phone=phone,
        emergency_type=emergency,
        location_address=location,
        latitude=lat,
        longitude=lon,
        ambulance_id=allocated_amb.id,
        assigned_vehicle=f"{allocated_amb.vehicle_identifier} ({allocated_amb.driver_name})",
        distance_km=distance_km,
        eta_minutes=eta_minutes,
        priority=priority,
        status='ASSIGNED',
        is_simulation=True
    )
    db.session.add(req)
    db.session.commit()

    return jsonify({
        'success': True,
        'request_id': req.id,
        'message': f"SIMULATION DEMO: Nearest unit {allocated_amb.vehicle_identifier} ({allocated_amb.base_location_name}) allocated! Distance: {round(distance_km, 2)} km, Estimated Arrival: ~{eta_minutes} mins.",
        'status': req.status,
        'eta_minutes': eta_minutes,
        'distance_km': round(distance_km, 2),
        'assigned_vehicle': req.assigned_vehicle,
        'ambulance_id': allocated_amb.id,
        'ambulance_lat': allocated_amb.latitude,
        'ambulance_lng': allocated_amb.longitude,
        'patient_lat': lat,
        'patient_lng': lon,
        'is_simulation': True,
        'disclaimer': 'DEMO SIMULATION ONLY: This does not contact real emergency services or dispatch a physical vehicle. Dial 108 / 911 for real medical emergencies.'
    })

@ambulance_bp.route('/ambulance/status/<int:req_id>')
def check_status(req_id):
    req = EmergencyRequest.query.get_or_404(req_id)
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    # Privacy & Access Control: patients can only track their own emergencies (unless admin)
    if req.patient_id and req.patient_id != user_id and user_role != 'ADMIN':
        abort(403)

    # Progress simulated state machine based on elapsed time:
    # REQUESTED -> ASSIGNED -> EN_ROUTE -> ARRIVED -> COMPLETED
    elapsed_seconds = (datetime.utcnow() - req.created_at).total_seconds()
    
    if req.status not in ['COMPLETED', 'CANCELLED'] and req.ambulance_id:
        if elapsed_seconds > 180:
            req.status = 'ARRIVED'
            req.eta_minutes = 0
            # Free up the ambulance after simulation completes
            if req.assigned_ambulance_rel and req.assigned_ambulance_rel.status == 'ASSIGNED':
                req.assigned_ambulance_rel.status = 'AVAILABLE'
        elif elapsed_seconds > 60:
            req.status = 'EN_ROUTE'
            if req.eta_minutes > 1:
                req.eta_minutes = max(1, req.eta_minutes - 1)
        elif elapsed_seconds > 5:
            req.status = 'ASSIGNED'
            
        db.session.commit()
    
    return jsonify(req.to_dict())
