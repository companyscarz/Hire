from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from settings import Config

suggestions_bp = Blueprint('suggestions_bp', __name__, template_folder='templates/admin', static_folder='static')

suggestions = Config.suggestions 

@suggestions_bp.route('/suggestions')
def Suggestions():
    title="suggestions"
    if 'name' and 'email' and 'password' in session:
    	return render_template('suggestions.html', title=title, data=suggestions.show())
    else:
    	flash('🚫Access denied!!')
    	return redirect(url_for('login_bp.Login'))
    