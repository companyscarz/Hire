from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint, session
from settings import Config
from admin.Forms.forms import Staff_Form

advert_search_bp = Blueprint('advert_search_bp', __name__, template_folder='templates/users', static_folder='static')


advertisements = Config.advertisements 
##will contain details from database of user advertisements
##details for all advertisements
##only specific people in the admin_admin database can have access to this page 
##with the administrators password one can access this page and be able to take action on the 
#data

@advert_search_bp.route('/advert_search', methods=['POST', 'GET'])
def Advert_search():
    title="advert_search"
    if request.method == 'POST':
    	search_advert = request.form.get("search_advert")
    	flash("Results for your search")
    	return render_template('advert_search.html', title=title, data=advertisements.advertisement_search(search_advert))
    else:
    	return redirect(url_for("welcome_bp.Welcome"))
    