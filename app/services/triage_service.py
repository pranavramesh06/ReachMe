import json
from app.models.doctor import Doctor, Specialization

SYMPTOM_TAXONOMY = {
    'cardiac': {
        'keywords': ['chest pain', 'heart rate', 'palpitations', 'tightness in chest', 'left arm pain'],
        'specialty': 'Cardiologist',
        'base_risk': 85.0
    },
    'neurological': {
        'keywords': ['numbness', 'slurred speech', 'seizure', 'fainting', 'severe dizziness', 'paralysis'],
        'specialty': 'Neurologist',
        'base_risk': 88.0
    },
    'dermatological': {
        'keywords': ['rash', 'itching', 'skin lesion', 'eczema', 'acne', 'hives', 'skin redness'],
        'specialty': 'Dermatologist',
        'base_risk': 35.0
    },
    'pediatric': {
        'keywords': ['child fever', 'infant', 'toddler cough', 'pediatric rash', 'child vomiting'],
        'specialty': 'Pediatrician',
        'base_risk': 60.0
    },
    'gastrointestinal': {
        'keywords': ['stomach pain', 'acid reflux', 'vomiting', 'diarrhea', 'abdominal cramps', 'nausea'],
        'specialty': 'Gastroenterologist',
        'base_risk': 55.0
    },
    'respiratory': {
        'keywords': ['shortness of breath', 'wheezing', 'asthma attack', 'coughing blood', 'difficulty breathing'],
        'specialty': 'Pulmonologist',
        'base_risk': 80.0
    },
    'orthopedic': {
        'keywords': ['fracture', 'joint pain', 'back pain', 'knee pain', 'sprain', 'bone pain'],
        'specialty': 'Orthopedic Surgeon',
        'base_risk': 45.0
    },
    'general': {
        'keywords': ['fever', 'headache', 'fatigue', 'body pain', 'sore throat', 'cold', 'flu'],
        'specialty': 'General Physician',
        'base_risk': 30.0
    }
}

def analyze_triage_symptoms(symptoms_text, severity=5, duration_days=1, age=30):
    """
    Data-Driven Healthcare Access & Triage Recommendation Engine.
    Provides explainable decision support (NOT diagnostic medical advice).
    """
    text_lower = symptoms_text.lower()
    matched_category = 'general'
    highest_score = 0.0
    contributing_factors = []

    # 1. Match symptom taxonomy
    for cat_name, info in SYMPTOM_TAXONOMY.items():
        matches = [kw for kw in info['keywords'] if kw in text_lower]
        if matches:
            score = info['base_risk'] + (len(matches) * 5)
            if score > highest_score:
                highest_score = score
                matched_category = cat_name
                contributing_factors.append(f"Identified primary symptom indicators: {', '.join(matches).title()}")

    if not contributing_factors:
        contributing_factors.append("General symptom query processed via primary care triage rule set.")
        highest_score = 30.0

    # 2. Adjust for reported severity scale (1 - 10)
    severity_boost = (int(severity) - 5) * 4.0
    risk_score = min(max(highest_score + severity_boost, 10.0), 98.0)
    contributing_factors.append(f"Patient reported symptom severity scale: {severity}/10")

    # 3. Adjust for duration
    if int(duration_days) > 7:
        risk_score = min(risk_score + 10.0, 98.0)
        contributing_factors.append(f"Chronic duration noted ({duration_days} days ongoing)")

    # 4. Determine Urgency Tier
    if risk_score >= 80.0:
        urgency = "CRITICAL"
        action = "Immediate medical evaluation recommended. Emergency assistance or urgent care visit suggested."
    elif risk_score >= 60.0:
        urgency = "HIGH"
        action = "Same-day doctor consultation recommended for targeted examination."
    elif risk_score >= 35.0:
        urgency = "MEDIUM"
        action = "Schedule a consultation with a specialist within 24-48 hours."
    else:
        urgency = "ROUTINE"
        action = "Routine tele-consultation or over-the-counter medication advice."

    # 5. Doctor Recommendation & Availability Lookup from Database
    target_specialty = SYMPTOM_TAXONOMY[matched_category]['specialty']
    recommended_doc = Doctor.query.filter(
        Doctor.specialty.ilike(f"%{target_specialty}%"),
        Doctor.is_available == True
    ).order_by(Doctor.rating.desc()).first()

    if not recommended_doc:
        recommended_doc = Doctor.query.filter_by(is_available=True).order_by(Doctor.rating.desc()).first()

    if recommended_doc:
        contributing_factors.append(f"Matched available specialist: {recommended_doc.name} ({recommended_doc.specialty}) with {recommended_doc.rating}★ rating")

    return {
        'symptoms_input': symptoms_text,
        'urgency_level': urgency,
        'risk_score': round(risk_score, 1),
        'recommended_specialization': target_specialty,
        'recommended_doctor_id': recommended_doc.id if recommended_doc else None,
        'recommended_doctor_name': recommended_doc.name if recommended_doc else "Available Network Physician",
        'contributing_factors': contributing_factors,
        'recommended_action': action
    }
