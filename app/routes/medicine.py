from flask import render_template, request, redirect, url_for, flash, session
from app.routes import medicine_bp
from app.models import db
from app.models.medicine import Medicine, MedicineCategory
from app.models.order import Order, OrderItem

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

    return render_template(
        'medicine/catalog.html',
        medicines=medicines,
        categories=categories,
        search_query=search_query,
        selected_category=category_id
    )

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

    order_items_data = []
    total_order_price = 0.0
    prescriptions_summary = []

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

        if medicine.stock_quantity < qty:
            flash(f'Sorry, stock limit reached for {medicine.name}. Only {medicine.stock_quantity} available.', 'warning')
            return redirect(url_for('medicine.order_meds'))

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

    user_id = session.get('user_id')

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
