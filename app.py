from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from models import db, Customer, Product, Sale, SaleItem, Vendor, Purchase, PurchaseItem, Report
import os
import json
from decimal import Decimal
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://kkk_enterprises_db_user:nEXLJUzyGZ4g4GAuPiWBTXXXthqlODAk@dpg-cv3e3b0gph6c738ptvc0-a.oregon-postgres.render.com/kkk_enterprises_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Function to generate daily report
def generate_daily_report():
    with app.app_context():
        # Get today's date
        today = datetime.now().date()
        
        # Get sales and purchases for today
        sales = Sale.query.filter(
            Sale.sale_date >= today,
            Sale.sale_date < today + timedelta(days=1)
        ).all()
        
        purchases = Purchase.query.filter(
            Purchase.purchase_date >= today,
            Purchase.purchase_date < today + timedelta(days=1)
        ).all()
        
        # Calculate totals
        total_sales = sum(sale.total_amount for sale in sales)
        total_purchases = sum(purchase.total_amount for purchase in purchases)
        net_profit = total_sales - total_purchases
        profit_margin = (net_profit / total_sales * 100) if total_sales > 0 else 0
        
        # Check inventory status
        products = Product.query.all()
        low_stock_count = sum(1 for p in products if p.quantity > 0 and p.quantity <= 10)
        out_of_stock_count = sum(1 for p in products if p.quantity <= 0)
        
        # Create a new report object
        report = Report(
            report_type='daily',
            start_date=today,
            end_date=today,
            total_sales=total_sales,
            total_purchases=total_purchases,
            net_profit=net_profit,
            profit_margin=profit_margin,
            low_stock_count=low_stock_count,
            out_of_stock_count=out_of_stock_count
        )
        
        db.session.add(report)
        db.session.commit()
        
        print(f"Daily Report Generated for {today}")
        print(f"Total Sales: ₹{total_sales}")
        print(f"Total Purchases: ₹{total_purchases}")
        print(f"Net Profit: ₹{net_profit}")
        print(f"Profit Margin: {profit_margin:.1f}%")
        print(f"Low Stock Items: {low_stock_count}")
        print(f"Out of Stock Items: {out_of_stock_count}")
        
        # Create a notification for the report
        print("Notification created: Daily business report is now available")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/insights')
def insights():
    return render_template('insights.html')

@app.route('/stock')
def stock():
    products = Product.query.all()
    return render_template('stock.html', products=products)

@app.route('/sales')
def sales():
    sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    return render_template('sales.html', sales=sales)

@app.route('/purchases')
def purchases():
    purchases = Purchase.query.order_by(Purchase.purchase_date.desc()).all()
    return render_template('purchases.html', purchases=purchases)

@app.route('/customers')
def customers():
    customers = Customer.query.all()
    return render_template('customers.html', customers=customers)

@app.route('/vendors')
def vendors():
    vendors = Vendor.query.all()
    return render_template('vendors.html', vendors=vendors)

@app.route('/notifications')
def notifications():
    return render_template('notifications.html')

@app.route('/report')
def report():
    return render_template('report.html')

# Customer API endpoints
@app.route('/api/customers', methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return jsonify([customer.to_dict() for customer in customers])

@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.json

    # Check if customer with GST ID already exists
    existing_customer = Customer.query.filter_by(gst_id=data['gst_id']).first()
    if existing_customer:
        return jsonify({'success': False, 'message': 'Customer with this GST ID already exists'}), 400

    customer = Customer(
        gst_id=data['gst_id'],
        name=data['name'],
        contact_person=data.get('contact_person', ''),
        phone=data.get('phone', ''),
        location=data['location'],
        about=data.get('about', '')
    )

    db.session.add(customer)
    db.session.commit()

    return jsonify({'success': True, 'customer': customer.to_dict()}), 201

@app.route('/api/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    data = request.json

    customer.name = data.get('name', customer.name)
    customer.contact_person = data.get('contact_person', customer.contact_person)
    customer.phone = data.get('phone', customer.phone)
    customer.location = data.get('location', customer.location)
    customer.about = data.get('about', customer.about)

    db.session.commit()

    return jsonify({'success': True, 'customer': customer.to_dict()})

@app.route('/api/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)

    # Check if customer has sales
    if customer.sales:
        return jsonify({'success': False, 'message': 'Cannot delete customer with sales records'}), 400

    db.session.delete(customer)
    db.session.commit()

    return jsonify({'success': True}), 200

# Vendor API endpoints
@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    vendors = Vendor.query.all()
    return jsonify([vendor.to_dict() for vendor in vendors])

@app.route('/api/vendors', methods=['POST'])
def add_vendor():
    data = request.json

    # Check if vendor with GST ID already exists
    existing_vendor = Vendor.query.filter_by(gst_id=data['gst_id']).first()
    if existing_vendor:
        return jsonify({'success': False, 'message': 'Vendor with this GST ID already exists'}), 400

    vendor = Vendor(
        gst_id=data['gst_id'],
        name=data['name'],
        contact_person=data.get('contact_person', ''),
        phone=data.get('phone', ''),
        location=data['location'],
        about=data.get('about', '')
    )

    db.session.add(vendor)
    db.session.commit()

    return jsonify({'success': True, 'vendor': vendor.to_dict()}), 201

@app.route('/api/vendors/<int:id>', methods=['PUT'])
def update_vendor(id):
    vendor = Vendor.query.get_or_404(id)
    data = request.json

    vendor.name = data.get('name', vendor.name)
    vendor.contact_person = data.get('contact_person', vendor.contact_person)
    vendor.phone = data.get('phone', vendor.phone)
    vendor.location = data.get('location', vendor.location)
    vendor.about = data.get('about', vendor.about)

    db.session.commit()

    return jsonify({'success': True, 'vendor': vendor.to_dict()})

@app.route('/api/vendors/<int:id>', methods=['DELETE'])
def delete_vendor(id):
    vendor = Vendor.query.get_or_404(id)

    # Check if vendor has purchases
    if vendor.purchases:
        return jsonify({'success': False, 'message': 'Cannot delete vendor with purchase records'}), 400

    db.session.delete(vendor)
    db.session.commit()

    return jsonify({'success': True}), 200

# Product API endpoints
@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json

    # Check if product with product ID already exists
    existing_product = Product.query.filter_by(product_id=data['product_id']).first()
    if existing_product:
        return jsonify({'success': False, 'message': 'Product with this ID already exists'}), 400

    product = Product(
        product_id=data['product_id'],
        name=data['name'],
        quantity=data['quantity'],
        cost_per_unit=data['cost_per_unit'],
        specifications=data.get('specifications', '')
    )

    db.session.add(product)
    db.session.commit()

    return jsonify({'success': True, 'product': product.to_dict()}), 201

@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.json

    product.name = data.get('name', product.name)
    product.quantity = data.get('quantity', product.quantity)
    product.cost_per_unit = data.get('cost_per_unit', product.cost_per_unit)
    product.specifications = data.get('specifications', product.specifications)

    db.session.commit()

    return jsonify({'success': True, 'product': product.to_dict()})

@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)

    # Check if product has sale items or purchase items
    if product.sale_items or product.purchase_items:
        return jsonify({'success': False, 'message': 'Cannot delete product with sales or purchase records'}), 400

    db.session.delete(product)
    db.session.commit()

    return jsonify({'success': True}), 200

# Sales API endpoints
@app.route('/api/sales', methods=['POST'])
def add_sale():
    data = request.json

    # Get customer
    customer = Customer.query.get(data['customer_id'])
    if not customer:
        return jsonify({'success': False, 'message': 'Customer not found'}), 404

    # Create sale
    sale = Sale(
        customer_id=customer.id,
        delivery_charges=data['delivery_charges'],
        total_amount=data['total_amount']
    )

    db.session.add(sale)

    # Add sale items
    for item_data in data['items']:
        product = Product.query.get(item_data['product_id'])
        if not product:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Product not found: {item_data["product_id"]}'}), 404
        
        # Check if enough stock
        if product.quantity < item_data['quantity']:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Not enough stock for product: {product.name}'}), 400
        
        # Update product quantity
        product.quantity -= item_data['quantity']
        
        # Create sale item
        sale_item = SaleItem(
            sale=sale,
            product_id=product.id,
            quantity=item_data['quantity'],
            gst_percentage=item_data['gst_percentage'],
            discount_percentage=item_data['discount_percentage'],
            unit_price=product.cost_per_unit,
            total_price=item_data['total_price']
        )
        
        db.session.add(sale_item)

    db.session.commit()

    return jsonify({'success': True, 'sale_id': sale.id}), 201

@app.route('/api/sales', methods=['GET'])
def get_sales():
    try:
        sales = Sale.query.all()
        print(f"Fetched {len(sales)} sales records from database")
        result = []

        for sale in sales:
            sale_data = {
                'id': sale.id,
                'customer_name': sale.customer.name,
                'customer_gst_id': sale.customer.gst_id,
                'sale_date': sale.sale_date.strftime('%Y-%m-%d %H:%M:%S'),
                'delivery_charges': sale.delivery_charges,
                'total_amount': sale.total_amount,
                'items': []
            }
            
            for item in sale.items:
                item_data = {
                    'product_name': item.product.name,
                    'product_id': item.product.product_id,
                    'quantity': item.quantity,
                    'gst_percentage': item.gst_percentage,
                    'discount_percentage': item.discount_percentage,
                    'unit_price': item.unit_price,
                    'total_price': item.total_price
                }
                sale_data['items'].append(item_data)
            
            result.append(sale_data)

        print(f"Returning {len(result)} formatted sales records")
        return jsonify(result)
    except Exception as e:
        print(f"Error in get_sales: {str(e)}")
        return jsonify([])

# Purchases API endpoints
@app.route('/api/purchases', methods=['POST'])
def add_purchase():
    data = request.json

    # Get vendor
    vendor = Vendor.query.get(data['vendor_id'])
    if not vendor:
        return jsonify({'success': False, 'message': 'Vendor not found'}), 404

    # Create purchase
    purchase = Purchase(
        vendor_id=vendor.id,
        order_id=data['order_id'],
        delivery_charges=data['delivery_charges'],
        total_amount=data['total_amount'],
        status=data['status']
    )

    if 'purchase_date' in data:
        purchase.purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d')

    db.session.add(purchase)

    # Add purchase items
    for item_data in data['items']:
        product = Product.query.get(item_data['product_id'])
        if not product:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Product not found: {item_data["product_id"]}'}), 404
        
        # Create purchase item
        purchase_item = PurchaseItem(
            purchase=purchase,
            product_id=product.id,
            quantity=item_data['quantity'],
            gst_percentage=item_data['gst_percentage'],
            unit_price=item_data['unit_price'],
            total_price=item_data['total_price']
        )
        
        db.session.add(purchase_item)
        
        # Update product quantity if purchase is delivered
        if data['status'] == 'Delivered':
            product.quantity += item_data['quantity']

    db.session.commit()

    return jsonify({'success': True, 'purchase_id': purchase.id}), 201

@app.route('/api/purchases', methods=['GET'])
def get_purchases():
    purchases = Purchase.query.all()
    result = []

    for purchase in purchases:
        purchase_data = {
            'id': purchase.id,
            'vendor_name': purchase.vendor.name,
            'vendor_gst_id': purchase.vendor.gst_id,
            'order_id': purchase.order_id,
            'purchase_date': purchase.purchase_date.strftime('%Y-%m-%d'),
            'delivery_charges': purchase.delivery_charges,
            'total_amount': purchase.total_amount,
            'status': purchase.status,
            'items': []
        }
        
        for item in purchase.items:
            item_data = {
                'product_name': item.product.name,
                'product_id': item.product.product_id,
                'quantity': item.quantity,
                'gst_percentage': item.gst_percentage,
                'unit_price': item.unit_price,
                'total_price': item.total_price
            }
            purchase_data['items'].append(item_data)
        
        result.append(purchase_data)

    return jsonify(result)

@app.route('/api/purchases/<int:id>', methods=['PUT'])
def update_purchase_status(id):
    purchase = Purchase.query.get_or_404(id)
    data = request.json

    old_status = purchase.status
    new_status = data.get('status', old_status)

    # If status is changing to Delivered, update product quantities
    if old_status != 'Delivered' and new_status == 'Delivered':
        for item in purchase.items:
            item.product.quantity += item.quantity

    # If status is changing from Delivered to something else, reduce product quantities
    if old_status == 'Delivered' and new_status != 'Delivered':
        for item in purchase.items:
            if item.product.quantity < item.quantity:
                return jsonify({'success': False, 'message': f'Not enough stock for product: {item.product.name}'}), 400
            item.product.quantity -= item.quantity

    purchase.status = new_status
    db.session.commit()

    return jsonify({'success': True})

# API endpoint for reports
@app.route('/api/reports', methods=['GET'])
def get_reports():
    # Fetch reports from the database
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return jsonify([report.to_dict() for report in reports])

@app.route('/api/reports', methods=['POST'])
def add_report():
    data = request.json
    
    # In a real application, this would save the report to the database
    # For this example, we'll just return success
    
    return jsonify({'success': True, 'report_id': 4})

@app.route('/api/reports/<int:id>', methods=['GET'])
def get_report(id):
    report = Report.query.get_or_404(id)
    return jsonify(report.to_dict())

# Create tables when the app starts
with app.app_context():
    db.create_all()

# Setup scheduler for daily reports
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(generate_daily_report, 'cron', hour=18, minute=0)
    scheduler.start()
    
    # Register a function to shut down the scheduler when the app is shutting down
    import atexit
    atexit.register(lambda: scheduler.shutdown())
    
except ImportError:
    print("APScheduler not installed. Daily reports will not be generated automatically.")

if __name__ == '__main__':
    app.run(debug=True)

