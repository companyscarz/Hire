from flask import Flask, render_template
from settings import Config

#importing blueprints
from users.hire_logo import hire_logo
from users.welcome import welcome_bp
from users.company import company_bp
from users.applicant import applicant_bp
from users.advertisement import advertisement_bp
from users.applications import applications_bp
from users.opportunities import opportunities_bp
from users.about import about_bp
from users.view_map import view_map_bp
from users.path import path_bp
from users.company_search import company_search_bp
from users.applicant_search import application_search_bp
from users.advert_search import advert_search_bp

from admin.suggestions import suggestions_bp
from admin.login import login_bp
from admin.add_staff import add_staff_bp
from admin.admin_advertisements import admin_advertisements_bp
from admin.admin_applicantions import admin_applicantions_bp
from admin.admin_opportunities import admin_opportunities_bp
from admin.delete_add import delete_add_bp
from admin.delete_application import delete_application_bp
from admin.delete_opportunity import delete_opportunity_bp
from admin.blocked import blocked_bp
from admin.delete_blocked import delete_blocked_bp
from admin.block_add import block_add_bp
from admin.block_company import block_company_bp
from admin.block_applicant import block_applicant_bp
from admin.logout import logout_bp
from admin.staff import staff_bp
from admin.delete_staff import delete_staff_bp
from admin.block_staff import block_staff_bp
from admin.staff_search import staff_search_bp

app = Flask(__name__)
app.config.from_object(Config)

#secret key
app.config["SECRET_KEY"]
#config for recaptcha
app.config["RECAPTCHA_PUBLIC_KEY"]
app.config["RECAPTCHA_PRIVATE_KEY"] 

#registering blueprints
app.register_blueprint(hire_logo)
app.register_blueprint(welcome_bp)
app.register_blueprint(company_bp)
app.register_blueprint(applicant_bp)
app.register_blueprint(advertisement_bp)
app.register_blueprint(applications_bp)
app.register_blueprint(opportunities_bp)
app.register_blueprint(about_bp)
app.register_blueprint(suggestions_bp)
app.register_blueprint(login_bp)
app.register_blueprint(add_staff_bp)
app.register_blueprint(admin_advertisements_bp)
app.register_blueprint(admin_applicantions_bp)
app.register_blueprint(admin_opportunities_bp)
app.register_blueprint(delete_add_bp)
app.register_blueprint(delete_application_bp)
app.register_blueprint(delete_opportunity_bp)
app.register_blueprint(blocked_bp)
app.register_blueprint(delete_blocked_bp)
app.register_blueprint(block_add_bp)
app.register_blueprint(block_company_bp)
app.register_blueprint(block_applicant_bp)
app.register_blueprint(logout_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(delete_staff_bp)
app.register_blueprint(block_staff_bp)
app.register_blueprint(view_map_bp)
app.register_blueprint(path_bp)
app.register_blueprint(company_search_bp)
app.register_blueprint(application_search_bp)
app.register_blueprint(staff_search_bp)
app.register_blueprint(advert_search_bp)
								
@app.errorhandler(400)
def error400(e):
    return render_template('errors/error(400).html', title='400'), 400

@app.errorhandler(401)
def error401(e):
    return render_template('errors/error(401).html', title='401'), 401 

@app.errorhandler(403)
def error403(e):
    return render_template('errors/error(403).html', title='403'), 403       
    
@app.errorhandler(404)
def error404(e):
    return render_template('errors/error(404).html', title='404'), 404

@app.errorhandler(406)
def error406(e):
    return render_template('errors/error(406).html',title='406'), 406    
    
@app.errorhandler(415)
def error415(e):
    return render_template('errors/error(415).html', title='405'), 415

@app.errorhandler(429)
def error429(e):
    return render_template('errors/error(429).html', title='429'), 429

@app.errorhandler(500)
def error500(e):
    return render_template('errors/error(500).html', title='500'), 500

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], port=Config.port, host=Config.host)