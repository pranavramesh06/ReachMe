from flask import render_template, request, flash, redirect, url_for
from app.routes import main_bp
from app.models.medicine import Medicine
from app.models.doctor import Doctor
from app.services.analytics_service import get_dashboard_analytics

@main_bp.route('/')
def index():
    stats = get_dashboard_analytics()
    featured_doctors = Doctor.query.order_by(Doctor.rating.desc()).limit(4).all()
    featured_medicines = Medicine.query.filter_by(is_available=True).limit(4).all()
    return render_template(
        'index.html',
        stats=stats,
        featured_doctors=featured_doctors,
        featured_medicines=featured_medicines
    )

@main_bp.route('/about-us')
def about_us():
    return render_template('about-us.html')

@main_bp.route('/contact-us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        flash(f'Thank you {name}, your inquiry has been received. Our team will contact you at {email}.', 'success')
        return redirect(url_for('main.contact_us'))
    return render_template('contact-us.html')

@main_bp.route('/getting-started')
def getting_started():
    return render_template('getting-started.html')

@main_bp.route('/talk-to-ai')
def talk_to_ai():
    return render_template('talk-to-ai.html')
