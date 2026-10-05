import os
import json
from flask import render_template, request, jsonify, flash, redirect, url_for, session, current_app
from werkzeug.utils import secure_filename
from app.routes import prescription_bp
from app.models import db
from app.models.prescription import Prescription
from app.services.ocr_service import process_prescription_image

@prescription_bp.route('/pa')
@prescription_bp.route('/prescription/upload')
def upload_page():
    user_id = session.get('user_id')
    prescriptions = []
    if user_id:
        prescriptions = Prescription.query.filter_by(patient_id=user_id).order_by(Prescription.uploaded_at.desc()).all()
    return render_template('prescription/upload.html', prescriptions=prescriptions)

@prescription_bp.route('/upload', methods=['POST'])
def upload():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No file part in request'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        if ext not in current_app.config['ALLOWED_EXTENSIONS']:
            return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, PDF'}), 400

        image_bytes = file.read()
        if len(image_bytes) > current_app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'error': 'File exceeds maximum limit of 16MB'}), 400

        # Save to static uploads folder
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        unique_filename = f"{int(os.urandom(4).hex(), 16)}_{filename}"
        save_path = os.path.join(upload_folder, unique_filename)

        with open(save_path, 'wb') as f:
            f.write(image_bytes)

        # Run OCR Service
        ocr_result = process_prescription_image(image_bytes)

        user_id = session.get('user_id')
        user_name = session.get('user_name', 'Guest Patient')

        prescription = Prescription(
            patient_id=user_id,
            patient_name=user_name,
            filename=unique_filename,
            file_path=f"/static/uploads/{unique_filename}",
            raw_ocr_text=ocr_result.get('raw_text', ''),
            verified_medications_json=json.dumps(ocr_result.get('extracted_meds', [])),
            status='PENDING_VERIFICATION'
        )
        db.session.add(prescription)
        db.session.commit()

        return jsonify({
            'success': True,
            'text': ocr_result.get('raw_text', ''),
            'extracted_meds': ocr_result.get('extracted_meds', []),
            'prescription_id': prescription.id,
            'file_url': prescription.file_path,
            'notice': 'OCR extracted text is unverified raw text. Doctor verification is required before medical use.'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400
