from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from settings import Config
from admin.Forms.forms import Staff_Form

delete_opportunity_bp = Blueprint('delete_opportunity_bp', __name__, template_folder='templates/admin', static_folder='static')


opportunities = Config.opportunities

@delete_opportunity_bp.route('/delete_opportunity', methods=['POST'])
def delete_opportunity():
    if 'name' and 'email' and 'password' in session:
	    if request.method == 'POST':
	        row_id = request.form.get('row_id')  # Get the row ID from the form data
	
	        # Perform the deletion operation in the database using the row ID
	        # Example assuming you have a function called delete_add_from_database(row_id)
	        opportunities.delete_row_from_database(row_id)
	        # Redirect the user to a relevant page after the deletion
	        return redirect(url_for('admin_opportunities_bp.Admin_opportunities'))
    else:
    	flash('🚫Access denied!!')
    	return redirect(url_for('login_bp.Login'))

    # when delete button is clicked then delete item where id is that one .. same with block.. 
    # a block column should be added in the all databases and default data is not blocked when one is blocked then data edits to block