from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from settings import Config
from admin.Forms.forms import Staff_Form
from datetime import datetime 

delete_add_bp = Blueprint('delete_add_bp', __name__, template_folder='templates/admin', static_folder='static')
current_time = datetime.utcnow()

advertisements = Config.advertisements 

@delete_add_bp.route('/delete_add', methods=['POST'])
def delete_add():
    if 'name' and 'email' and 'password' in session:
	    if request.method == 'POST':
	        row_id = request.form.get('row_id')  # Get the row ID from the form data	
	        # Perform the deletion operation in the database using the row ID
	        # Example assuming you have a function called delete_add_from_database(row_id)
	        advertisements.delete_row_from_database(row_id)
	        return redirect(url_for('admin_advertisements_bp.Admin_advertisements'))
	    else:
	    	return redirect(url_for('login_bp.Login'))	        
    else:
    	flash('🚫Access denied!!')
    	return redirect(url_for('login_bp.Login'))

