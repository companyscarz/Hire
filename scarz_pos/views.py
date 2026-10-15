from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from .extensions import db
from .models import Expense, Product, Sale, SaleItem, SaleVoid, StockMovement

bp = Blueprint('views', __name__)


def money(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount < 0:
            raise InvalidOperation
        return amount.quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('Enter a valid non-negative amount.')


def csv_safe_text(value):
    """Prevent spreadsheet formula execution when user-controlled text is exported."""
    text_value = str(value or "")
    if text_value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
        return "'" + text_value
    return text_value


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
    tomorrow = today + timedelta(days=1)
    start_day = today - timedelta(days=6)
    start_at = datetime.combine(start_day, time.min, tzinfo=timezone.utc)
    today_at = datetime.combine(today, time.min, tzinfo=timezone.utc)
    end_at = datetime.combine(tomorrow, time.min, tzinfo=timezone.utc)
    valid_sale = ~Sale.id.in_(db.session.query(SaleVoid.sale_id))

    sales = db.session.query(func.coalesce(func.sum(Sale.total), 0)).filter(
        Sale.business_id == bid, Sale.created_at >= today_at, Sale.created_at < end_at, valid_sale,
    ).scalar()
    count = Sale.query.filter(
        Sale.business_id == bid, Sale.created_at >= today_at, Sale.created_at < end_at, valid_sale,
    ).count()
    products = Product.query.filter_by(business_id=bid, active=True).order_by(Product.name).all()
    low_stock = [p for p in products if p.quantity <= p.low_stock_at]
    expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.business_id == bid, Expense.created_at >= today_at, Expense.created_at < end_at,
    ).scalar()
    recent = Sale.query.filter_by(business_id=bid).filter(
        valid_sale
    ).order_by(Sale.created_at.desc()).limit(8).all()

    daily_sales = db.session.query(
        func.date(Sale.created_at), func.coalesce(func.sum(Sale.total), 0)
    ).filter(
        Sale.business_id == bid, Sale.created_at >= start_at, Sale.created_at < end_at, valid_sale,
    ).group_by(func.date(Sale.created_at)).all()
    daily_map = {str(day)[:10]: float(total or 0) for day, total in daily_sales}
    dashboard_chart = [
        {'label': (start_day + timedelta(days=offset)).strftime('%d %b'),
         'revenue': daily_map.get((start_day + timedelta(days=offset)).isoformat(), 0)}
        for offset in range(7)
    ]

    product_rows = db.session.query(
        SaleItem.product_name,
        func.coalesce(func.sum(SaleItem.quantity), 0),
        func.coalesce(func.sum(SaleItem.quantity * SaleItem.unit_price), 0),
    ).join(Sale, Sale.id == SaleItem.sale_id).filter(
        Sale.business_id == bid,
        Sale.created_at >= datetime.combine(today - timedelta(days=29), time.min, tzinfo=timezone.utc),
        Sale.created_at < end_at, valid_sale,
    ).group_by(SaleItem.product_name).order_by(
        func.sum(SaleItem.quantity).desc(), SaleItem.product_name
    ).limit(5).all()
    top_products = [
        {'label': name, 'quantity': int(quantity or 0), 'revenue': float(revenue or 0)}
        for name, quantity, revenue in product_rows
    ]
    return render_template(
        'dashboard.html', sales=sales, sale_count=count, products=products,
        low_stock=low_stock, expenses=expenses, recent=recent,
        dashboard_chart=dashboard_chart, top_products=top_products,
    )

@bp.route('/products', methods=['GET', 'POST'])
@login_required
def products():
    if request.method == 'POST':
        require_active_subscription()
        try:
            name = request.form.get('name', '').strip()
            sku = request.form.get('sku', '').strip() or None
            barcode = request.form.get('barcode', '').strip() or None
            category = request.form.get('category', '').strip() or 'General'
            cost = money(request.form.get('cost_price', '0'))
            price = money(request.form.get('selling_price', ''))
            quantity = int(request.form.get('quantity', '0'))
            low_stock = int(request.form.get('low_stock_at', '5'))
            if not name or len(name) > 160 or quantity < 0 or low_stock < 0 or (barcode and len(barcode) > 80):
                raise ValueError('Check the product name, barcode and stock quantities.')
            product = Product(business_id=current_user.business_id, name=name, sku=sku, barcode=barcode, category=category[:80], cost_price=cost, selling_price=price, quantity=quantity, low_stock_at=low_stock)
            db.session.add(product)
            db.session.flush()
            if quantity > 0:
                db.session.add(StockMovement(
                    business_id=current_user.business_id,
                    product_id=product.id,
                    user_id=current_user.id,
                    quantity_change=quantity,
                    quantity_before=0,
                    quantity_after=quantity,
                    reason='Opening stock',
                ))
            db.session.commit()
            flash('Product saved.', 'success')
            return redirect(url_for('views.products'))
        except (ValueError, InvalidOperation, IntegrityError):
            db.session.rollback()
            flash('Please check the product details. SKU and barcode must each be unique within your business.', 'error')
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
                before = product.quantity
                db.session.add(SaleItem(sale_id=sale.id, product_id=product.id, product_name=product.name, quantity=qty, unit_price=product.selling_price, unit_cost=product.cost_price))
                product.quantity -= qty
                db.session.add(StockMovement(
                    business_id=current_user.business_id,
                    product_id=product.id,
                    user_id=current_user.id,
                    sale_id=sale.id,
                    quantity_change=-qty,
                    quantity_before=before,
                    quantity_after=product.quantity,
                    reason=f'Sale #{sale.id}',
                ))
            db.session.commit()
            flash(f'Sale #{sale.id} completed.', 'success')
            return redirect(url_for('views.receipt', sale_id=sale.id))
        except (ValueError, InvalidOperation) as exc:
            db.session.rollback()
            flash(str(exc) or 'Please check quantities and try again.', 'error')
    return render_template('checkout.html', products=available)


@bp.route('/stock', methods=['GET', 'POST'])
@login_required
def stock_history():
    if request.method == 'POST':
        require_active_subscription()
        try:
            product_id = int(request.form.get('product_id', ''))
            change = int(request.form.get('quantity_change', '0'))
            reason = request.form.get('reason', '').strip()
            if change == 0:
                raise ValueError('Enter a stock change other than zero.')
            if not reason or len(reason) > 200:
                raise ValueError('Enter a reason of up to 200 characters.')
            product = Product.query.filter_by(
                id=product_id, business_id=current_user.business_id
            ).with_for_update().first()
            if product is None:
                raise ValueError('Choose a product from your inventory.')
            before = product.quantity
            after = before + change
            if after < 0:
                raise ValueError(f'Cannot remove {-change} units; only {before} are in stock.')
            product.quantity = after
            db.session.add(StockMovement(
                business_id=current_user.business_id,
                product_id=product.id,
                user_id=current_user.id,
                quantity_change=change,
                quantity_before=before,
                quantity_after=after,
                reason=reason,
            ))
            db.session.commit()
            flash('Stock adjustment saved and recorded.', 'success')
            return redirect(url_for('views.stock_history'))
        except (ValueError, InvalidOperation) as exc:
            db.session.rollback()
            flash(str(exc) or 'Check the stock adjustment details.', 'error')

    products = Product.query.filter_by(
        business_id=current_user.business_id
    ).order_by(Product.name).all()
    movements = StockMovement.query.filter_by(
        business_id=current_user.business_id
    ).order_by(StockMovement.created_at.desc(), StockMovement.id.desc()).limit(200).all()
    return render_template('stock.html', products=products, movements=movements)


@bp.get('/sales')
@login_required
def sales():
    items = Sale.query.filter_by(business_id=current_user.business_id).order_by(Sale.created_at.desc()).limit(200).all()
    return render_template('sales.html', sales=items)


@bp.post('/sales/<int:sale_id>/void')
@login_required
def void_sale(sale_id):
    """Void a completed sale once, restore its inventory, and retain an audit trail."""
    reason = request.form.get('reason', '').strip()
    if not reason or len(reason) > 240:
        flash('Enter a reason for voiding this sale (up to 240 characters).', 'error')
        return redirect(url_for('views.receipt', sale_id=sale_id))

    try:
        sale = Sale.query.filter_by(
            id=sale_id, business_id=current_user.business_id
        ).with_for_update().first_or_404()
        existing = SaleVoid.query.filter_by(sale_id=sale.id).first()
        if existing is not None:
            flash(f'Sale #{sale.id} has already been voided; stock was not restored again.', 'error')
            return redirect(url_for('views.receipt', sale_id=sale.id))

        db.session.add(SaleVoid(
            business_id=current_user.business_id,
            sale_id=sale.id,
            user_id=current_user.id,
            reason=reason,
        ))
        db.session.flush()

        for item in sale.items:
            product = Product.query.filter_by(
                id=item.product_id, business_id=current_user.business_id
            ).with_for_update().first()
            if product is None:
                raise ValueError(
                    f'Cannot safely restore stock for sale #{sale.id}: '
                    f'product record for {item.product_name} is missing.'
                )
            before = product.quantity
            after = before + item.quantity
            product.quantity = after
            db.session.add(StockMovement(
                business_id=current_user.business_id,
                product_id=product.id,
                user_id=current_user.id,
                sale_id=sale.id,
                quantity_change=item.quantity,
                quantity_before=before,
                quantity_after=after,
                reason=f'Void sale #{sale.id}: {reason}'[:200],
            ))
        db.session.commit()
        flash(f'Sale #{sale.id} voided. Inventory restored and audit record saved.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('This sale has already been voided; no additional stock restoration was applied.', 'error')
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), 'error')
    return redirect(url_for('views.receipt', sale_id=sale_id))


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


def report_period():
    """Parse inclusive date filters into a half-open UTC interval."""
    today = datetime.now(timezone.utc).date()
    default_start = today.replace(day=1)
    raw_start = request.args.get('start', default_start.isoformat())
    raw_end = request.args.get('end', today.isoformat())
    try:
        start_date = date.fromisoformat(raw_start)
        end_date = date.fromisoformat(raw_end)
    except (TypeError, ValueError):
        raise ValueError('Use valid start and end dates.')
    if end_date < start_date:
        raise ValueError('The end date must be on or after the start date.')
    if (end_date - start_date).days > 366:
        raise ValueError('Choose a date range of 366 days or fewer.')
    start_at = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_at = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return start_date, end_date, start_at, end_at


def report_data(start_at, end_at):
    bid = current_user.business_id
    valid_sale = ~Sale.id.in_(db.session.query(SaleVoid.sale_id))
    sales_count, revenue = db.session.query(
        func.count(Sale.id), func.coalesce(func.sum(Sale.total), 0),
    ).filter(
        Sale.business_id == bid, valid_sale,
        Sale.created_at >= start_at, Sale.created_at < end_at,
    ).one()
    cost = db.session.query(
        func.coalesce(func.sum(SaleItem.quantity * SaleItem.unit_cost), 0)
    ).join(Sale, Sale.id == SaleItem.sale_id).filter(
        Sale.business_id == bid, valid_sale,
        Sale.created_at >= start_at, Sale.created_at < end_at,
    ).scalar()
    expense_total = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.business_id == bid, Expense.created_at >= start_at, Expense.created_at < end_at,
    ).scalar()
    payment_rows = db.session.query(
        Sale.payment_method, func.count(Sale.id), func.coalesce(func.sum(Sale.total), 0),
    ).filter(
        Sale.business_id == bid, valid_sale,
        Sale.created_at >= start_at, Sale.created_at < end_at,
    ).group_by(Sale.payment_method).order_by(Sale.payment_method).all()
    daily_rows = db.session.query(
        func.date(Sale.created_at), func.count(Sale.id), func.coalesce(func.sum(Sale.total), 0),
    ).filter(
        Sale.business_id == bid, valid_sale,
        Sale.created_at >= start_at, Sale.created_at < end_at,
    ).group_by(func.date(Sale.created_at)).order_by(func.date(Sale.created_at)).all()

    daily_revenue_rows = db.session.query(
        func.date(Sale.created_at), func.coalesce(func.sum(Sale.total), 0),
    ).filter(
        Sale.business_id == bid, valid_sale,
        Sale.created_at >= start_at, Sale.created_at < end_at,
    ).group_by(func.date(Sale.created_at)).all()
    daily_cost_rows = db.session.query(
        func.date(Sale.created_at),
        func.coalesce(func.sum(SaleItem.quantity * SaleItem.unit_cost), 0),
    ).join(Sale, Sale.id == SaleItem.sale_id).filter(
        Sale.business_id == bid, valid_sale,
        Sale.created_at >= start_at, Sale.created_at < end_at,
    ).group_by(func.date(Sale.created_at)).all()
    daily_expense_rows = db.session.query(
        func.date(Expense.created_at), func.coalesce(func.sum(Expense.amount), 0),
    ).filter(
        Expense.business_id == bid, Expense.created_at >= start_at, Expense.created_at < end_at,
    ).group_by(func.date(Expense.created_at)).all()

    revenue_map = {str(day)[:10]: float(value or 0) for day, value in daily_revenue_rows}
    cost_map = {str(day)[:10]: float(value or 0) for day, value in daily_cost_rows}
    expense_map = {str(day)[:10]: float(value or 0) for day, value in daily_expense_rows}
    chart_rows = []
    cursor = start_at.date()
    last_day = end_at.date() - timedelta(days=1)
    while cursor <= last_day:
        key = cursor.isoformat()
        day_revenue = revenue_map.get(key, 0.0)
        day_cost = cost_map.get(key, 0.0)
        day_expenses = expense_map.get(key, 0.0)
        chart_rows.append({
            'label': key, 'revenue': round(day_revenue, 2),
            'gross_profit': round(day_revenue - day_cost, 2),
            'expenses': round(day_expenses, 2),
            'net_estimate': round(day_revenue - day_cost - day_expenses, 2),
        })
        cursor += timedelta(days=1)

    revenue = Decimal(str(revenue or 0))
    cost = Decimal(str(cost or 0))
    expense_total = Decimal(str(expense_total or 0))
    gross_profit = revenue - cost
    return {
        'sales_count': sales_count,
        'revenue': revenue,
        'cost': cost,
        'gross_profit': gross_profit,
        'expenses': expense_total,
        'net_estimate': gross_profit - expense_total,
        'payment_rows': payment_rows,
        'daily_rows': daily_rows,
        'chart_rows': chart_rows,
        'payment_chart': [
            {'label': method.replace('_', ' ').title(), 'revenue': float(total or 0), 'transactions': int(count or 0)}
            for method, count, total in payment_rows
        ],
    }

@bp.get('/reports')
@login_required
def reports():
    try:
        start_date, end_date, start_at, end_at = report_period()
    except ValueError as exc:
        flash(str(exc), 'error')
        today = datetime.now(timezone.utc).date()
        return redirect(url_for('views.reports', start=today.replace(day=1).isoformat(), end=today.isoformat()))
    data = report_data(start_at, end_at)
    return render_template(
        'reports.html',
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        report=data,
    )


@bp.get('/reports.csv')
@login_required
def reports_csv():
    import csv, io
    from flask import Response
    try:
        start_date, end_date, start_at, end_at = report_period()
    except ValueError as exc:
        abort(400, description=str(exc))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Report start (UTC)', start_date.isoformat()])
    writer.writerow(['Report end (UTC)', end_date.isoformat()])
    writer.writerow([])
    writer.writerow(['Sale ID', 'Date (UTC)', 'Payment method', 'Total', 'Items', 'Cost of goods', 'Estimated gross profit'])
    items = Sale.query.filter(
        Sale.business_id == current_user.business_id,
        ~Sale.id.in_(db.session.query(SaleVoid.sale_id)),
        Sale.created_at >= start_at,
        Sale.created_at < end_at,
    ).order_by(Sale.created_at.desc()).all()
    for sale in items:
        units = sum(i.quantity for i in sale.items)
        cost = sum(i.unit_cost * i.quantity for i in sale.items)
        profit = sum((i.unit_price - i.unit_cost) * i.quantity for i in sale.items)
        writer.writerow([sale.id, sale.created_at.isoformat(), sale.payment_method, sale.total, units, cost, profit])
    writer.writerow([])
    writer.writerow(['Expenses (date UTC)', 'Description', 'Amount'])
    expenses = Expense.query.filter(
        Expense.business_id == current_user.business_id,
        Expense.created_at >= start_at,
        Expense.created_at < end_at,
    ).order_by(Expense.created_at.desc()).all()
    for expense in expenses:
        writer.writerow([expense.created_at.isoformat(), csv_safe_text(expense.description), expense.amount])
    return Response(
        '\ufeff' + output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=scarz-pos-report-{start_date.isoformat()}-to-{end_date.isoformat()}.csv'},
    )

