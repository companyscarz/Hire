from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Flask-Login is intentionally a direct dependency declared below.
db = SQLAlchemy()
login_manager = LoginManager()
