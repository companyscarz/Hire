from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from .extensions import db
from .models import Expense, Product, Sale, SaleItem

bp = Blueprint('views', __name__)


def money(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0:
            raise InvalidOperation
        return amount.quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('Enter a valid non-negative amount.')


def require_active_subscription():
    business = current_user.business
    if not business.subscription_active:
        flash('Your trial or subscription has expired. Subscription checkout will be enabled after Nylon Pay integration is verified.', 'error')
        abort(402)


@bp.get('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    return render_template('home.html')


@bp.get('/dashboard')
@login_required
def dashboard():
    bid = current_user.business_id
    today = datetime.now(timezone.utc).date()
    sales = db.session.query(func.coalesce(func.sum(Sale.total), 0)).filter(Sale.business_id == bid, func.date(Sale.created_at) == today).scalar()
    count = Sale.query.filter_by(business_id=bid).count()
    products = Product.query.filter_by(business_id=bid, active=True).order_by(Product.name).all()
    low_stock = [p for p in products if p.quantity <= p.low_stock_at]
    expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(Expense.business_id == bid, func.date(Expense.created_at) == today).scalar()
    recent = Sale.query.filter_by(business_id=bid).order_by(Sale.created_at.desc()).limit(8).all()
    return render_template('dashboard.html', sales=sales, sale_count=count, products=products, low_stock=low_stock, expenses=expenses, recent=recent)


@bp.route('/products', methods=['GET', 'POST'])
@login_required
def products():
    if request.method == 'POST':
        require_active_subscription()
        try:
            name = request.form.get('name', '').strip()
            sku = request.form.get('sku', '').strip() or None
            category = request.form.get('category', '').strip() or 'General'
            cost = money(request.form.get('cost_price', '0'))
            price = money(request.form.get('selling_price', ''))
            quantity = int(request.form.get('quantity', '0'))
            low_stock = int(request.form.get('low_stock_at', '5'))
            if not name or len(name) > 160 or quantity < 0 or low_stock < 0:
                raise ValueError('Check the product name and stock quantities.')
            product = Product(business_id=current_user.business_id, name=name, sku=sku, category=category[:80], cost_price=cost, selling_price=price, quantity=quantity, low_stock_at=low_stock)
            db.session.add(product)
            db.session.commit()
            flash('Product saved.', 'success')
            return redirect(url_for('views.products'))
        except (ValueError, InvalidOperation):
            db.session.rollback()
            flash('Please check the product details. SKU must be unique within your business.', 'error')
    items = Product.query.filter_by(business_id=current_user.business_id).order_by(Product.name).all()
    return render_template('products.html', products=items)


@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    available = Product.query.filter_by(business_id=current_user.business_id, active=True).order_by(Product.name).all()
    if request.method == 'POST':
        require_active_subscription()
        try:
            quantities = {}
            for key, value in request.form.items():
                if key.startswith('qty_') and value.strip():
                    pid = int(key[4:]); qty = int(value)
                    if qty < 0:
                        raise ValueError('Quantity cannot be negative.')
                    if qty:
                        quantities[pid] = quantities.get(pid, 0) + qty
            if not quantities:
                raise ValueError('Enter a quantity for at least one item.')
            ids = sorted(quantities)
            selected = Product.query.filter(Product.business_id == current_user.business_id, Product.active.is_(True), Product.id.in_(ids)).order_by(Product.id).with_for_update().all()
            if len(selected) != len(ids):
                raise ValueError('One or more selected products are unavailable.')
            total = Decimal('0.00')
            lines = []
            for product in selected:
                qty = quantities[product.id]
                if product.quantity < qty:
                    raise ValueError(f'Not enough stock for {product.name}.')
                total += product.selling_price * qty
                lines.append((product, qty))
            method = request.form.get('payment_method', 'cash')
            if method not in {'cash', 'mobile_money', 'card', 'other'}:
                raise ValueError('Choose a valid payment method.')
            sale = Sale(business_id=current_user.business_id, user_id=current_user.id, total=total, payment_method=method)
            db.session.add(sale)
            db.session.flush()
            for product, qty in lines:
                db.session.add(SaleItem(sale_id=sale.id, product_id=product.id, product_name=product.name, quantity=qty, unit_price=product.selling_price, unit_cost=product.cost_price))
                product.quantity -= qty
            db.session.commit()
            flash(f'Sale #{sale.id} completed.', 'success')
            return redirect(url_for('views.receipt', sale_id=sale.id))
        except (ValueError, InvalidOperation) as exc:
            db.session.rollback()
            flash(str(exc) or 'Please check quantities and try again.', 'error')
    return render_template('checkout.html', products=available)


@bp.get('/sales')
@login_required
def sales():
    items = Sale.query.filter_by(business_id=current_user.business_id).order_by(Sale.created_at.desc()).limit(200).all()
    return render_template('sales.html', sales=items)


@bp.get('/receipt/<int:sale_id>')
@login_required
def receipt(sale_id):
    sale = Sale.query.filter_by(id=sale_id, business_id=current_user.business_id).first_or_404()
    return render_template('receipt.html', sale=sale)


@bp.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    if request.method == 'POST':
        require_active_subscription()
        description = request.form.get('description', '').strip()
        try:
            amount = money(request.form.get('amount', ''))
            if not description or len(description) > 200:
                raise ValueError('Enter an expense description.')
            db.session.add(Expense(business_id=current_user.business_id, user_id=current_user.id, description=description, amount=amount))
            db.session.commit()
            flash('Expense saved.', 'success')
            return redirect(url_for('views.expenses'))
        except ValueError:
            db.session.rollback()
            flash('Enter a valid description and amount.', 'error')
    items = Expense.query.filter_by(business_id=current_user.business_id).order_by(Expense.created_at.desc()).limit(100).all()
    return render_template('expenses.html', expenses=items)


@bp.get('/reports.csv')
@login_required
def reports_csv():
    import csv, io
    from flask import Response
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Sale ID', 'Date (UTC)', 'Payment method', 'Total', 'Items', 'Estimated gross profit'])
    items = Sale.query.filter_by(business_id=current_user.business_id).order_by(Sale.created_at.desc()).limit(5000).all()
    for sale in items:
        units = sum(i.quantity for i in sale.items)
        profit = sum((i.unit_price - i.unit_cost) * i.quantity for i in sale.items)
        writer.writerow([sale.id, sale.created_at.isoformat(), sale.payment_method, sale.total, units, profit])
    return Response('\ufeff' + output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=scarz-pos-sales.csv'})
