import os
from datetime import timedelta
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import inspect, text
from .extensions import db, login_manager

migrate = Migrate()
csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    database_url = os.getenv('DATABASE_URL', 'sqlite:///scarz_pos.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-only-change-this-secret'),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.getenv('APP_ENV') == 'production',
        PERMANENT_SESSION_LIFETIME=timedelta(days=14),
        REMEMBER_COOKIE_DURATION=timedelta(days=14),
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE='Lax',
        REMEMBER_COOKIE_SECURE=os.getenv('APP_ENV') == 'production',
        WTF_CSRF_TIME_LIMIT=3600,
    )
    if test_config:
        app.config.update(test_config)
    if app.config['SECRET_KEY'] == 'dev-only-change-this-secret' and os.getenv('APP_ENV') == 'production':
        raise RuntimeError('SECRET_KEY must be set in production')
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    from . import models
    from .auth import bp as auth_bp
    from .views import bp as views_bp
    from .billing import bp as billing_bp
    from .scanner import bp as scanner_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(scanner_bp)

    @app.cli.command('init-db')
    def init_db_command():
        """Create missing tables and apply the additive barcode schema update."""
        db.create_all()
        product_columns = {column['name'] for column in inspect(db.engine).get_columns('product')}
        if 'barcode' not in product_columns:
            db.session.execute(text('ALTER TABLE product ADD COLUMN barcode VARCHAR(80)'))
            db.session.commit()
        db.session.execute(text(
            'CREATE UNIQUE INDEX IF NOT EXISTS uq_product_business_barcode '
            'ON product (business_id, barcode)'
        ))
        scanner_columns = {column['name'] for column in inspect(db.engine).get_columns('phone_scanner_session')}
        if 'pending_codes' not in scanner_columns:
            db.session.execute(text(
                "ALTER TABLE phone_scanner_session ADD COLUMN pending_codes JSON NOT NULL DEFAULT '[]'"
            ))
            db.session.commit()
        db.session.commit()
        print('ScarZ POS tables are present; barcode and wireless-scanner schemas are ready.')

    @app.get('/health/live')
    def health_live():
        return {'status': 'ok', 'service': 'scarz-pos'}, 200

    @app.get('/health/ready')
    def health_ready():
        try:
            db.session.execute(text('SELECT 1'))
            return {'status': 'ready'}, 200
        except Exception:
            db.session.rollback()
            return {'status': 'not_ready'}, 503

    @app.errorhandler(404)
    def not_found(_error):
        return render_template('error.html', code=404, message='That page could not be found.'), 404

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        return render_template('error.html', code=500, message='Something went wrong. Please try again.'), 500

    return app
