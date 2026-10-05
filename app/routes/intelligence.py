import json
from flask import render_template, request, jsonify, session, flash, redirect, url_for
from app.routes import intelligence_bp
from app.models import db
from app.models.triage import TriageRecommendation
from app.services.triage_service import analyze_triage_symptoms

@intelligence_bp.route('/triage', methods=['GET', 'POST'])
def triage():
    result = None
    if request.method == 'POST':
        symptoms = request.form.get('symptoms', '').strip()
        severity = int(request.form.get('severity', 5))
        duration = int(request.form.get('duration', 1))
        age = int(request.form.get('age', 30))

        if not symptoms:
            flash('Please describe your symptoms to receive decision support.', 'warning')
            return redirect(url_for('intelligence.triage'))

        result = analyze_triage_symptoms(symptoms, severity=severity, duration_days=duration, age=age)

        # Save to database
        user_id = session.get('user_id')
        user_name = session.get('user_name', 'Anonymous Patient')

        triage_rec = TriageRecommendation(
            user_id=user_id,
            patient_name=user_name,
            symptoms_input=symptoms,
            urgency_level=result['urgency_level'],
            risk_score=result['risk_score'],
            recommended_specialization=result['recommended_specialization'],
            recommended_doctor_id=result.get('recommended_doctor_id'),
            recommended_doctor_name=result.get('recommended_doctor_name'),
            contributing_factors_json=json.dumps(result['contributing_factors']),
            recommended_action=result['recommended_action']
        )
        db.session.add(triage_rec)
        db.session.commit()

    user_history = []
    if session.get('user_id'):
        user_history = TriageRecommendation.query.filter_by(user_id=session['user_id']).order_by(TriageRecommendation.created_at.desc()).limit(5).all()

    return render_template('intelligence/triage.html', result=result, user_history=user_history)
