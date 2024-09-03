from flask_wtf import FlaskForm, RecaptchaField
from wtforms import Form, StringField, SubmitField, FileField, TextAreaField, IntegerField, SelectField, TelField
from wtforms.validators import Email, DataRequired, URL
from flask_wtf.file import FileField, FileAllowed, FileRequired, FileSize


entry = '🤨 Entry must be filled!'
file_entry = '🤨 field must be filled!'
e_mail = '🐒 Enter a valid Email!'
link = '🐒 Enter a valid link!!'
file_error = '📁This file format cannot be accepted!'
file_size = '🪨Heavy file 📁, it must be less than 10MB'

class AdvertisementForm(FlaskForm):
    email = StringField('Valid Email', validators=[Email(e_mail), DataRequired(entry)])
    telphone = TelField('Telphone', validators=[DataRequired(entry)])
    link = StringField('Any blog or social media link about the company / employer', validators=[URL(link)])
    information = FileField('Information', validators=[FileRequired(file_entry), 
                            FileAllowed(['jpg', 'jpeg', 'png','gif','bmp','tiff','mp4','avi','mov','wmv','flv'], file_error),
                            FileSize(10*1024*1024, message=file_size)])
    #recaptcha = RecaptchaField()
    submit = SubmitField('Submit') 

	#use this in the html before close button 
		#<div>
		  #{{form.recaptcha(class="btn btn-outline-primary")}}
		#</div>

class ApplicantForm(FlaskForm):
    name = StringField('Full name', validators=[DataRequired(entry)])
    email = StringField('Email', validators=[DataRequired(entry), Email(e_mail)])
    telphone = StringField('Telphone', validators=[DataRequired(entry)])
    gender = SelectField("What's your gender?", choices=[('M','Male'),('F','Female')])
    position = StringField('What position do you want in company?', validators=[DataRequired(entry)])
    interest = TextAreaField("What makes you interested in this position?", validators=[DataRequired(entry)])
    education = SelectField('Educational level', choices=[('Elementary Education','Primary Education/Elementary School'), ('High and High School Education','Secondary Education/Junior High and High School'), ('College and Graduate School (Higher Education)','Higher Education/College and Graduate School')], validators=[DataRequired('Entry must be filled!')])
    experience = IntegerField('What is your work experience (years)?')#, validators=[DataRequired(entry)]
    skills = TextAreaField('What are your Skills and abilities', validators=[DataRequired(entry)])
    certificate = FileField('Any relevant certifications', validators=[FileRequired(entry), 
                            FileAllowed(['jpg', 'jpeg', 'png','gif'], file_error),
                            FileSize(10*1024*1024, message=file_size)])#image
    #recaptcha = RecaptchaField()
    submit = SubmitField('Submit')


class CompanyForm(FlaskForm):
    companyname = StringField("Name of the company", validators=[DataRequired(entry)])
    company_logo = FileField("company logo 'optional' ", validators=[FileRequired(entry), FileAllowed(['jpg', 'jpeg', 'png','gif'], file_error),FileSize(10*1024*1024, message=file_size)])
    companyemail = StringField("Email of the company", validators=[DataRequired(entry)])
    companyhotline  = StringField("Hotline of the company", validators=[DataRequired(entry)])
    link = StringField('Any blog or social media link about the company / employer', validators=[URL(link)])
    location = StringField("Location of the company", validators=[DataRequired(entry)])
    seeking = StringField("Looking for ", validators=[DataRequired(entry)])
    description = TextAreaField("Description of the job offerred", validators=[DataRequired(entry)])
    gender = SelectField("Gender needed", choices=[('A','Any'),('M','Male'),('F','Female')])
    education = SelectField('Educational level', choices=[('Elementary Education','Primary Education/Elementary School'), ('High and High School Education','Secondary Education/Junior High and High School'), ('College and Graduate School (Higher Education)','Higher Education/College and Graduate School')], validators=[DataRequired('Entry must be filled!')])
    experience = IntegerField('What is work experience (years)?')#, validators=[DataRequired(entry)]
    skills = TextAreaField("Skills one needs to have")
    applying = TextAreaField("How can one apply?", validators=[DataRequired(entry)])
    benefits = TextAreaField("Benefits one has for working for the company", validators=[DataRequired(entry)])
    details = FileField("Details about the company or license", validators=[FileRequired(entry), 
                            FileAllowed(['jpg', 'jpeg', 'png','gif'], file_error),
                            FileSize(10*1024*1024, message=file_size)])
    #recaptcha = RecaptchaField()
    submit = SubmitField("submit")
    
class AboutForm(FlaskForm):
	suggestion = TextAreaField("Your Feedback", validators=[DataRequired(entry)])
	#recaptcha = RecaptchaField()
	submit = SubmitField("submit")