from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from settings import Config
from admin.Forms.forms import Staff_Form

admin_applicantions_bp = Blueprint('admin_applicantions_bp', __name__, template_folder='templates/admin', static_folder='static')

applications = Config.applications

##will contain details from database of user applications
##details for all applications
##only specific people in the admin_admin database can have access to this page 
##with the administrators password one can access this page and be able to take action on the 
#data

@admin_applicantions_bp.route('/admin_applicantions')
def Admin_applicantions():
    title="admin_applicantions"
    if 'name' and 'email' and 'password' in session:
    	return render_template('admin_applicantions.html', title=title, data=applications.show())
    else:
    	flash('🚫Access denied!!')
    	return redirect(url_for('login_bp.Login'))
