#!/usr/bin/env python
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db
from app.services.seed_service import migrate_and_seed_data

def main():
    app = create_app()
    with app.app_context():
        print("Initializing database tables...")
        db.create_all()
        migrate_and_seed_data()
        print("Migration process finished successfully.")

if __name__ == '__main__':
    main()
