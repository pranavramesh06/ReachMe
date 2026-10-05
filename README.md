<h1 align="center" id="title">ReachMe — Data-Driven Telemedicine & Healthcare Intelligence Platform</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/Neon_PostgreSQL-Relational_DB-00E599?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-Modern_UI-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
</p>

> **Hackathon Track: Code to Cure – Data-Driven Healthcare**  
> A production-grade, database-driven healthcare platform transformed from a legacy spreadsheet prototype into a modern, robust telemedicine platform. Powered by **Neon PostgreSQL**, **Flask-SQLAlchemy**, **Computer Vision OCR**, and an explainable **Healthcare Triage & Recommendation Engine**.

---

## 📋 Table of Contents
1. [Project Overview](#-project-overview)
2. [Key Features](#-key-features)
3. [Technology Stack](#-technology-stack)
4. [Architecture & System Design](#-architecture--system-design)
5. [Database Schema](#-database-schema)
6. [Neon PostgreSQL Setup](#-neon-postgresql-setup)
7. [Environment Variables](#-environment-variables)
8. [Installation & Setup](#-installation--setup)
9. [Database & Excel Data Migration](#-database--excel-data-migration)
10. [Demo Accounts](#-demo-accounts)
11. [Running Locally](#-running-locally)
12. [Testing](#-testing)
13. [Project Structure](#-project-structure)
14. [Security Considerations](#-security-considerations)
15. [Limitations & Simulations](#-limitations--simulations)
16. [Future Improvements](#-future-improvements)

---

## 🌟 Project Overview

**ReachMe** connects patients with healthcare providers, online pharmacy inventory, and emergency dispatch tracking. 

While the initial prototype relied on flat `.xlsx` Excel spreadsheets for data persistence, the platform has now been completely transformed to use **Neon PostgreSQL** via **SQLAlchemy ORM**. It adds role-based access control, transaction-safe inventory management, real-time double-booking prevention, automated prescription OCR scanning, and an intelligent **Symptom Triage Decision-Support Engine** with explainable clinical indicators.

---

## 🚀 Key Features

### 1. 🧠 Hackathon Track: Smart Healthcare Triage Engine
- **Explainable Clinical Decision Support**: Evaluates patient symptoms against a medical taxonomy, factoring in reported severity (1–10 scale) and duration.
- **Risk Score & Urgency Rating**: Generates dynamic risk scores (`CRITICAL`, `HIGH`, `MEDIUM`, `ROUTINE`).
- **Explainable Factors**: Breaks down the assessment into transparent contributing factors (e.g. cardiac symptom indicators, chronic duration).
- **Specialist Routing**: Automatically queries PostgreSQL to match the patient with top-rated available specialists in the network.

### 2. 💊 Online E-Pharmacy & Order Management
- **Search & Category Filtering**: Browse medicines with live database search and therapeutic category filters.
- **Backend-Enforced Pricing**: Prices are calculated and validated strictly on the server—never trusting client-side tampering.
- **Stock Tracking**: Atomic stock decrementing and out-of-stock guards.
- **Multi-Item Orders**: Supports ordering multiple medications in a single checkout.

### 3. 👨‍⚕️ Doctor Consultation System
- **Practitioner Directory**: Filter doctors by medical specialty, experience years, and consultation fee.
- **Double-Booking Prevention**: Strict database validation prevents multiple patients from reserving the same doctor for the same date and time slot.
- **Appointment Management**: Patients can view upcoming consultations and cancel appointments; doctors can mark appointments as completed.

### 4. 📄 Prescription OCR Scanner
- **Computer Vision Extraction**: Upload image/PDF prescriptions to extract text via Pytesseract image pre-processing.
- **Clinical Safety Distinction**: Clearly separates raw machine-extracted OCR text from doctor-verified medications.

### 5. 🚑 Emergency Ambulance Dispatch Simulation
- **Geolocation Integration**: Auto-detects patient coordinates via browser GPS.
- **State Machine Workflow**: Real-time tracking from `REQUESTED` → `ACKNOWLEDGED` → `EN_ROUTE` → `ARRIVED`.
- **Transparency**: Explicitly labeled as a simulation demo mode for hackathon evaluation.

### 6. 🔐 Authentication & Role-Based Access Control
- **Werkzeug Password Hashing**: Passwords are securely hashed with salted hashes.
- **Role Hierarchy**: Separate views and permissions for `PATIENT`, `DOCTOR`, and `ADMIN`.
- **Dedicated Dashboards**:
  - **Patient Dashboard**: My appointments, active orders, prescription vault, and triage history.
  - **Doctor Dashboard**: Appointment schedule overview, patient symptom summaries, and status updates.
  - **Admin Dashboard**: System-wide statistics from PostgreSQL, inventory control, and emergency dispatch tracking.

---

## 💻 Technology Stack

- **Backend**: Python 3.11+, Flask 3.0+
- **Database**: Neon PostgreSQL (Production), SQLAlchemy ORM, Flask-Migrate
- **Authentication**: Werkzeug Security (pbkdf2:sha256)
- **Computer Vision / OCR**: Pillow (PIL), Pytesseract
- **Data Migration & Seeding**: openpyxl, pandas
- **Frontend**: HTML5, Tailwind CSS, Flowbite, FontAwesome 6
- **Testing**: Python unittest / Pytest

---

## 🗄️ Database Schema

The database design uses normalized relational models:

```
 users (id, email, password_hash, full_name, phone, role, is_active, created_at)
   ├── patient_profiles (id, user_id, blood_group, address, emergency_contact)
   ├── doctors (id, user_id, name, specialty, specialization_id, experience_years, consultation_fee, rating, is_available)
   │     └── doctor_availabilities (id, doctor_id, day_of_week, start_time, end_time)
   ├── appointments (id, patient_id, doctor_id, doctor_name, appointment_date, time_slot, problem_description, status)
   ├── orders (id, user_id, full_name, phone_number, shipping_address, total_amount, status, created_at)
   │     └── order_items (id, order_id, medicine_id, medicine_name, quantity, unit_price, subtotal)
   ├── prescriptions (id, patient_id, filename, file_path, raw_ocr_text, verified_medications_json, status)
   ├── emergency_requests (id, patient_id, patient_name, emergency_type, location_address, priority, status, eta_minutes)
   └── triage_recommendations (id, user_id, symptoms_input, urgency_level, risk_score, recommended_specialization, contributing_factors_json)
```

---

## ☁️ Neon PostgreSQL Setup

1. Create a free PostgreSQL database at [Neon.tech](https://neon.tech).
2. Copy your connection string from the Neon dashboard.
3. Add the string to your `.env` file:
   ```env
   DATABASE_URL=postgresql://your_user:your_password@ep-cool-name-123456.us-east-2.aws.neon.tech/reachme_db?sslmode=require
   ```

*(Note: If `DATABASE_URL` is omitted, the platform automatically defaults to a local SQLite database for zero-config local testing).*

---

## ⚙️ Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Neon PostgreSQL Connection String
DATABASE_URL=postgresql://your_neon_postgresql_connection_string?sslmode=require

# Flask Configuration
SECRET_KEY=your_secure_secret_key_here
FLASK_ENV=development
PORT=5000
```

---

## 🛠️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/pranavramesh06/ReachMe.git
   cd ReachMe
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 📦 Database & Excel Data Migration

Run the migration script to convert historical data from `medicine_prices.xlsx`, `doctor_list.xlsx`, `consultations.xlsx`, and `orders.xlsx` into PostgreSQL:

```bash
python scripts/migrate_excel_data.py
```

Output:
```
Initializing database tables...
[Seed Service] Starting data migration from Excel files...
[Seed Service] Migrated 50 medicines from Excel.
[Seed Service] Migrated 31 doctors from Excel.
[Seed Service] Migrated 1 consultations from Excel.
[Seed Service] Migrated 11 orders from Excel.
[Seed Service] Data migration complete!
Migration process finished successfully.
```

---

## 👥 Demo Accounts

The database comes pre-seeded with accounts for all roles:

| Role | Email | Password | Access Level |
|---|---|---|---|
| **Patient** | `patient@reachme.com` | `patient123` | Patient Portal, Orders, Appointments |
| **Doctor** | `dr.johnsmith@reachme.com` | `doctor123` | Doctor Consultation Dashboard |
| **Admin** | `admin@reachme.com` | `admin123` | Platform Metrics, Stock Control, Emergency Log |

---

## 🏃 Running Locally

Start the development server:

```bash
python run.py
```

Access the application in your browser at: **`http://localhost:5000`**

---

## 🧪 Testing

Run the automated test suite:

```bash
python -m unittest discover -s tests
```

Output:
```
......
----------------------------------------------------------------------
Ran 6 tests in 0.741s

OK
```

The test suite verifies:
- User registration, login, and password hashing.
- Medicine stock validation and backend pricing enforcement.
- Doctor consultation booking and double-booking rejection.
- Emergency ambulance dispatch request creation and simulation flags.
- Healthcare triage engine symptom scoring and explainable factors output.

---

## 📂 Project Structure

```
ReachMe/
│
├── app/
│   ├── __init__.py           # Flask App Factory & extension initialization
│   ├── models/               # SQLAlchemy Relational Models
│   │   ├── __init__.py
│   │   ├── user.py           # User & PatientProfile
│   │   ├── doctor.py         # Doctor, Specialization, Availability
│   │   ├── medicine.py       # Medicine, MedicineCategory
│   │   ├── order.py          # Order & OrderItem
│   │   ├── appointment.py    # Appointment
│   │   ├── prescription.py   # Prescription & OCR Vault
│   │   ├── ambulance.py      # EmergencyRequest
│   │   └── triage.py         # TriageRecommendation & AuditLog
│   ├── routes/               # Modular Flask Blueprints
│   │   ├── __init__.py
│   │   ├── main.py           # Landing, About, Contact, Voice Assistant
│   │   ├── auth.py           # Authentication & Role guards
│   │   ├── patient.py        # Patient Dashboard
│   │   ├── doctor.py         # Doctor Dashboard & slot updates
│   │   ├── admin.py          # Admin System Control & stock management
│   │   ├── medicine.py       # E-Pharmacy catalog & order checkout
│   │   ├── consultation.py   # Doctor search & double-booking prevention
│   │   ├── prescription.py   # OCR image upload & parsing
│   │   ├── ambulance.py      # Emergency request & simulation tracker
│   │   ├── intelligence.py   # Smart Healthcare Triage Engine
│   │   └── api.py            # REST API endpoints
│   ├── services/             # Core Business Logic
│   │   ├── seed_service.py   # Excel to PostgreSQL migration runner
│   │   ├── triage_service.py # Healthcare triage & explainability algorithm
│   │   ├── analytics_service.py # PostgreSQL dynamic metrics aggregator
│   │   └── ocr_service.py    # Image pre-processing & OCR extraction
│   ├── static/               # Assets & uploads
│   └── templates/            # Redesigned Modern Tailwind Templates
│       ├── base.html         # Master layout
│       ├── index.html        # Modern Landing Page
│       ├── auth/             # Login & Registration
│       ├── dashboards/       # Patient, Doctor, Admin Portals
│       ├── medicine/         # Catalog & Order Success
│       ├── consult/          # Doctor Directory & Appointment Booking
│       ├── prescription/     # OCR Scanner
│       ├── ambulance/        # Live Emergency Simulation
│       ├── intelligence/     # Smart Triage Engine
│       └── errors/           # 404, 403, 500 error handlers
│
├── scripts/
│   └── migrate_excel_data.py # Standalone database migration CLI
├── tests/                    # Automated Unit Tests
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore patterns
├── config.py                 # Application configuration
├── requirements.txt          # Production dependencies
├── run.py                    # Server entrypoint
└── README.md                 # Complete documentation
```

---

## 🔒 Security Considerations

- **Secure Password Hashing**: Implements Werkzeug's salted hashing. Plaintext passwords are never saved.
- **Role-Based Authorization**: Protected routes enforce strict role checks; patients cannot access administrative controls.
- **Backend Pricing**: Frontend forms cannot manipulate medicine unit prices.
- **SQL Injection Prevention**: All queries execute through SQLAlchemy parameterized ORM calls.
- **Secure File Uploads**: Uploaded prescriptions are checked for file extensions, size limits (max 16MB), and sanitized filenames.

---

## ⚠️ Limitations & Simulated Features

- **Ambulance Dispatch**: The ambulance dispatch system is a **simulation demo** designed for hackathon demonstration. It simulates real-time vehicle dispatch workflows (`REQUESTED` → `ACKNOWLEDGED` → `EN_ROUTE` → `ARRIVED`) and is clearly labeled as such.
- **Prescription OCR**: Extracted OCR text is classified as unverified machine text and requires clinical confirmation by a medical doctor before prescription fulfillment.
- **Decision Support**: The Smart Triage Engine provides decision-support and routing advice, not automated medical diagnoses.

---

## 🔮 Future Improvements

1. Integration with hospital Electronic Health Records (HL7 / FHIR).
2. Live WebRTC video consultations between doctors and patients.
3. Payment gateway integration (Razorpay / Stripe) for online pharmacy orders.
4. Push notifications and SMS alerts for upcoming appointments.

---

## 📄 License
This project is licensed under the MIT License.
