from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint
from settings import Config

#get the search results and pass them here 
# check if email or name is there then display

company_search_bp = Blueprint('company_search_bp', __name__, template_folder='templates', static_folder='static')

advertisement, data= Config.advertisements, Config.opportunities                                                                   

@company_search_bp.route('/company_search',  methods=["POST", "GET"])
def Company_search():
    title="company_search"
    if request.method == "POST":
    	search_company = request.form.get("search_company")
    	details=data.search_for_company(search_company)#populate the function with data from request the search bar 
    	return render_template('company_search.html', title=title, details=details, advertisement=advertisement.show())
# pass the geo location country in template as a variable and as data is diplayed check if the current country is in the list 
#of the countries of the post in the database