from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from settings import Config
from admin.Forms.forms import Staff_Form

admin_opportunities_bp = Blueprint('admin_opportunities_bp', __name__, template_folder='templates/admin', static_folder='static')

opportunities =Config.opportunities

##will contain details from database of user opportunities
##details for all opportunities
##only specific people in the admin_admin datase can have access to this page 
##with the administrators password one can access this page and be able to take action on the 
#data

@admin_opportunities_bp.route('/admin_opportunities')
def Admin_opportunities():
    title="admin_opportunities"
    if 'name' and 'email' and 'password' in session:
    	return render_template('admin_opportunities.html', title=title, data=opportunities.show())
    else:
        flash('🚫Access denied!!')
        return redirect(url_for('login_bp.Login'))
