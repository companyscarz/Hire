from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint
from settings import Config

opportunities_bp = Blueprint('opportunities_bp', __name__, template_folder='templates', static_folder='static')

advertisement, data= Config.advertisements, Config.opportunities                                                                   

@opportunities_bp.route('/opportunities',  methods=["POST", "GET"])
def Opportunities():
    return render_template('opportunities.html', title="opportunities", details=data.show(), advertisement=advertisement.show())
# pass the geo location country in template as a variable and as data is diplayed check if the current country is in the list 
#of the countries of the post in the database