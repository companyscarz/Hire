from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from settings import Config
from admin.Forms.forms import Staff_Form

admin_advertisements_bp = Blueprint('admin_advertisements_bp', __name__, template_folder='templates/admin', static_folder='static')


advertisements = Config.advertisements 
##will contain details from database of user advertisements
##details for all advertisements
##only specific people in the admin_admin database can have access to this page 
##with the administrators password one can access this page and be able to take action on the 
#data

@admin_advertisements_bp.route('/admin_advertisements', methods=['POST', 'GET'])
def Admin_advertisements():
    title="manage"
    if 'name' and 'email' and 'password' in session:
    	return render_template('admin_advertisements.html', title=title, data=advertisements.SHOW())
    else:
    	flash('🚫Access denied!!')
    	return redirect(url_for('login_bp.Login'))
    