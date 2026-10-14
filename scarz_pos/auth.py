from datetime import datetime, timezone
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func
from .extensions import db
from .models import Business, User

bp = Blueprint('auth', __name__)


def safe_next(value):
    # Only allow local relative paths to prevent open redirects.
    if value and value.startswith('/') and not value.startswith('//') and '\\' not in value:
        return value
    return url_for('views.dashboard')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    if request.method == 'POST':
        name = request.form.get('business_name', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if not all([name, full_name, email, password]):
            flash('Please complete every required field.', 'error')
        elif len(name) > 120 or len(full_name) > 120 or len(email) > 254:
            flash('One of those fields is too long.', 'error')
        elif len(password) < 10:
            flash('Use a password with at least 10 characters.', 'error')
        elif password != confirm:
            flash('The passwords do not match.', 'error')
        elif User.query.filter(func.lower(User.email) == email).first():
            flash('An account with that email already exists.', 'error')
        else:
            business = Business(name=name)
            user = User(business=business, full_name=full_name, email=email, role='owner')
            user.set_password(password)
            db.session.add_all([business, user])
            db.session.commit()
            login_user(user, remember=True, fresh=True)
            flash('Your 14-day trial has started. Add your first product to begin.', 'success')
            return redirect(url_for('views.dashboard'))
    return render_template('register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter(func.lower(User.email) == email).first()
        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember') == 'on', fresh=True)
            return redirect(safe_next(request.args.get('next')))
        flash('Email or password is incorrect.', 'error')
    return render_template('login.html')


@bp.post('/logout')
def logout():
    logout_user()
    flash('You have been signed out.', 'success')
    return redirect(url_for('auth.login'))
