from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint
from settings import Config

applications_bp = Blueprint('applications_bp', __name__, template_folder='templates/users', static_folder='static')

advertisement, data= Config.advertisements, Config.applications


@applications_bp.route('/applications',  methods=["POST", "GET"])
def Applications():
    return render_template('applications.html', title="applications", details=data.show(), advertisement=advertisement.show())
# pass the geo location country in template as a variable and as data is diplayed check if the current country is in the list 
#of the countries of the post in the database