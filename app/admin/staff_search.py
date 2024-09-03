from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from settings import Config

staff_search_bp = Blueprint('staff_search_bp', __name__, template_folder='templates/admin', static_folder='static')


members = Config.members 

@staff_search_bp.route('/staff_search', methods=['GET','POST'])
def Staff_search():
    title="staff_search"
    if 'name' and 'email' and 'password' in session:
    	if request.method == 'POST':
    		search = request.form.get('staff_search')
    		flash("Results for your search")
    		return render_template('staff_search.html', title=title, data=members.staff_search(search))
    else:
    	flash('🚫Access denied!!')
    	return redirect(url_for('login_bp.Login'))
    