from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint
from users.Forms.forms import ApplicantForm
from users.models.models_applicant import APplicant 
from users.models.models_block import BLock
from users.Forms.geo import Geogrpahy
from datetime import datetime
import geocoder
import random
import secrets
import base64

applicant_bp = Blueprint('applicant_bp', __name__, template_folder='templates/users', static_folder='static')
block = BLock('0','1')
g = geocoder.ipinfo('me')#access ip address
#the termination code that will be needed when someone wants to delete their post
termination_code = secrets.token_hex(random.randint(5,9))#generate termination code 

@applicant_bp.route('/applicant',  methods=["POST", "GET"])
def Applicant():#data should be entered on the databse hire.db
    form = ApplicantForm()
    form2 = Geogrpahy()
    current_time = datetime.utcnow()#get current time
       #if form submittied check if Form2 has selected data if it has charge the user according to the geography is no use default loaction which is current region then save on database
    if request.method == 'POST':
        if block.is_email_blocked(form.email.data):
        	flash(f'The email: {form.email.data} is blocked')
        else:
	        if form.validate() and form2.validate():
	            #open the image file and read its content as binary data
	            uploaded_file = form.certificate.data
	            binary_data = uploaded_file.read()
	            file_data = base64.b64encode(binary_data).decode('utf-8')
	
	            #change the list into a CSV format
	            locations = ', '.join(form2.countries.data)
	            skills = ",".join(form.skills.data.data)#change the skills into a CSV formart
	            
	            #save the details and encoded image data on database
	            data = APplicant(form.name.data, form.email.data, form.telphone.data, 
				            form.gender.data, form.position.data, form.interest.data, form.education.data, 
				            form.experience.data, skills, file_data, uploaded_file.filename, 
				            uploaded_file.content_type, locations, current_time, termination_code)
	            	
	            data.add()
	            flash(" Form Submitted Successfully!")
	            return redirect(url_for('welcome_bp.Welcome'))
	            
	        elif form.validate_on_submit() == False:# if form not valide
	            flash("Failed to submit form Please check your details!")
	            
	        elif form2.validate_on_submit() == False: #if form 2 not valide          
	            current_country = g.country
	            if g.status=='OK': #if there is internet connection
	                skills = ",".join(form.skills.data.data)#change the skills into a CSV formart
	                #open the image file and read its content as binary data
	                uploaded_file = form.certificate.data
	                binary_data = uploaded_file.read()
	                file_data = base64.b64encode(binary_data).decode('utf-8')
	                
	                data = APplicant(form.name.data, form.email.data, form.telphone.data, form.gender.data, 
	                			form.position.data, form.interest.data, form.education.data, form.experience.data, 
	                			skills, file_data, uploaded_file.filename, uploaded_file.content_type, 
	                			current_country, current_time,termination_code)
	                			
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
    return render_template('applicant.html', title="applicant", form=form, form2=form2)
