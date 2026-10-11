import unittest
from app import create_app
from config import TestingConfig
from app.models import db
from app.models.user import User
from app.models.ambulance import Ambulance, EmergencyRequest
from app.services.ambulance_service import (
    haversine_distance_km,
    estimate_eta_minutes,
    validate_coordinates,
    allocate_nearest_ambulance
)

class AmbulanceAllocationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

            # Seed 3 ambulances with known coordinates
            self.amb1 = Ambulance(
                vehicle_identifier='AMB-CHN-01',
                driver_name='Driver One',
                contact_phone='111',
                latitude=13.0827,
                longitude=80.2707,
                base_location_name='Chennai Central',
                status='AVAILABLE',
                simulated_speed_kmh=40.0
            )
            self.amb2 = Ambulance(
                vehicle_identifier='AMB-CHN-02',
                driver_name='Driver Two',
                contact_phone='222',
                latitude=13.0850,
                longitude=80.2101,
                base_location_name='Anna Nagar',
                status='AVAILABLE',
                simulated_speed_kmh=40.0
            )
            self.amb_busy = Ambulance(
                vehicle_identifier='AMB-BUSY',
                driver_name='Driver Three',
                contact_phone='333',
                latitude=13.0820,
                longitude=80.2700,
                base_location_name='Central Close Depot',
                status='ASSIGNED', # Busy
                simulated_speed_kmh=40.0
            )
            db.session.add_all([self.amb1, self.amb2, self.amb_busy])
            db.session.commit()
            self.amb1_id = self.amb1.id
            self.amb2_id = self.amb2.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_haversine_distance_calculation(self):
        """Distance calculation against known coordinates."""
        # Chennai Central (13.0827, 80.2707) to Adyar (13.0012, 80.2565) is approx 9.1 - 9.3 km
        dist = haversine_distance_km(13.0827, 80.2707, 13.0012, 80.2565)
        self.assertAlmostEqual(dist, 9.2, delta=0.5)

    def test_eta_calculation(self):
        """ETA is calculated properly from distance and speed."""
        # 10 km at 40 km/h with 1.2 traffic factor -> (10/40)*1.2*60 = 18 mins
        eta = estimate_eta_minutes(10.0, speed_kmh=40.0, traffic_factor=1.2)
        self.assertEqual(eta, 18)

    def test_coordinate_validation(self):
        """Valid and invalid coordinates handling."""
        lat, lon = validate_coordinates("13.0827", "80.2707")
        self.assertIsNotNone(lat)
        self.assertIsNotNone(lon)

        bad_lat, bad_lon = validate_coordinates("invalid", "999")
        self.assertIsNone(bad_lat)
        self.assertIsNone(bad_lon)

    def test_nearest_available_ambulance_selected(self):
        """Nearest available ambulance is allocated while busy ones are excluded."""
        with self.app.app_context():
            # Patient at Chennai Central: AMB-CHN-01 is nearest available (distance < 0.1km)
            # AMB-BUSY is closer but status is ASSIGNED, so it must be skipped!
            allocated, dist, eta = allocate_nearest_ambulance(13.0827, 80.2707)
            self.assertIsNotNone(allocated)
            self.assertEqual(allocated.vehicle_identifier, 'AMB-CHN-01')
            self.assertEqual(allocated.status, 'ASSIGNED') # Marked assigned

    def test_no_ambulance_available_response(self):
        """When all ambulances are busy or unavailable, an honest response is returned."""
        with self.app.app_context():
            # Mark all ambulances unavailable
            for a in Ambulance.query.all():
                a.status = 'BUSY'
            db.session.commit()

        res = self.client.post('/submitAmbulanceRequest', json={
            'name': 'Patient Emergency',
            'phone': '9876543210',
            'emergency': 'Cardiovascular episode',
            'location': 'Chennai Central',
            'latitude': 13.0827,
            'longitude': 80.2707
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get('no_ambulance_available'))
        self.assertEqual(data.get('status'), 'REQUESTED')
        self.assertTrue(data.get('is_simulation'))

    def test_emergency_privacy_access_control(self):
        """Patients cannot access another patient's emergency tracking details."""
        with self.app.app_context():
            patient_a = User(email='pt_a@test.com', full_name='Patient A', role='PATIENT')
            patient_a.set_password('pass123')
            patient_b = User(email='pt_b@test.com', full_name='Patient B', role='PATIENT')
            patient_b.set_password('pass123')
            db.session.add_all([patient_a, patient_b])
            db.session.flush()

            req = EmergencyRequest(
                patient_id=patient_a.id,
                patient_name='Patient A',
                patient_phone='123',
                emergency_type='Trauma',
                location_address='Sector 1',
                status='ASSIGNED'
            )
            db.session.add(req)
            db.session.commit()
            req_id = req.id
            pt_b_id = patient_b.id

        # Patient B tries to access Patient A's emergency status
        with self.client.session_transaction() as sess:
            sess['user_id'] = pt_b_id
            sess['user_role'] = 'PATIENT'

        res = self.client.get(f'/ambulance/status/{req_id}')
        self.assertEqual(res.status_code, 403)

    def test_emergency_request_schema_and_allocation_regression(self):
        """Regression test verifying emergency_requests query with ambulance_id FK and allocation."""
        with self.app.app_context():
            # Create an emergency request linked to ambulance
            req = EmergencyRequest(
                patient_name='Regression Tester',
                patient_phone='+91 99999 00000',
                emergency_type='Acute Chest Pain',
                location_address='Chennai Central',
                latitude=13.0827,
                longitude=80.2707,
                ambulance_id=self.amb1_id,
                assigned_vehicle="AMB-CHN-01 (Driver One)",
                distance_km=0.0,
                eta_minutes=2,
                priority='CRITICAL',
                status='ASSIGNED',
                is_simulation=True
            )
            db.session.add(req)
            db.session.commit()

            # Query all emergency requests using SQLAlchemy ORM (must not fail with UndefinedColumn)
            all_reqs = EmergencyRequest.query.all()
            self.assertGreaterEqual(len(all_reqs), 1)
            fetched = EmergencyRequest.query.filter_by(patient_name='Regression Tester').first()
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.ambulance_id, self.amb1_id)
            self.assertEqual(fetched.distance_km, 0.0)
            self.assertEqual(fetched.status, 'ASSIGNED')
            
            # Verify relationship & dictionary serialization
            d = fetched.to_dict()
            self.assertEqual(d['ambulance_id'], self.amb1_id)
            self.assertIsNotNone(d['ambulance_lat'])
            self.assertIsNotNone(d['ambulance_lng'])

if __name__ == '__main__':
    unittest.main()
