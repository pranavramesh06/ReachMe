from flask import Blueprint

# Centralized route blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
patient_bp = Blueprint('patient', __name__)
doctor_bp = Blueprint('doctor', __name__)
admin_bp = Blueprint('admin', __name__)
medicine_bp = Blueprint('medicine', __name__)
consultation_bp = Blueprint('consultation', __name__)
prescription_bp = Blueprint('prescription', __name__)
ambulance_bp = Blueprint('ambulance', __name__)
intelligence_bp = Blueprint('intelligence', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')
