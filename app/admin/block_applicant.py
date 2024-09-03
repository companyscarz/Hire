from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from settings import Config
from admin.Forms.forms import Staff_Form
from datetime import datetime 

block_applicant_bp = Blueprint('block_applicant_bp', __name__, template_folder='templates/admin', static_folder='static')
current_time = datetime.utcnow()

applicantion = Config.applications
block = Config.block

@block_applicant_bp.route('/block_applicant_bp', methods=['POST'])
def block_applicant():
    if 'name' and 'email' and 'password' in session:
	    if request.method == 'POST':
	        row_id = request.form.get('row_id')  # Get the row ID from the form data
	        row_email = request.form.get('row_email')
	
	        # Perform the deletion operation in the database using the row ID
	        # Example assuming you have a function called delete_add_from_database(row_id)
	        data = BLock(row_email, current_time)
	        data.add()
	        applicantion.delete_row_from_database(row_id)
	        return redirect(url_for('blocked_bp.Blocked'))
    else:
    	flash('🚫Access denied!!')
    	return redirect(url_for('login_bp.Login'))
