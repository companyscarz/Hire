from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint
from settings import Config

application_search_bp = Blueprint('application_search_bp', __name__, template_folder='templates/users', static_folder='static')

advertisement, data= Config.advertisements, Config.applications


@application_search_bp.route('/application_search',  methods=["POST", "GET"])
def Application_search():
    title="applicant_search"
    if request.method == "POST":
    	search_applicant = request.form.get("search_applicant")
    	details = data.search_for_applicant(search_applicant)#pass the data from form inside the function
    	flash("Results for your search")
    	return render_template('applicant_search.html', title=title, details=details, advertisement=advertisement.show())
    else:
    	return redirect(url_for("welcome_bp.Welcome"))
# pass the geo location country in template as a variable and as data is diplayed check if the current country is in the list 
#of the countries of the post in the database