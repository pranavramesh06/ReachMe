import os
from flask import Flask, render_template, session
from config import Config
from app.models import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.patient import patient_bp
    from app.routes.doctor import doctor_bp
    from app.routes.admin import admin_bp
    from app.routes.medicine import medicine_bp
    from app.routes.consultation import consultation_bp
    from app.routes.prescription import prescription_bp
    from app.routes.ambulance import ambulance_bp
    from app.routes.intelligence import intelligence_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(medicine_bp)
    app.register_blueprint(consultation_bp)
    app.register_blueprint(prescription_bp)
    app.register_blueprint(ambulance_bp)
    app.register_blueprint(intelligence_bp)
    app.register_blueprint(api_bp)

    # Context processors for navigation & auth user state
    @app.context_processor
    def inject_user():
        from app.models.user import User
        current_user = None
        if 'user_id' in session:
            current_user = db.session.get(User, session['user_id'])
        return dict(current_user=current_user)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Auto-initialize DB tables & seed Excel data if first run (non-testing and non-serverless)
    if not app.config.get('TESTING') and not os.environ.get('VERCEL'):
        with app.app_context():
            try:
                db.create_all()
                from app.services.seed_service import migrate_and_seed_data
                from app.models.medicine import Medicine
                if Medicine.query.count() == 0:
                    migrate_and_seed_data()
            except Exception as e:
                print(f"[App Init Warning] DB auto-creation notice: {e}")

    return app
