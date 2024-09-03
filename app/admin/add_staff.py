from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from admin.Forms.forms import Staff_Form 
from admin.models.models_staff import STaff
from datetime import datetime
from settings import Config
import base64
import secrets

add_staff_bp = Blueprint('add_staff_bp', __name__, template_folder='templates/admin', static_folder='static')
block = Config.block

current_time = datetime.utcnow()

#genarate automatic strong password gor a new user
def generate_password(length=6):
	password=secrets.token_hex(length)
	return password


@add_staff_bp.route('/add_staff', methods=["POST","GET"])
def Add_staff():
    title="login"
    if 'name' and 'email' and 'password' in session:
	    form = Staff_Form()
	    current_time = datetime.utcnow()#get current time
	    password = generate_password()
	    if request.method == 'POST':
	        if block.is_email_blocked(form.email.data):
	        	flash(f'The email: {form.email.data} is blocked')
	        else:
		        if form.validate():
		            if form.passcode.data==Config.CODE_1 or form.passcode.data==Config.CODE_2:
			            #open the image file and read its content as binary data
			            uploaded_file = form.photo.data
			            binary_data = uploaded_file.read()
			            file_data = base64.b64encode(binary_data).decode('utf-8')
			        #check if passcode is one of the top administrators in admin_admin_db
			                ##password should be harshed, photo should be decoded 
			            data = STaff(form.name.data, form.email.data, form.telphone.data, file_data, uploaded_file.filename, uploaded_file.content_type, form.gender.data, form.password.data, current_time)
			            data.add()
			            flash(f'{form.name.data} has been added successfully.')
			            return redirect(url_for('staff_bp.Staff'))
		            else:
			            flash('You are not authorised to perfom this action!!') 
			            return redirect(url_for('login_bp.Login'))
		        elif form.validate_on_submit() == False:
		            flash("Failed to add user check details!")
		            return redirect(url_for('add_staff_bp.Add_staff'))
	    return render_template('add_staff.html', title=title, form=form, password=password)
    else:
    	flash('🚫Access denied!!')
    	return redirect(url_for('login_bp.Login'))

