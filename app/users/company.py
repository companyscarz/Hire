from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint
from users.Forms.forms import  CompanyForm
from users.models.models_company import COmpany 
from settings import Config
from users.Forms.geo import Geogrpahy
from datetime import datetime
import geocoder
import random
import secrets
import base64

company_bp = Blueprint('company_bp', __name__, template_folder='templates/users', static_folder='static')
block = Config.block
g = geocoder.ipinfo('me')#access ip address
#the termination code that will be needed when someone wants to delete their post
termination_code = secrets.token_hex(random.randint(5,9))#generate termination code 

@company_bp.route("/company", methods=["POST", "GET"])
def Company():
    form = CompanyForm()
    form2 = Geogrpahy()
    current_time = datetime.utcnow()#get current time
    #if form submittied check if Form2 has selected data if it has, price the user according to the geography is no use default loaction which is current region then save on database
    #when someone is using the app and his location matches that of the post in the database then it is displayed 
    if request.method == 'POST':
        if block.is_email_blocked(form.companyemail.data):
        	flash(f'The email: {form.companyemail.data} is blocked')
        else:
	        if form.validate() and form2.validate():
	            lat=0.0
	            long=0.0
	            
	            #open the logo and read its content as binary data for company logo
	            company_logo = form.company_logo.data
	            binary_data = company_logo.read()
	            company_logo_data = base64.b64encode(binary_data).decode('utf-8')
	            
	            #open the image file and read its content as binary data for company legal document
	            uploaded_file = form.details.data
	            binary_data = uploaded_file.read()
	            file_data = base64.b64encode(binary_data).decode('utf-8')
	            
	            #change the list into a CSV format
	            locations = ', '.join(form2.countries.data)
	            skills = ",".join(form.skills.data.data)#change skills into a CSV formart 
	            
	            #save the details and encoded image data on database
	            data = COmpany(
								form.companyname.data, company_logo_data, company_logo.filename, company_logo.content_type ,
								form.companyemail.data, form.companyhotline.data, 
							   form.link.data, form.location.data, form.seeking.data, form.description.data, 
							   form.gender.data, form.education.data, form.experience.data, skills,
							   form.applying.data, form.benefits.data, file_data, uploaded_file.filename,
							   uploaded_file.content_type, locations, current_time, g.lat, g.lng, termination_code
							  )
	            data.add()
	            flash(" Form Submitted Successfully!")
	            return redirect(url_for('welcome_bp.Welcome'))
	            
	        elif form.validate_on_submit() == False:
	            flash("Failed to submit form Please check your details! or connection")
	            
	        elif form2.validate_on_submit() == False:
	            current_country = g.country
	            if g.status=='OK':
	                
	                skills = ",".join(form.skills.data.data)#change the skills into a list formart
	                #open the image file and read its content as binary data
	                uploaded_file = form.details.data
	                binary_data = uploaded_file.read()
	                file_data = base64.b64encode(binary_data).decode('utf-8') 
	                data = COmpany(
									form.companyname.data, form.companyemail.data, form.companyhotline.data, 
								   form.link.data, form.location.data, form.seeking.data, form.description.data, 
								   form.gender.data, form.education.data, form.experience.data, skills, 
								   form.applying.data, form.benefits.data, file_data, uploaded_file.filename,
								   uploaded_file.content_type, current_country,  current_time, g.lat, g.lng,termination_code
								  )
	                data.add()
	                flash(" Form Submitted Successfully!")
	                return redirect(url_for('welcome_bp.Welcome'))
	            else:#if no internet connection
	                flash("Failed to get your country! Please check your connection!")
	                
	        else:
	        	flash("Failed to submit form Please check your details or connection")
	            #if no location is selected then then use geocoder via my_adress function in connect module to get current loction then save on database
	            #if the my_adress func is not ok ie no internet access then flash check your internet connection.
				#get current country and save it
    return render_template('company.html', title="company", form=form, form2=form2, current_country = g.country)
