#!/usr/bin/env python
"""
Reset script for ReachMe simulated Chennai ambulance fleet.
Targeted and safe:
1. Resolves/completes existing test/demo simulation emergency requests.
2. Resets the 5 simulated ambulances (AMB-CHN-01 to AMB-CHN-05) to their intended coordinates,
   base location names, simulated speeds, and 'AVAILABLE' status.
3. Completely preserves all tables, users, doctors, medicines, orders, appointments, prescriptions,
   and historical emergency request records.
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

TARGET_AMBULANCE_FLEET = [
    {
        'vehicle_identifier': 'AMB-CHN-01',
        'driver_name': 'K. Rajesh (Unit #101)',
        'contact_phone': '+91 98401 22331',
        'latitude': 13.0827,
        'longitude': 80.2707,
        'base_location_name': 'Chennai Central (Park Town)',
        'simulated_speed_kmh': 42.0,
        'status': 'AVAILABLE',
        'is_active': True
    },
    {
        'vehicle_identifier': 'AMB-CHN-02',
        'driver_name': 'S. Murugan (Unit #102)',
        'contact_phone': '+91 98402 33442',
        'latitude': 13.0850,
        'longitude': 80.2101,
        'base_location_name': 'Anna Nagar West Depot',
        'simulated_speed_kmh': 38.0,
        'status': 'AVAILABLE',
        'is_active': True
    },
    {
        'vehicle_identifier': 'AMB-CHN-03',
        'driver_name': 'V. Anand (Unit #103)',
        'contact_phone': '+91 98403 44553',
        'latitude': 13.0012,
        'longitude': 80.2565,
        'base_location_name': 'Adyar Bridge Response Hub',
        'simulated_speed_kmh': 45.0,
        'status': 'AVAILABLE',
        'is_active': True
    },
    {
        'vehicle_identifier': 'AMB-CHN-04',
        'driver_name': 'M. Karthik (Unit #104)',
        'contact_phone': '+91 98404 55664',
        'latitude': 12.9249,
        'longitude': 80.1000,
        'base_location_name': 'Tambaram Sanatorium Emergency Base',
        'simulated_speed_kmh': 40.0,
        'status': 'AVAILABLE',
        'is_active': True
    },
    {
        'vehicle_identifier': 'AMB-CHN-05',
        'driver_name': 'D. Suresh (Unit #105)',
        'contact_phone': '+91 98405 66775',
        'latitude': 13.0418,
        'longitude': 80.2341,
        'base_location_name': 'T. Nagar Panagal Park Unit',
        'simulated_speed_kmh': 35.0,
        'status': 'AVAILABLE',
        'is_active': True
    }
]

def reset_fleet():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("[ERROR] DATABASE_URL environment variable is not set.")
        sys.exit(1)

    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif db_url.startswith('postgresql://') and not db_url.startswith('postgresql+'):
        db_url = db_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    import time
    engine = create_engine(
        db_url,
        pool_pre_ping=True
    )

    # Retry loop in case Neon endpoint is waking from suspended state
    conn = None
    for attempt in range(1, 4):
        try:
            print(f"[RESET] Connecting to Neon PostgreSQL (attempt {attempt}/3)...")
            conn = engine.connect()
            break
        except Exception as e:
            print(f"[RESET] Connection attempt {attempt} failed ({e}), waiting 3s...")
            time.sleep(3)

    if not conn:
        print("[ERROR] Could not establish connection to Neon DB.")
        sys.exit(1)

    with conn:
        trans = conn.begin()
        try:
            print("[RESET] 1. Inspecting active test/demo simulation emergency requests...")
            # Mark active simulation requests as 'COMPLETED' so ambulances are safely released
            # and request records are retained in history with an audit note.
            updated_reqs = conn.execute(
                text("""
                    UPDATE emergency_requests
                    SET status = 'COMPLETED',
                        notes = COALESCE(notes, '') || ' [Simulated run concluded for demo reset]',
                        status_updated_at = NOW()
                    WHERE is_simulation = TRUE
                      AND status IN ('ASSIGNED', 'EN_ROUTE', 'REQUESTED')
                """)
            ).rowcount
            print(f"[RESET] Completed {updated_reqs} active test/demo simulation emergency requests.")

            print("[RESET] 2. Resetting simulated Chennai ambulances to intended coordinates and AVAILABLE status...")
            for amb_data in TARGET_AMBULANCE_FLEET:
                conn.execute(
                    text("""
                        INSERT INTO ambulances (
                            vehicle_identifier, driver_name, contact_phone,
                            latitude, longitude, base_location_name,
                            simulated_speed_kmh, status, is_active, last_updated
                        )
                        VALUES (
                            :vehicle_identifier, :driver_name, :contact_phone,
                            :latitude, :longitude, :base_location_name,
                            :simulated_speed_kmh, :status, :is_active, NOW()
                        )
                        ON CONFLICT (vehicle_identifier) DO UPDATE SET
                            driver_name = EXCLUDED.driver_name,
                            contact_phone = EXCLUDED.contact_phone,
                            latitude = EXCLUDED.latitude,
                            longitude = EXCLUDED.longitude,
                            base_location_name = EXCLUDED.base_location_name,
                            simulated_speed_kmh = EXCLUDED.simulated_speed_kmh,
                            status = 'AVAILABLE',
                            is_active = TRUE,
                            last_updated = NOW();
                    """),
                    amb_data
                )
            print("[RESET] Successfully updated/reset all 5 ambulances to AVAILABLE status.")
            trans.commit()
        except Exception:
            trans.rollback()
            raise

    # Verification read
    with engine.connect() as verify_conn:
        available_count = verify_conn.execute(
            text("SELECT COUNT(*) FROM ambulances WHERE status = 'AVAILABLE' AND is_active = TRUE")
        ).scalar()
        print(f"[VERIFY] Currently available ambulances in Neon DB: {available_count}/5")

if __name__ == '__main__':
    reset_fleet()
