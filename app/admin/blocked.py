from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from settings import Config
from admin.Forms.forms import Staff_Form

blocked_bp = Blueprint('blocked_bp', __name__, template_folder='templates/admin', static_folder='static')

blocked = Config.block 

@blocked_bp.route('/blocked')
def Blocked():
    if 'name' and 'email' and 'password' in session:
    	title="blocked"
    	return render_template('blocked.html', title=title, data=blocked.show())
    else:
    	flash('🚫Access denied!!')
    	return redirect(url_for('login_bp.Login'))
    