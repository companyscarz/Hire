from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from admin.Forms.forms import LoginForm
from datetime import datetime
from settings import Config

login_bp = Blueprint('login_bp', __name__, template_folder='templates/admin', static_folder='static')
block,user = Config.block, Config.members

#check if login data is in the admin_user database
#if its there then login

@login_bp.route('/login', methods=["POST","GET"])
def Login():
    title="login"
    form = LoginForm()
    current_time = datetime.utcnow()#get current time
    if request.method == 'POST':
        if block.is_email_blocked(form.email.data):
        	flash(f'The email: {form.email.data} is blocked')
        else:
        	if user.is_login_member(form.name.data, form.email.data, form.password.data):
		        if form.validate():
		                session['name']=form.name.data
		                session['email']=form.email.data
		                session['password']=form.password.data
		                flash(f'welcome back {form.name.data}')
		                return redirect(url_for('staff_bp.Staff'))
		        elif form.validate_on_submit() == False:
		            flash("Failed to login! check your details!")
		            return redirect(url_for('login_bp.Login'))
        	else:
        		flash('🚫Access denied!!')
    return render_template('login.html', title=title, form=form)