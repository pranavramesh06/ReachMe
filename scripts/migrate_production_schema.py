#!/usr/bin/env python
"""
Migration script to safely update Neon PostgreSQL schema with missing columns and indexes.
Non-destructive: Uses ADD COLUMN IF NOT EXISTS, sets foreign keys and indexes safely.
Preserves all existing data across all tables.
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

MIGRATION_SQL = """
BEGIN;

-- 1. Update emergency_requests table with missing columns from recent ambulance allocation model
ALTER TABLE emergency_requests 
    ADD COLUMN IF NOT EXISTS ambulance_id INTEGER,
    ADD COLUMN IF NOT EXISTS distance_km DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS status_updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add foreign key constraint to ambulances(id) if it doesn't already exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_emergency_requests_ambulance_id'
    ) THEN
        ALTER TABLE emergency_requests 
            ADD CONSTRAINT fk_emergency_requests_ambulance_id 
            FOREIGN KEY (ambulance_id) REFERENCES ambulances(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add indexes on emergency_requests for fast querying
CREATE INDEX IF NOT EXISTS ix_emergency_requests_ambulance_id ON emergency_requests (ambulance_id);
CREATE INDEX IF NOT EXISTS ix_emergency_requests_status ON emergency_requests (status);

-- 2. Update prescriptions table with missing clinical review columns
ALTER TABLE prescriptions 
    ADD COLUMN IF NOT EXISTS reviewed_by_doctor_id INTEGER,
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITHOUT TIME ZONE,
    ADD COLUMN IF NOT EXISTS rejection_reason TEXT,
    ADD COLUMN IF NOT EXISTS valid_until TIMESTAMP WITHOUT TIME ZONE;

-- Add foreign key constraint to doctors(id) if it doesn't already exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fk_prescriptions_reviewed_by_doctor_id'
    ) THEN
        ALTER TABLE prescriptions 
            ADD CONSTRAINT fk_prescriptions_reviewed_by_doctor_id 
            FOREIGN KEY (reviewed_by_doctor_id) REFERENCES doctors(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add index on prescriptions status for approval queue queries
CREATE INDEX IF NOT EXISTS ix_prescriptions_status ON prescriptions (status);

COMMIT;
"""

def run_migration():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("[ERROR] DATABASE_URL environment variable is not set.")
        sys.exit(1)

    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif db_url.startswith('postgresql://') and not db_url.startswith('postgresql+'):
        db_url = db_url.replace('postgresql://', 'postgresql+psycopg2://', 1)

    engine = create_engine(db_url)
    
    print("[MIGRATION] Connecting to Neon PostgreSQL...")
    with engine.connect() as conn:
        print("[MIGRATION] Applying non-destructive schema migration...")
        conn.execute(text(MIGRATION_SQL))
        print("[MIGRATION] Schema migration successfully applied and committed!")

if __name__ == '__main__':
    run_migration()
