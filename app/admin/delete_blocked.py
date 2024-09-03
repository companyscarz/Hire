from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from settings import Config
from admin.Forms.forms import Staff_Form

delete_blocked_bp = Blueprint('delete_blocked_bp', __name__, template_folder='templates/admin', static_folder='static')

block = Config.block

@delete_blocked_bp.route('/delete_blocked', methods=['POST'])
def delete_blocked():
    if 'name' and 'email' and 'password' in session:
	    if request.method == 'POST':
	        row_id = request.form.get('row_id')  # Get the row ID from the form data
	
	        # Perform the deletion operation in the database using the row ID
	        # Example assuming you have a function called delete_add_from_database(row_id)
	        block.delete_row_from_database(row_id)
	        # Redirect the user to a relevant page after the deletion
	        return redirect(url_for('blocked_bp.Blocked'))
    else:
    	flash('🚫Access denied!!')
    	return redirect(url_for('login_bp.Login'))
