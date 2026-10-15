import pytest
from scarz_pos import create_app
from scarz_pos.extensions import db
from scarz_pos.models import Business, Product, User

@pytest.fixture()
def app():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret-long-enough', 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:', 'WTF_CSRF_ENABLED': False})
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

def register(client, email='demo@example.com', business='Demo Shop'):
    return client.post('/register', data={
        'business_name': business, 'full_name': 'Demo Owner', 'email': email,
        'password': 'very-long-password', 'confirm_password': 'very-long-password'
    }, follow_redirects=True)

def test_home_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'ScarZ POS' in response.data

def test_register_and_dashboard(client):
    response = register(client)
    assert response.status_code == 200
    assert b'Demo Shop' in response.data
    assert b'Your free trial is active' in response.data

def test_product_and_checkout_reduce_stock(client, app):
    register(client)
    response = client.post('/products', data={
        'name': 'Tea', 'sku': 'TEA-1', 'category': 'Groceries', 'cost_price': '2.00',
        'selling_price': '3.50', 'quantity': '10', 'low_stock_at': '2'
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        product = Product.query.filter_by(sku='TEA-1').one()
        product_id = product.id
    response = client.post('/checkout', data={f'qty_{product_id}': '2', 'payment_method': 'cash'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Sale complete' in response.data or b'SALE COMPLETE' in response.data
    with app.app_context():
        assert db.session.get(Product, product_id).quantity == 8
        from scarz_pos.models import StockMovement
        movements = StockMovement.query.filter_by(product_id=product_id).order_by(StockMovement.id).all()
        assert [(m.quantity_change, m.quantity_before, m.quantity_after) for m in movements] == [
            (10, 0, 10), (-2, 10, 8)
        ]

def test_tenant_cannot_read_other_business_receipt(client, app):
    register(client, 'first@example.com', 'First Shop')
    with app.app_context():
        business = Business(name='Other Shop')
        other = User(business=business, full_name='Other Owner', email='other@example.com')
        other.set_password('very-long-password')
        db.session.add_all([business, other])
        db.session.commit()
    response = client.get('/receipt/99999')
    assert response.status_code == 404

def test_health(client):
    assert client.get('/health/live').status_code == 200
    assert client.get('/health/ready').status_code == 200


def test_subscription_page_shows_server_configured_plan_state(client):
    register(client)
    response = client.get('/subscription')
    assert response.status_code == 200
    assert b'Subscription' in response.data
    assert b'not configured' in response.data.lower()


def test_unconfigured_subscription_plan_does_not_start_payment(client, app, monkeypatch):
    register(client)
    monkeypatch.delenv('SCARZ_POS_PLAN_MONTHLY_UGX', raising=False)
    response = client.post('/subscription', data={
        'plan': 'monthly',
        'phone_number': '0771234567',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'not configured' in response.data.lower()
    from scarz_pos.models import SubscriptionPayment
    with app.app_context():
        assert SubscriptionPayment.query.count() == 0

def _make_subscription_payment(app, amount='5000.00', reference='sub-test-reference'):
    from decimal import Decimal
    from scarz_pos.models import SubscriptionPayment
    with app.app_context():
        business = Business(name='Billing Test Shop')
        business.plan = 'trial'
        db.session.add(business)
        db.session.flush()
        payment = SubscriptionPayment(
            business_id=business.id,
            merchant_reference=reference,
            plan_key='monthly',
            duration_days=30,
            amount=Decimal(amount),
            currency='UGX',
            phone_number='256771234567',
            status='processing',
        )
        db.session.add(payment)
        db.session.commit()
        return business.id, payment.id


def _success_webhook(reference='sub-test-reference', amount='5000.00', currency='UGX'):
    return {
        'event': 'transaction.successful',
        'payload': {
            'reference': reference,
            'status': 'successful',
            'amount': amount,
            'currency': currency,
            'transactionId': 'nylon-txn-123',
        },
    }


def test_subscription_webhook_rejects_invalid_signature(client, app, monkeypatch):
    _make_subscription_payment(app)
    monkeypatch.setattr('scarz_pos.billing._verify_signature', lambda raw, signature: False)
    response = client.post(
        '/webhooks/nylonpay/subscriptions',
        json=_success_webhook(),
        headers={'x-nylon-signature': 'invalid'},
    )
    assert response.status_code == 401
    with app.app_context():
        from scarz_pos.models import SubscriptionPayment
        payment = SubscriptionPayment.query.filter_by(merchant_reference='sub-test-reference').one()
        assert payment.status == 'processing'
        assert payment.business.subscription_ends_at is None


def test_subscription_webhook_rejects_amount_mismatch(client, app, monkeypatch):
    _make_subscription_payment(app)
    monkeypatch.setattr('scarz_pos.billing._verify_signature', lambda raw, signature: True)
    response = client.post(
        '/webhooks/nylonpay/subscriptions',
        json=_success_webhook(amount='1.00'),
        headers={'x-nylon-signature': 'test-signature'},
    )
    assert response.status_code == 400
    with app.app_context():
        from scarz_pos.models import SubscriptionPayment
        payment = SubscriptionPayment.query.filter_by(merchant_reference='sub-test-reference').one()
        assert payment.status == 'processing'
        assert payment.business.subscription_ends_at is None


def test_subscription_webhook_requires_provider_amount_and_currency(client, app, monkeypatch):
    _make_subscription_payment(app)
    monkeypatch.setattr('scarz_pos.billing._verify_signature', lambda raw, signature: True)
    payload = _success_webhook()
    del payload['payload']['amount']
    response = client.post(
        '/webhooks/nylonpay/subscriptions',
        json=payload,
        headers={'x-nylon-signature': 'test-signature'},
    )
    assert response.status_code == 400
    with app.app_context():
        from scarz_pos.models import SubscriptionPayment
        payment = SubscriptionPayment.query.filter_by(merchant_reference='sub-test-reference').one()
        assert payment.status == 'processing'
        assert payment.business.subscription_ends_at is None


def test_successful_subscription_webhook_is_idempotent(client, app, monkeypatch):
    business_id, payment_id = _make_subscription_payment(app)
    monkeypatch.setattr('scarz_pos.billing._verify_signature', lambda raw, signature: True)
    payload = _success_webhook()
    headers = {'x-nylon-signature': 'test-signature'}

    first = client.post('/webhooks/nylonpay/subscriptions', json=payload, headers=headers)
    assert first.status_code == 200
    with app.app_context():
        business = db.session.get(Business, business_id)
        first_expiry = business.subscription_ends_at
        assert business.plan == 'monthly'
        assert first_expiry is not None
        from scarz_pos.models import SubscriptionPayment
        payment = db.session.get(SubscriptionPayment, payment_id)
        assert payment.status == 'successful'
        assert payment.provider_transaction_id == 'nylon-txn-123'

    second = client.post('/webhooks/nylonpay/subscriptions', json=payload, headers=headers)
    assert second.status_code == 200
    with app.app_context():
        business = db.session.get(Business, business_id)
        assert business.subscription_ends_at == first_expiry

def test_stock_adjustment_records_ledger_and_prevents_negative_stock(client, app):
    register(client)
    client.post('/products', data={
        'name': 'Coffee', 'sku': 'COF-1', 'category': 'Drinks',
        'cost_price': '1.00', 'selling_price': '2.00', 'quantity': '4',
        'low_stock_at': '1'
    }, follow_redirects=True)
    with app.app_context():
        product = Product.query.filter_by(sku='COF-1').one()
        product_id = product.id

    added = client.post('/stock', data={
        'product_id': str(product_id), 'quantity_change': '6',
        'reason': 'Supplier delivery'
    }, follow_redirects=True)
    assert added.status_code == 200
    with app.app_context():
        from scarz_pos.models import StockMovement
        product = db.session.get(Product, product_id)
        assert product.quantity == 10
        movement = StockMovement.query.filter_by(product_id=product_id).order_by(StockMovement.id.desc()).first()
        assert (movement.quantity_change, movement.quantity_before, movement.quantity_after) == (6, 4, 10)
        assert movement.reason == 'Supplier delivery'

    rejected = client.post('/stock', data={
        'product_id': str(product_id), 'quantity_change': '-11',
        'reason': 'Incorrect stock count'
    }, follow_redirects=True)
    assert rejected.status_code == 200
    with app.app_context():
        assert db.session.get(Product, product_id).quantity == 10
        assert StockMovement.query.filter_by(product_id=product_id).count() == 2


def test_stock_adjustment_cannot_change_another_business_product(client, app):
    register(client, 'owner-one@example.com', 'Owner One')
    with app.app_context():
        other_business = Business(name='Owner Two')
        db.session.add(other_business)
        db.session.flush()
        other_product = Product(
            business_id=other_business.id, name='Private item', sku='PRIVATE-1',
            category='General', cost_price='1.00', selling_price='2.00',
            quantity=7, low_stock_at=2
        )
        db.session.add(other_product)
        db.session.commit()
        other_product_id = other_product.id

    response = client.post('/stock', data={
        'product_id': str(other_product_id), 'quantity_change': '-3',
        'reason': 'Attempted cross-tenant change'
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Product, other_product_id).quantity == 7

def test_date_filtered_reports_include_revenue_cost_profit_and_expenses(client):
    register(client)
    client.post('/products', data={
        'name': 'Tea', 'sku': 'REPORT-TEA', 'category': 'Groceries',
        'cost_price': '2.00', 'selling_price': '3.50', 'quantity': '10',
        'low_stock_at': '2'
    }, follow_redirects=True)
    with client.application.app_context():
        product = Product.query.filter_by(sku='REPORT-TEA').one()
        product_id = product.id
    client.post('/checkout', data={f'qty_{product_id}': '2', 'payment_method': 'cash'}, follow_redirects=True)
    client.post('/expenses', data={'description': 'Packing materials', 'amount': '1.00'}, follow_redirects=True)

    response = client.get('/reports')
    assert response.status_code == 200
    assert b'Reports' in response.data
    assert b'7.00' in response.data
    assert b'4.00' in response.data
    assert b'3.00' in response.data
    assert b'1.00' in response.data
    assert b'2.00' in response.data

    csv_response = client.get('/reports.csv')
    assert csv_response.status_code == 200
    assert b'REPORT-TEA' not in csv_response.data
    assert b'Packing materials' in csv_response.data
    assert b'Estimated gross profit' in csv_response.data


def test_reports_reject_invalid_date_range(client):
    register(client)
    response = client.get('/reports?start=2026-12-31&end=2026-01-01')
    assert response.status_code == 302
    response = client.get('/reports.csv?start=not-a-date&end=2026-01-01')
    assert response.status_code == 400



def _make_sale_for_void(client, app, sku='VOID-TEA'):
    client.post('/products', data={
        'name': 'Void tea', 'sku': sku, 'category': 'Groceries',
        'cost_price': '2.00', 'selling_price': '3.50', 'quantity': '10',
        'low_stock_at': '2'
    }, follow_redirects=True)
    with app.app_context():
        product_id = Product.query.filter_by(sku=sku).one().id
    response = client.post('/checkout', data={f'qty_{product_id}': '2', 'payment_method': 'cash'}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        from scarz_pos.models import Sale
        return Sale.query.order_by(Sale.id.desc()).first().id, product_id


def test_void_sale_restores_inventory_once_and_is_excluded_from_reports(client, app):
    register(client)
    sale_id, product_id = _make_sale_for_void(client, app)
    response = client.post(f'/sales/{sale_id}/void', data={'reason': 'Duplicate checkout'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'SALE VOIDED' in response.data
    assert b'Duplicate checkout' in response.data

    with app.app_context():
        from scarz_pos.models import SaleVoid, StockMovement
        assert db.session.get(Product, product_id).quantity == 10
        assert SaleVoid.query.filter_by(sale_id=sale_id).count() == 1
        movement = StockMovement.query.filter_by(sale_id=sale_id).order_by(StockMovement.id.desc()).first()
        assert (movement.quantity_change, movement.quantity_before, movement.quantity_after) == (2, 8, 10)
        assert movement.reason == f'Void sale #{sale_id}: Duplicate checkout'

    client.post(f'/sales/{sale_id}/void', data={'reason': 'Repeat request'}, follow_redirects=True)
    with app.app_context():
        from scarz_pos.models import SaleVoid, StockMovement
        assert db.session.get(Product, product_id).quantity == 10
        assert SaleVoid.query.filter_by(sale_id=sale_id).count() == 1
        assert StockMovement.query.filter_by(sale_id=sale_id).count() == 2

    report = client.get('/reports')
    assert report.status_code == 200
    assert b'0 completed transactions' in report.data
    csv_response = client.get('/reports.csv')
    assert csv_response.status_code == 200
    assert not any(line.startswith(f'{sale_id},') for line in csv_response.data.decode('utf-8-sig').splitlines())


def test_void_sale_requires_reason_and_cannot_cross_business(client, app):
    register(client)
    sale_id, product_id = _make_sale_for_void(client, app, sku='VOID-REASON')
    response = client.post(f'/sales/{sale_id}/void', data={'reason': '   '}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        from scarz_pos.models import SaleVoid
        assert db.session.get(Product, product_id).quantity == 8
        assert SaleVoid.query.filter_by(sale_id=sale_id).count() == 0

        other_business = Business(name='Other business')
        db.session.add(other_business)
        db.session.flush()
        other_user = User(business_id=other_business.id, full_name='Other Owner', email='other-void@example.com')
        other_user.set_password('very-long-password')
        db.session.add(other_user)
        db.session.flush()
        other_product = Product(business_id=other_business.id, name='Private product', sku='PRIVATE-VOID', category='General', cost_price='1.00', selling_price='2.00', quantity=5, low_stock_at=1)
        db.session.add(other_product)
        db.session.flush()
        from scarz_pos.models import Sale, SaleItem
        other_sale = Sale(business_id=other_business.id, user_id=other_user.id, total='2.00', payment_method='cash')
        db.session.add(other_sale)
        db.session.flush()
        db.session.add(SaleItem(sale_id=other_sale.id, product_id=other_product.id, product_name='Private product', quantity=1, unit_price='2.00', unit_cost='1.00'))
        db.session.commit()
        other_sale_id, other_product_id = other_sale.id, other_product.id

    response = client.post(f'/sales/{other_sale_id}/void', data={'reason': 'Cross tenant attempt'}, follow_redirects=True)
    assert response.status_code == 404
    with app.app_context():
        from scarz_pos.models import SaleVoid
        assert db.session.get(Product, other_product_id).quantity == 5
        assert SaleVoid.query.filter_by(sale_id=other_sale_id).count() == 0



def test_dashboard_and_reports_render_analytics_charts_and_ignore_voided_sales(client, app):
    import html
    import json
    import re

    register(client)
    sale_id, product_id = _make_sale_for_void(client, app, sku='GRAPH-TEA')
    client.post(f'/sales/{sale_id}/void', data={'reason': 'Graph exclusion check'}, follow_redirects=True)

    # Keep one completed sale so the graph proves it excludes only the voided transaction.
    client.post('/checkout', data={f'qty_{product_id}': '1', 'payment_method': 'cash'}, follow_redirects=True)

    dashboard = client.get('/dashboard')
    assert dashboard.status_code == 200
    assert b'data-chart="line"' in dashboard.data
    assert b'data-chart="bars"' in dashboard.data
    dashboard_match = re.search(rb'data-chart="line"[^>]*data-chart-data="([^"]+)"', dashboard.data)
    assert dashboard_match
    dashboard_rows = json.loads(html.unescape(dashboard_match.group(1).decode()))
    assert sum(row['revenue'] for row in dashboard_rows) == 3.5

    reports = client.get('/reports')
    assert reports.status_code == 200
    assert b'Revenue & profitability trend' in reports.data
    assert b'data-chart="line"' in reports.data
    assert b'data-chart="bars"' in reports.data
    assert b'1 completed transactions' in reports.data
    report_match = re.search(rb'data-chart="line"[^>]*data-chart-data="([^"]+)"', reports.data)
    assert report_match
    report_rows = json.loads(html.unescape(report_match.group(1).decode()))
    assert sum(row['revenue'] for row in report_rows) == 3.5
    assert sum(row['gross_profit'] for row in report_rows) == 1.5


def test_product_barcode_is_saved_and_unique_within_business(client, app):
    register(client)
    first = client.post('/products', data={
        'name': 'Barcode tea', 'sku': 'BAR-TEA-1', 'barcode': '0123456789012',
        'category': 'Groceries', 'cost_price': '2.00', 'selling_price': '3.50',
        'quantity': '10', 'low_stock_at': '2'
    }, follow_redirects=True)
    assert first.status_code == 200
    with app.app_context():
        product = Product.query.filter_by(barcode='0123456789012').one()
        assert product.sku == 'BAR-TEA-1'
        product_id = product.id

    checkout = client.get('/checkout')
    assert checkout.status_code == 200
    assert b'id="product-search"' in checkout.data
    assert b'data-product-barcode="0123456789012"' in checkout.data
    assert b'data-barcode-scanner' in checkout.data

    duplicate = client.post('/products', data={
        'name': 'Duplicate barcode item', 'sku': 'BAR-TEA-2', 'barcode': '0123456789012',
        'category': 'Groceries', 'cost_price': '1.00', 'selling_price': '2.00',
        'quantity': '3', 'low_stock_at': '1'
    }, follow_redirects=True)
    assert duplicate.status_code == 200
    assert b'barcode must each be unique' in duplicate.data
    with app.app_context():
        assert Product.query.filter_by(barcode='0123456789012').count() == 1
        assert db.session.get(Product, product_id).quantity == 10


def test_phone_scanner_pairing_sends_barcode_to_own_checkout(client, app):
    register(client, 'phone-owner@example.com', 'Phone Shop')
    paired = client.post('/scanner/pair')
    assert paired.status_code == 200
    payload = paired.get_json()
    assert payload['token']
    assert payload['expires_in'] == 1200
    phone_page = client.get('/scanner/phone/' + payload['token'])
    assert phone_page.status_code == 200
    assert b'Phone barcode scanner' in phone_page.data

    first_sent = client.post('/scanner/phone/' + payload['token'] + '/code', json={'code': '5012345678900'})
    second_sent = client.post('/scanner/phone/' + payload['token'] + '/code', json={'code': '4006381333931'})
    assert first_sent.status_code == second_sent.status_code == 200
    first_received = client.get('/scanner/pair/' + payload['token'] + '/next')
    second_received = client.get('/scanner/pair/' + payload['token'] + '/next')
    assert first_received.status_code == second_received.status_code == 200
    assert first_received.get_json()['code'] == '5012345678900'
    assert second_received.get_json()['code'] == '4006381333931'
    empty = client.get('/scanner/pair/' + payload['token'] + '/next')
    assert empty.status_code == 200
    assert empty.get_json()['code'] is None


def test_phone_scanner_pairing_is_scoped_to_business(client, app):
    register(client, 'scanner-first@example.com', 'First Shop')
    token = client.post('/scanner/pair').get_json()['token']

    # Create a genuinely separate tenant and explicitly authenticate that user.
    # Using the register helper here made this test dependent on registration's
    # redirect/session behavior rather than isolating the tenant authorization.
    with app.app_context():
        business = Business(name='Second Shop')
        other_user = User(
            business=business,
            full_name='Second Owner',
            email='scanner-second@example.com',
        )
        other_user.set_password('very-long-password')
        db.session.add_all([business, other_user])
        db.session.commit()
        other_user_id = other_user.id

    second_client = app.test_client()
    with second_client.session_transaction() as session:
        session['_user_id'] = str(other_user_id)
        session['_fresh'] = True

    response = second_client.get('/scanner/pair/' + token + '/next')
    assert response.status_code == 404


def test_phone_scanner_rejects_invalid_barcode(client, app):
    register(client, 'scanner-validation@example.com', 'Scanner Validation Shop')
    token = client.post('/scanner/pair').get_json()['token']
    assert client.post('/scanner/phone/' + token + '/code', json={'code': ''}).status_code == 400
    assert client.post('/scanner/phone/' + token + '/code', json={'code': 'x' * 81}).status_code == 400


def test_report_csv_neutralizes_spreadsheet_formula_in_expense_descriptions(client):
    register(client, 'csv-safety@example.com', 'CSV Safety Shop')
    response = client.post('/expenses', data={
        'description': '=HYPERLINK("https://example.com","click")',
        'amount': '12.00',
    }, follow_redirects=True)
    assert response.status_code == 200

    exported = client.get('/reports.csv')
    assert exported.status_code == 200
    assert b'\'=HYPERLINK' in exported.data
    assert b'=HYPERLINK("https://example.com","click")' not in exported.data
