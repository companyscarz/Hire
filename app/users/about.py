from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint
from users.Forms.forms import AboutForm
from users.models.models_about import  ABout
from datetime import datetime
import geocoder
import base64

about_bp = Blueprint('about_bp', __name__, template_folder='templates/users', static_folder='static')

@about_bp.route('/about', methods=['GET', 'POST'])
def About():
    form = AboutForm()
    current_time = datetime.utcnow()#get current time
    if request.method == 'POST':
        if form.validate():
            data = ABout(form.suggestion.data, current_time)
            data.add()
            flash('thank you for your feedback')
            return redirect(url_for('welcome_bp.Welcome'))
        elif form.validate_on_submit() == False:
            flash("Your suggestion was not submitted!")
    return render_template('about.html', title="about", form=form)
