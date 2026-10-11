from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.routes import medicine_bp
from app.models import db
from app.models.medicine import Medicine, MedicineCategory
from app.models.order import Order, OrderItem
from app.models.prescription import Prescription, MedicineApprovalRequest
from app.models.doctor import Doctor

@medicine_bp.route('/orderMeds')
def order_meds():
    search_query = request.args.get('search', '').strip()
    category_id = request.args.get('category', type=int)

    query = Medicine.query.filter_by(is_available=True)
    if search_query:
        query = query.filter(Medicine.name.ilike(f"%{search_query}%"))
    if category_id:
        query = query.filter_by(category_id=category_id)

    medicines = query.order_by(Medicine.name).all()
    categories = MedicineCategory.query.all()

    # User approvals mapping if authenticated
    user_id = session.get('user_id')
    user_valid_approvals = {}
    user_prescriptions = []
    doctors = []
    
    if user_id:
        approvals = MedicineApprovalRequest.query.filter_by(patient_id=user_id).all()
        for app in approvals:
            if app.is_currently_valid():
                user_valid_approvals[app.medicine_id] = {
                    'request_id': app.id,
                    'remaining_qty': app.remaining_authorized_quantity(),
                    'valid_until': app.valid_until.strftime('%Y-%m-%d') if app.valid_until else 'No expiry'
                }
        user_prescriptions = Prescription.query.filter_by(patient_id=user_id).order_by(Prescription.uploaded_at.desc()).all()
        doctors = Doctor.query.filter_by(is_available=True).all()

    return render_template(
        'medicine/catalog.html',
        medicines=medicines,
        categories=categories,
        search_query=search_query,
        selected_category=category_id,
        user_valid_approvals=user_valid_approvals,
        user_prescriptions=user_prescriptions,
        doctors=doctors
    )

@medicine_bp.route('/request-approval', methods=['POST'])
def request_approval():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to submit a prescription review request.', 'warning')
        return redirect(url_for('auth.login', next=url_for('medicine.order_meds')))

    medicine_id = request.form.get('medicine_id', type=int)
    doctor_id = request.form.get('doctor_id', type=int)
    prescription_id = request.form.get('prescription_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)
    clinical_notes = request.form.get('clinical_notes', '').strip()

    medicine = Medicine.query.get_or_404(medicine_id)
    if not medicine.requires_prescription:
        flash(f'{medicine.name} does not require a prescription approval.', 'info')
        return redirect(url_for('medicine.order_meds'))

    if quantity <= 0:
        quantity = 1

    # Verify prescription belongs to user if provided
    if prescription_id:
        rx = Prescription.query.get(prescription_id)
        if not rx or rx.patient_id != user_id:
            flash('Invalid prescription selected.', 'danger')
            return redirect(url_for('medicine.order_meds'))

    # If doctor not specified, route to first available doctor or leave unassigned
    if not doctor_id:
        doc = Doctor.query.filter_by(is_available=True).first()
        doctor_id = doc.id if doc else None

    approval_req = MedicineApprovalRequest(
        patient_id=user_id,
        medicine_id=medicine_id,
        prescription_id=prescription_id if prescription_id else None,
        doctor_id=doctor_id,
        quantity_requested=quantity,
        clinical_notes=clinical_notes,
        status='PENDING'
    )
    db.session.add(approval_req)
    db.session.commit()

    flash(f'Approval request for {medicine.name} submitted successfully! Your doctor will review your prescription.', 'success')
    return redirect(url_for('patient.dashboard'))

@medicine_bp.route('/submit', methods=['POST'])
def submit_order():
    full_name = request.form.get('Full_name', '').strip()
    phone_number = request.form.get('Phone_number', '').strip()
    shipping_address = request.form.get('Shipping_address', '').strip()

    medications = request.form.getlist('Medication')
    quantities = request.form.getlist('Quantity')

    if not full_name or not phone_number or not shipping_address or not medications:
        flash('Please fill in all order details and select at least one medication.', 'danger')
        return redirect(url_for('medicine.order_meds'))

    user_id = session.get('user_id')

    order_items_data = []
    total_order_price = 0.0
    prescriptions_summary = []
    approvals_to_decrement = []

    # STRICT BACKEND ENFORCEMENT OF PRESCRIPTION ELIGIBILITY & CONCURRENCY
    for med_name_raw, qty_raw in zip(medications, quantities):
        if not med_name_raw or not qty_raw:
            continue
        try:
            qty = int(qty_raw)
            if qty <= 0:
                continue
        except ValueError:
            continue

        med_name = med_name_raw.strip()
        medicine = Medicine.query.filter(Medicine.name.ilike(med_name)).first()

        if not medicine:
            flash(f'Sorry, medication "{med_name}" is currently unavailable in our database.', 'danger')
            return redirect(url_for('medicine.order_meds'))

        # Check stock quantity
        if medicine.stock_quantity < qty:
            flash(f'Sorry, stock limit reached for {medicine.name}. Only {medicine.stock_quantity} available.', 'warning')
            return redirect(url_for('medicine.order_meds'))

        # STRICT PRESCRIPTION CHECK
        if medicine.requires_prescription:
            if not user_id:
                flash(f'"{medicine.name}" requires an approved prescription. Please log in to complete this purchase.', 'danger')
                return redirect(url_for('auth.login', next=url_for('medicine.order_meds')))

            # Check for valid approved MedicineApprovalRequest
            # Concurrency-safe check using with_for_update where supported
            try:
                valid_approval = (
                    MedicineApprovalRequest.query
                    .filter_by(patient_id=user_id, medicine_id=medicine.id, status='APPROVED')
                    .with_for_update()
                    .first()
                )
            except Exception:
                valid_approval = (
                    MedicineApprovalRequest.query
                    .filter_by(patient_id=user_id, medicine_id=medicine.id, status='APPROVED')
                    .first()
                )

            if not valid_approval or not valid_approval.is_currently_valid():
                flash(
                    f'Order blocked: "{medicine.name}" requires an active doctor-approved prescription. '
                    f'Your request is either pending review, rejected, or missing.',
                    'danger'
                )
                return redirect(url_for('medicine.order_meds'))

            # Check authorized quantity limit
            remaining_allowed = valid_approval.remaining_authorized_quantity()
            if qty > remaining_allowed:
                flash(
                    f'Order blocked: Requested quantity ({qty}) exceeds authorized prescription limit '
                    f'({remaining_allowed} units remaining) for {medicine.name}.',
                    'danger'
                )
                return redirect(url_for('medicine.order_meds'))

            approvals_to_decrement.append((valid_approval, qty))

        # Backend controlled price calculation
        unit_price = medicine.price
        subtotal = unit_price * qty
        total_order_price += subtotal

        # Stock decrement
        medicine.stock_quantity -= qty

        order_items_data.append({
            'medicine_id': medicine.id,
            'medicine_name': medicine.name,
            'quantity': qty,
            'unit_price': unit_price,
            'subtotal': subtotal
        })

        prescriptions_summary.append(
            f"Medicine: {medicine.name}, Quantity: {qty}, Unit Price: ₹{unit_price}, Subtotal: ₹{subtotal}"
        )

    if not order_items_data:
        flash('Invalid order items submitted.', 'danger')
        return redirect(url_for('medicine.order_meds'))

    # Update approvals quantity used within database transaction
    for approval, used_qty in approvals_to_decrement:
        approval.quantity_used = (approval.quantity_used or 0) + used_qty

    order = Order(
        user_id=user_id,
        full_name=full_name,
        phone_number=phone_number,
        shipping_address=shipping_address,
        total_amount=total_order_price,
        status='PROCESSING'
    )
    db.session.add(order)
    db.session.flush()

    for item in order_items_data:
        order_item = OrderItem(
            order_id=order.id,
            medicine_id=item['medicine_id'],
            medicine_name=item['medicine_name'],
            quantity=item['quantity'],
            unit_price=item['unit_price'],
            subtotal=item['subtotal']
        )
        db.session.add(order_item)

    db.session.commit()

    return render_template(
        'medicine/order_success.html',
        order=order,
        prescriptions=prescriptions_summary,
        total_price=total_order_price
    )
