from flask import Blueprint, render_template

hire_logo = Blueprint('hire_logo', __name__, template_folder='templates/users', static_folder='static')

@hire_logo.route('/')
def Hire_logo():
    title="welcome"
    return render_template('hire_logo_welcome.html', title=title)
