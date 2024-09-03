from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from settings import Config

delete_staff_bp = Blueprint('delete_staff_bp', __name__, template_folder='templates/admin', static_folder='static')


member = Config.members

@delete_staff_bp.route('/delete_staff', methods=['POST'])
def delete_staff():
    if 'name' and 'email' and 'password' in session:
	    if request.method == 'POST':
	        passcode = request.form.get('passcode')
	        if passcode==Config.CODE_1 or passcode==Config.CODE_2:
	         	row_id = request.form.get('row_id')  # Get the row ID from the form data
		        # Perform the deletion operation in the database using the row ID
		        #  you have a function called delete_add_from_database(row_id)
	         	member.delete_row_from_database(row_id)
		        # Redirect the user to a relevant page after the deletion
	         	return redirect(url_for('staff_bp.Staff'))
	        else:
	        	flash('🚫You are not authorised to perform this action')
	        	return redirect(url_for('login_bp.Login'))
    else:
    	flash('🚫Access denied!!')
    	return redirect(url_for('login_bp.Login'))

    # when delete button is clicked then delete item where id is that one .. same with block.. 
    # a block column should be added in the all databases and default data is not blocked when one is blocked then data edits to block