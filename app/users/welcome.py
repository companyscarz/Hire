from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint
from settings import Config

welcome_bp = Blueprint('welcome_bp', __name__, template_folder='templates/users', static_folder='static')

advertisements, applications, opportunities= Config.advertisements, Config.applications, Config.opportunities

@welcome_bp.route('/welcome')
def Welcome():
    title="welcome"
    flash('Hire brings to you the wordly opportunities!')
    return render_template('welcome.html', title=title)
