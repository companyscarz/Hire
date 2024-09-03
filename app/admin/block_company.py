from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from settings import Config
from datetime import datetime 

block_company_bp = Blueprint('block_company_bp', __name__, template_folder='templates/admin', static_folder='static')
current_time = datetime.utcnow()

company = Config.opportunities
block = Config.block

@block_company_bp.route('/block_company_bp', methods=['POST'])
def block_company():
    if 'name' and 'email' and 'password' in session:
	    if request.method == 'POST':
	        row_id = request.form.get('row_id')  # Get the row ID from the form data
	        row_email = request.form.get('row_email')
	
	        # Perform the deletion operation in the database using the row ID
	        # Example assuming you have a function called delete_add_from_database(row_id)
	        data = BLock(row_email, current_time)
	        data.add()
	        company.delete_row_from_database(row_id)
	        return redirect(url_for('blocked_bp.Blocked'))
    else:
    	flash('🚫Access denied!!')
    	return redirect(url_for('login_bp.Login'))
