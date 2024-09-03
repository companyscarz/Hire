from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from settings import Config

staff_bp = Blueprint('staff_bp', __name__, template_folder='templates/admin', static_folder='static')


members = Config.members 

@staff_bp.route('/staff')
def Staff():
    title="staff"
    if 'name' and 'email' and 'password' in session:
    	return render_template('staff.html', title=title, data=members.show())
    else:
    	flash('🚫Access denied!!')
    	return redirect(url_for('login_bp.Login'))
    