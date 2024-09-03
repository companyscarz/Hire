from flask import Flask, redirect, url_for, flash, request, Blueprint, session
from admin.Forms.forms import LoginForm
from settings import Config
from datetime import datetime

logout_bp = Blueprint('logout_bp', __name__, template_folder='templates/admin', static_folder='static')
block = Config.block

#check if logout data is in the admin_user database
#if its there then logout

@logout_bp.route('/logout', methods=["POST","GET"])
def logout():
	current_time = datetime.utcnow()#get current time
	session.clear()
	flash("logged out successfully")
	return redirect(url_for('welcome_bp.Welcome'))
 