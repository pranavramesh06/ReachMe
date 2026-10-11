import math
from app.models import db
from app.models.ambulance import Ambulance, EmergencyRequest

EARTH_RADIUS_KM = 6371.0

def haversine_distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate geographic distance between two sets of coordinates using Haversine formula.
    Returns distance in kilometers.
    """
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c

def estimate_eta_minutes(distance_km, speed_kmh=40.0, traffic_factor=1.2):
    """
    Estimate simulated travel time in minutes based on distance and speed.
    Adds a configurable traffic factor (1.2x) for realistic urban response time.
    """
    if speed_kmh <= 0:
        speed_kmh = 40.0
    # Travel time (hrs) = distance / speed
    travel_time_hours = (distance_km / speed_kmh) * traffic_factor
    minutes = max(1, round(travel_time_hours * 60))
    return minutes

def validate_coordinates(lat, lon):
    """
    Validates that latitude and longitude are valid numbers within realistic bounds.
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return None, None
    if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
        return lat, lon
    return None, None

def allocate_nearest_ambulance(patient_lat, patient_lon):
    """
    Concurrently safe allocation of the nearest available ambulance.
    Filters available ambulances, calculates Haversine distance, and locks candidate.
    Returns: (assigned_ambulance, distance_km, eta_minutes) or (None, None, None)
    """
    plat, plon = validate_coordinates(patient_lat, patient_lon)
    if plat is None or plon is None:
        return None, None, None

    # Concurrency safe query with row-level lock where supported
    try:
        available_ambulances = (
            Ambulance.query
            .filter_by(status='AVAILABLE', is_active=True)
            .with_for_update()
            .all()
        )
    except Exception:
        # Fallback if DB dialect does not support with_for_update (e.g. SQLite in test)
        available_ambulances = (
            Ambulance.query
            .filter_by(status='AVAILABLE', is_active=True)
            .all()
        )

    if not available_ambulances:
        return None, None, None

    nearest_ambulance = None
    min_distance = float('inf')

    for amb in available_ambulances:
        dist = haversine_distance_km(plat, plon, amb.latitude, amb.longitude)
        if dist < min_distance:
            min_distance = dist
            nearest_ambulance = amb

    if not nearest_ambulance:
        return None, None, None

    # Reserve the ambulance immediately
    nearest_ambulance.status = 'ASSIGNED'
    eta = estimate_eta_minutes(min_distance, nearest_ambulance.simulated_speed_kmh or 40.0)

    return nearest_ambulance, min_distance, eta
