from flask import Flask, redirect, url_for, flash, render_template, request, Blueprint
from users.Forms.forms import AdvertisementForm
from users.models.models_advertisement  import ADvertisement 
from users.models.models_block import BLock
from users.Forms.geo import Geogrpahy
from datetime import datetime
import geocoder
import random
import secrets
import base64

advertisement_bp = Blueprint('advertisement_bp', __name__, template_folder='templates/users', static_folder='static')
block = BLock('0','1')
g = geocoder.ipinfo('me')#access ip address
termination_code = secrets.token_hex(random.randint(5,9))#generate termination code 

@advertisement_bp.route('/advertisement',  methods=["POST", "GET"])
def Advertisement():
    form = AdvertisementForm()#data should saved on the database hire.db
    form2 = Geogrpahy()
    current_time = datetime.utcnow()#get current time
    if request.method == 'POST':
        if block.is_email_blocked(form.email.data):
        	flash(f'The email: {form.email.data} is blocked')
        	return redirect(url_for('advertisement_bp.Advertisement'))
        else:
	        if form.validate() and form2.validate():
	            #open the image file and read its content as binary data
	            uploaded_file = form.information.data
	            binary_data = uploaded_file.read()
	            file_data = base64.b64encode(binary_data).decode('utf-8')
	   
	            #change the list into a CSV format
	            locations = ', '.join(form2.countries.data)
	            
	            #save the details and binary image data on database
	            data = ADvertisement(form.email.data, form.telphone.data, form.link.data, file_data, 
	            uploaded_file.filename, uploaded_file.content_type, locations, current_time, termination_code)
	            data.add()
	            #flash if all goes well
	            flash(" Form Submitted Successfully!")
	            return redirect(url_for('welcome_bp.Welcome'))
	            
	        
	        elif form2.validate_on_submit() == False:
	            current_country = g.country
	            if g.status == "OK":
	                #open the image file and read its content as binary data
	                uploaded_file = form.information.data
	                binary_data = uploaded_file.read()
	                file_data = base64.b64encode(binary_data).decode('utf-8')    
	                
	            
	                #add to database
	                data = ADvertisement(form.email.data, form.telphone.data, form.link.data, file_data, 
	                			uploaded_file.filename, uploaded_file.content_type, current_country, current_time, termination_code)
	                
	                data.add()
	                flash(" Form Submitted Successfully!")
	                return redirect(url_for('welcome_bp.Welcome'))
	            else:
	                flash("Failed to get your coordinates! Please check your internet connection!")    
	                return redirect(url_for('advertisement_bp.Advertisement'))
	            #if no location is selected then then use geocoder via get_country function in connect module to get current loction then save on database
	            #if the get_country func is not ok ie no internet access then flash check your internet connection.
				#get current country and save it
				
	        elif form.validate_on_submit() == False:
	            #if there is an error alert with a flash messge 
	            flash("Failed to submit form Please check your details! or connection")
	            return redirect(url_for('advertisement_bp.Advertisement'))
	            
	        else:
	            flash("Failed to submit form Please check your details or connection")
    return render_template('advertisement.html',  title="advertisement", form=form, form2=form2)
       #if form submittied check if Form2 has selected data if it has charge the user according to the geography is no use default loaction which is current region then save on database
       #when someone is using the app and his location matches that of the post in the database then it is displayed 