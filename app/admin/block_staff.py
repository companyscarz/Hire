from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from datetime import datetime 
from users.models.models_block import BLock
from settings import Config

block_staff_bp = Blueprint('block_staff_bp', __name__, template_folder='templates/admin', static_folder='static')
current_time = datetime.utcnow()

members = Config.members 
block = Config.block

@block_staff_bp.route('/block_staff_bp', methods=['POST'])
def block_staff():
    if 'name' and 'email' and 'password' in session:
        if request.method == 'POST':
            passcode = request.form.get('passcode')
            if passcode==Config.CODE_1 or passcode==Config.CODE_2:
                row_email = request.form.get('row_email') #get email
                row_id = request.form.get('row_id')  # Get the row ID from the form data
                # Perform the deletion operation in the database using the row ID
                # Example assuming you have a function called delete_add_from_database(row_id)
                data = BLock(row_email, current_time)
                data.add()
                members.delete_row_from_database(row_id)
                return redirect(url_for('blocked_bp.Blocked'))
            else:
                flash('🚫You are not authorised to perform this action')
                return redirect(url_for('blocked_bp.Blocked'))
    else:
        flash('🚫Access denied!!')
        return redirect(url_for('login_bp.Login'))