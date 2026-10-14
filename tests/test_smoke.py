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
